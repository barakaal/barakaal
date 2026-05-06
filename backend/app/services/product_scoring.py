from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class ProductScoreInput:
    # Données de tendances
    demand_score: float = 50.0          # Score demande 0-100
    growth_rate_pct: float = 0.0        # % croissance

    # Données pricing
    supplier_price_usd: float = 0.0     # Prix fournisseur
    shipping_cost_usd: float = 0.0      # Frais livraison
    market_avg_price_usd: float = 0.0   # Prix moyen marché

    # Logistique
    shipping_days_max: int = 30          # Délai livraison max

    # Concurrence
    competition_level: str = "MEDIUM"   # LOW/MEDIUM/HIGH
    competitor_count: int = 10

    # Risques
    return_rate_pct: float = 5.0        # Taux retour estimé %
    legal_risk: str = "LOW"             # LOW/MEDIUM/HIGH
    quality_risk: str = "LOW"

    # Saisonnalité
    is_seasonal: bool = False
    seasonality_score: float = 50.0     # 0=très saisonnier, 100=evergreen

    # Marketing
    ad_potential: str = "MEDIUM"        # LOW/MEDIUM/HIGH


@dataclass
class ProductScoreResult:
    # Sous-scores (0-100 chacun)
    popularite: float
    croissance_demande: float
    prix_fournisseur_score: float
    marge_brute_score: float
    frais_livraison_score: float
    delai_livraison_score: float
    concurrence_score: float
    retour_probable_score: float
    risque_legal_score: float
    risque_qualite_score: float
    saisonnalite_score: float
    potentiel_pub_score: float

    # Score final pondéré 0-100
    score_final: float

    # Méta
    recommended_selling_price_usd: float
    gross_margin_pct: float
    verdict: str
    recommendation: str


class ProductScoringService:

    WEIGHTS = {
        "popularite": 0.15,
        "croissance_demande": 0.12,
        "prix_fournisseur_score": 0.08,
        "marge_brute_score": 0.18,
        "frais_livraison_score": 0.06,
        "delai_livraison_score": 0.07,
        "concurrence_score": 0.10,
        "retour_probable_score": 0.07,
        "risque_legal_score": 0.06,
        "risque_qualite_score": 0.05,
        "saisonnalite_score": 0.04,
        "potentiel_pub_score": 0.02,
    }

    def calculate(self, inp: ProductScoreInput) -> ProductScoreResult:
        # 1. Popularité (demande actuelle)
        popularite = min(100, max(0, inp.demand_score))

        # 2. Croissance demande
        if inp.growth_rate_pct >= 100:
            croissance = 100
        elif inp.growth_rate_pct >= 50:
            croissance = 85
        elif inp.growth_rate_pct >= 20:
            croissance = 70
        elif inp.growth_rate_pct >= 0:
            croissance = 50
        elif inp.growth_rate_pct >= -10:
            croissance = 30
        else:
            croissance = 10

        # 3. Score prix fournisseur (favorise les prix bas < $30)
        if inp.supplier_price_usd <= 0:
            prix_fourn = 50
        elif inp.supplier_price_usd <= 10:
            prix_fourn = 95
        elif inp.supplier_price_usd <= 20:
            prix_fourn = 85
        elif inp.supplier_price_usd <= 30:
            prix_fourn = 75
        elif inp.supplier_price_usd <= 50:
            prix_fourn = 60
        elif inp.supplier_price_usd <= 100:
            prix_fourn = 40
        else:
            prix_fourn = 20

        # 4. Marge brute
        total_cost = inp.supplier_price_usd + inp.shipping_cost_usd
        recommended_price: float
        gross_margin: float

        if inp.market_avg_price_usd > 0 and total_cost > 0:
            # Prix de vente recommandé = 2.5x à 3x le coût total
            recommended_price = total_cost * 2.8
            # Mais ne pas dépasser le prix marché de plus de 10%
            recommended_price = min(recommended_price, inp.market_avg_price_usd * 1.1)
            gross_margin = ((recommended_price - total_cost) / recommended_price) * 100
        else:
            recommended_price = total_cost * 2.5 if total_cost > 0 else 0.0
            gross_margin = 60.0 if total_cost > 0 else 0.0

        if gross_margin >= 60:
            marge_score = 100
        elif gross_margin >= 50:
            marge_score = 85
        elif gross_margin >= 40:
            marge_score = 70
        elif gross_margin >= 30:
            marge_score = 55
        elif gross_margin >= 20:
            marge_score = 35
        else:
            marge_score = 10

        # 5. Frais livraison
        if inp.shipping_cost_usd == 0:
            livraison_score = 100
        elif inp.shipping_cost_usd <= 3:
            livraison_score = 85
        elif inp.shipping_cost_usd <= 8:
            livraison_score = 65
        elif inp.shipping_cost_usd <= 15:
            livraison_score = 45
        else:
            livraison_score = 20

        # 6. Délai livraison
        if inp.shipping_days_max <= 7:
            delai_score = 100
        elif inp.shipping_days_max <= 14:
            delai_score = 75
        elif inp.shipping_days_max <= 21:
            delai_score = 55
        elif inp.shipping_days_max <= 30:
            delai_score = 35
        else:
            delai_score = 15

        # 7. Concurrence (moins = mieux)
        competition_map = {"LOW": 90, "MEDIUM": 55, "HIGH": 20}
        concurrence_score = competition_map.get(inp.competition_level, 55)

        # 8. Taux retour (moins = mieux)
        if inp.return_rate_pct <= 2:
            retour_score = 100
        elif inp.return_rate_pct <= 5:
            retour_score = 80
        elif inp.return_rate_pct <= 10:
            retour_score = 55
        elif inp.return_rate_pct <= 20:
            retour_score = 30
        else:
            retour_score = 10

        # 9. Risque légal (moins = mieux)
        risk_map = {"LOW": 95, "MEDIUM": 55, "HIGH": 10, "CRITICAL": 0}
        risque_legal = risk_map.get(inp.legal_risk, 55)

        # 10. Risque qualité
        risque_qualite = risk_map.get(inp.quality_risk, 55)

        # 11. Saisonnalité
        saisonnalite = inp.seasonality_score

        # 12. Potentiel pub
        pub_map = {"LOW": 30, "MEDIUM": 65, "HIGH": 95}
        pub_score = pub_map.get(inp.ad_potential, 65)

        # Score final pondéré
        scores = {
            "popularite": popularite,
            "croissance_demande": croissance,
            "prix_fournisseur_score": prix_fourn,
            "marge_brute_score": marge_score,
            "frais_livraison_score": livraison_score,
            "delai_livraison_score": delai_score,
            "concurrence_score": concurrence_score,
            "retour_probable_score": retour_score,
            "risque_legal_score": risque_legal,
            "risque_qualite_score": risque_qualite,
            "saisonnalite_score": saisonnalite,
            "potentiel_pub_score": pub_score,
        }

        score_final = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
        score_final = round(min(100, max(0, score_final)), 1)

        # Verdict
        if score_final >= 80:
            verdict = "EXCELLENT"
            recommendation = "Produit gagnant. Recommandé pour mise en vente immédiate."
        elif score_final >= 65:
            verdict = "BON"
            recommendation = "Bon potentiel. Validation fournisseur recommandée avant lancement."
        elif score_final >= 50:
            verdict = "MOYEN"
            recommendation = "Potentiel modéré. Analyser les axes d'amélioration avant décision."
        elif score_final >= 35:
            verdict = "FAIBLE"
            recommendation = "Risques importants. Non recommandé sans améliorations significatives."
        else:
            verdict = "REJETÉ"
            recommendation = "Produit non rentable ou trop risqué. Rejeter."

        return ProductScoreResult(
            **scores,
            score_final=score_final,
            recommended_selling_price_usd=round(recommended_price, 2),
            gross_margin_pct=round(gross_margin, 1),
            verdict=verdict,
            recommendation=recommendation,
        )

    def calculate_from_dict(self, data: dict) -> ProductScoreResult:
        """Calcule le score depuis un dictionnaire brut (pratique pour les tests)."""
        inp = ProductScoreInput(
            demand_score=float(data.get("demand_score", 50.0)),
            growth_rate_pct=float(data.get("growth_rate_pct", 0.0)),
            supplier_price_usd=float(data.get("supplier_price_usd", 0.0)),
            shipping_cost_usd=float(data.get("shipping_cost_usd", 0.0)),
            market_avg_price_usd=float(data.get("market_avg_price_usd", 0.0)),
            shipping_days_max=int(data.get("shipping_days_max", 30)),
            competition_level=str(data.get("competition_level", "MEDIUM")).upper(),
            competitor_count=int(data.get("competitor_count", 10)),
            return_rate_pct=float(data.get("return_rate_pct", 5.0)),
            legal_risk=str(data.get("legal_risk", "LOW")).upper(),
            quality_risk=str(data.get("quality_risk", "LOW")).upper(),
            is_seasonal=bool(data.get("is_seasonal", False)),
            seasonality_score=float(data.get("seasonality_score", 50.0)),
            ad_potential=str(data.get("ad_potential", "MEDIUM")).upper(),
        )
        return self.calculate(inp)

    def score_to_dict(self, result: ProductScoreResult) -> dict:
        """Sérialise un ProductScoreResult en dict pour stockage JSON."""
        return {
            "score_final": result.score_final,
            "verdict": result.verdict,
            "recommendation": result.recommendation,
            "recommended_selling_price_usd": result.recommended_selling_price_usd,
            "gross_margin_pct": result.gross_margin_pct,
            "sub_scores": {
                "popularite": result.popularite,
                "croissance_demande": result.croissance_demande,
                "prix_fournisseur_score": result.prix_fournisseur_score,
                "marge_brute_score": result.marge_brute_score,
                "frais_livraison_score": result.frais_livraison_score,
                "delai_livraison_score": result.delai_livraison_score,
                "concurrence_score": result.concurrence_score,
                "retour_probable_score": result.retour_probable_score,
                "risque_legal_score": result.risque_legal_score,
                "risque_qualite_score": result.risque_qualite_score,
                "saisonnalite_score": result.saisonnalite_score,
                "potentiel_pub_score": result.potentiel_pub_score,
            },
        }


# Singleton instance
scoring_service = ProductScoringService()
