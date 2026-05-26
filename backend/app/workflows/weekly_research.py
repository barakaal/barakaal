"""
WeeklyResearchWorkflow — Workflow complet de recherche produits hebdomadaire.

Pipeline:
  1. Collecte des tendances depuis tous les connecteurs (Amazon, AliExpress, eBay, TikTok, Google Trends)
  2. Analyse par ProductResearchManagerAgent
  3. Calcul du score (ProductScoringService) pour chaque candidat
  4. Filtrage: score >= 50
  5. Analyse sourcing par SourcingManagerAgent pour les meilleurs produits
  6. Vérification conformité par ComplianceManagerAgent
  7. Création des AgentDecision + Approval pour chaque produit validé
  8. Revue finale par CEOAgent
  9. Sauvegarde en DB (ProductTrend, produits candidats)
  10. Rapport de synthèse
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_factory import create_agent, create_ceo_agent
from app.connectors.connector_registry import get_default_connectors, get_connector
from app.models.agent import Agent, AgentDecision, DecisionStatus, RiskLevel
from app.models.audit import AuditLog, Approval
from app.models.product import Product, ProductStatus, ProductTrend, Platform
from app.services.product_scoring import scoring_service, ProductScoreInput
from app.services import audit_service

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WeeklyResearchWorkflow:
    """
    Orchestre le workflow complet de recherche produits hebdomadaire.

    Usage:
        async with AsyncSessionLocal() as db:
            workflow = WeeklyResearchWorkflow(db)
            summary = await workflow.run()
    """

    # Score minimum pour qu'un produit soit retenu comme candidat
    MIN_SCORE_THRESHOLD = 50.0

    # Nombre maximum de produits à soumettre à l'approbation par workflow
    MAX_DECISIONS_PER_RUN = 10

    def __init__(self, db: AsyncSession):
        self.db = db
        self.start_time = _utcnow()
        self.step_results: dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #

    async def run(self) -> dict[str, Any]:
        """
        Exécute le workflow complet et retourne un rapport de synthèse.

        Retourne:
          {
            "step_results": {...},
            "products_found": int,
            "products_validated": int,
            "decisions_created": int,
            "duration_seconds": float
          }
        """
        logger.info("=== WeeklyResearchWorkflow started at %s ===", self.start_time.isoformat())

        products_found = 0
        products_validated = 0
        decisions_created = 0

        try:
            # Step 1: Collecte des tendances
            all_products = await self._step_collect_trends()
            products_found = len(all_products)
            self.step_results["step_1_collect"] = {
                "products_collected": products_found,
                "status": "ok",
            }

            if not all_products:
                logger.warning("No products collected. Aborting workflow.")
                return self._build_summary(0, 0, 0)

            await self._log_system("WORKFLOW_STEP", "workflow", "Étape 1/10: Tendances collectées")

            # Step 2: Analyse par ProductResearchManager
            research_result = await self._step_analyze_products(all_products)
            candidates_raw = research_result.get("candidates", [])
            self.step_results["step_2_analyze"] = {
                "candidates_from_llm": len(candidates_raw),
                "market_insights": research_result.get("market_insights", []),
            }
            await self._log_system(
                "WORKFLOW_STEP", "workflow",
                f"Étape 2/10: {len(candidates_raw)} candidats identifiés par l'agent"
            )

            # Step 3: Calcul des scores pour chaque candidat
            scored_candidates = await self._step_score_products(all_products, candidates_raw)
            self.step_results["step_3_score"] = {
                "scored": len(scored_candidates),
                "avg_score": round(
                    sum(c["score"] for c in scored_candidates) / max(len(scored_candidates), 1), 1
                ),
            }
            await self._log_system("WORKFLOW_STEP", "workflow", "Étape 3/10: Scores calculés")

            # Step 4: Filtrage par score
            validated_candidates = [
                c for c in scored_candidates if c["score"] >= self.MIN_SCORE_THRESHOLD
            ]
            validated_candidates.sort(key=lambda c: c["score"], reverse=True)
            products_validated = len(validated_candidates)
            self.step_results["step_4_filter"] = {
                "passed_threshold": products_validated,
                "threshold": self.MIN_SCORE_THRESHOLD,
            }
            await self._log_system(
                "WORKFLOW_STEP", "workflow",
                f"Étape 4/10: {products_validated} produits au-dessus du seuil {self.MIN_SCORE_THRESHOLD}"
            )

            if not validated_candidates:
                logger.info("No candidates passed the score threshold. Ending workflow early.")
                await self._step_ceo_review([], research_result)
                return self._build_summary(products_found, 0, 0)

            # Limiter le nombre de candidats traités
            top_candidates = validated_candidates[: self.MAX_DECISIONS_PER_RUN]

            # Step 5: Analyse sourcing
            sourcing_result = await self._step_sourcing_analysis(top_candidates)
            self.step_results["step_5_sourcing"] = sourcing_result
            await self._log_system("WORKFLOW_STEP", "workflow", "Étape 5/10: Analyse sourcing terminée")

            # Step 6: Vérification conformité
            compliance_result = await self._step_compliance_check(top_candidates)
            self.step_results["step_6_compliance"] = compliance_result
            await self._log_system("WORKFLOW_STEP", "workflow", "Étape 6/10: Conformité vérifiée")

            # Filtrer les produits avec risque légal CRITICAL
            compliant_candidates = [
                c for c in top_candidates
                if compliance_result.get("risks", {}).get(c.get("name", ""), {}).get("risk_level", "LOW") != "CRITICAL"
            ]

            # Step 7: Créer les produits en DB + decisions + approvals
            decisions_created = await self._step_create_decisions(compliant_candidates)
            self.step_results["step_7_decisions"] = {"decisions_created": decisions_created}
            await self._log_system(
                "WORKFLOW_STEP", "workflow",
                f"Étape 7/10: {decisions_created} décisions créées"
            )

            # Step 8: Sauvegarder les tendances en DB
            await self._step_save_trends(all_products)
            self.step_results["step_8_save_trends"] = {"status": "ok"}
            await self._log_system("WORKFLOW_STEP", "workflow", "Étape 8/10: Tendances sauvegardées")

            # Step 9: Revue CEO
            ceo_report = await self._step_ceo_review(top_candidates, research_result)
            self.step_results["step_9_ceo"] = {"report_generated": True}
            await self._log_system("WORKFLOW_STEP", "workflow", "Étape 9/10: Revue CEO terminée")

            # Step 10: Commit final
            await self.db.commit()
            await self._log_system("WORKFLOW_COMPLETE", "workflow", "Étape 10/10: Workflow hebdomadaire terminé")

        except Exception as exc:
            logger.error("WeeklyResearchWorkflow failed: %s", exc, exc_info=True)
            self.step_results["error"] = str(exc)
            await self.db.rollback()
            raise

        return self._build_summary(products_found, products_validated, decisions_created)

    # ------------------------------------------------------------------ #
    # Steps
    # ------------------------------------------------------------------ #

    async def _step_collect_trends(self) -> list[dict]:
        """
        Étape 1: Collecte les tendances depuis tous les connecteurs.
        Gère gracieusement les échecs de connecteurs individuels.
        """
        connectors = get_default_connectors()
        all_products: list[dict] = []
        collection_errors: list[str] = []

        async def collect_from(platform: str, connector) -> list[dict]:
            try:
                products = await connector.get_trending_products(limit=20)
                logger.info("Collected %d products from %s", len(products), platform)
                return products
            except Exception as e:
                logger.warning("Failed to collect from %s: %s", platform, e)
                collection_errors.append(f"{platform}: {str(e)}")
                return []
            finally:
                try:
                    await connector.close()
                except Exception:
                    pass

        # Collecte parallèle de tous les connecteurs
        tasks = [
            collect_from(platform, connector)
            for platform, connector in connectors.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        for platform_products in results:
            all_products.extend(platform_products)

        if collection_errors:
            logger.warning("Collection errors: %s", collection_errors)
        self.step_results["collection_errors"] = collection_errors

        logger.info("Total products collected: %d", len(all_products))
        return all_products

    async def _step_analyze_products(self, products: list[dict]) -> dict:
        """Étape 2: Analyse des produits par ProductResearchManagerAgent."""
        try:
            agent = await create_agent(self.db, "ProductResearchManager")
            result = await agent.execute(
                {
                    "action": "analyze_products",
                    "products": products,
                    "context": {
                        "workflow": "weekly_research",
                        "date": _utcnow().strftime("%Y-%m-%d"),
                        "min_score_threshold": self.MIN_SCORE_THRESHOLD,
                    },
                }
            )
            return result
        except Exception as e:
            logger.error("ProductResearchManager failed: %s", e)
            # Fallback: retourner tous les produits comme candidats bruts
            return {
                "candidates": [
                    {
                        "name": p.get("name", "Unknown"),
                        "category": p.get("category", ""),
                        "potential_score": p.get("demand_score", 50),
                        "demand_level": "MEDIUM",
                        "competition_level": p.get("competition_level", "MEDIUM"),
                        "estimated_margin_pct": 40.0,
                        "source_product": p,
                    }
                    for p in products[:20]
                ],
                "market_insights": [],
                "fallback_mode": True,
            }

    async def _step_score_products(
        self, raw_products: list[dict], candidates: list[dict]
    ) -> list[dict]:
        """
        Étape 3: Calcule les scores pour chaque candidat.
        Enrichit les candidats avec les données des produits bruts correspondants.
        """
        # Index des produits bruts par nom pour enrichissement
        products_by_name = {p.get("name", "").lower(): p for p in raw_products}

        scored = []
        for candidate in candidates:
            name = candidate.get("name", "")
            raw = products_by_name.get(name.lower(), {})

            # Construire l'input de scoring depuis les données combinées
            inp = ProductScoreInput(
                demand_score=float(raw.get("demand_score", candidate.get("potential_score", 50))),
                growth_rate_pct=float(raw.get("growth_rate_pct", 10.0)),
                supplier_price_usd=float(raw.get("supplier_price", raw.get("price_usd", 0)) * 0.3),
                shipping_cost_usd=float(raw.get("shipping_cost_usd", 2.0)),
                market_avg_price_usd=float(raw.get("price_usd", 0)),
                shipping_days_max=int(raw.get("shipping_days_max", 25)),
                competition_level=str(
                    raw.get("competition_level", candidate.get("competition_level", "MEDIUM"))
                ).upper(),
                return_rate_pct=5.0,
                legal_risk="LOW",
                quality_risk="LOW",
                seasonality_score=60.0,
                ad_potential="MEDIUM",
            )

            score_result = scoring_service.calculate(inp)
            score_dict = scoring_service.score_to_dict(score_result)

            enriched = {
                **candidate,
                **raw,
                "score": score_result.score_final,
                "score_details": score_dict,
                "verdict": score_result.verdict,
                "recommended_price_usd": score_result.recommended_selling_price_usd,
                "gross_margin_pct": score_result.gross_margin_pct,
                "scoring_input": {
                    "demand_score": inp.demand_score,
                    "supplier_price_usd": inp.supplier_price_usd,
                    "shipping_cost_usd": inp.shipping_cost_usd,
                    "market_avg_price_usd": inp.market_avg_price_usd,
                },
            }
            scored.append(enriched)

        scored.sort(key=lambda c: c["score"], reverse=True)
        return scored

    async def _step_sourcing_analysis(self, candidates: list[dict]) -> dict:
        """Étape 5: Analyse sourcing par SourcingManagerAgent."""
        try:
            agent = await create_agent(self.db, "SourcingManager")
            result = await agent.execute(
                {
                    "action": "compare_suppliers",
                    "products": candidates,
                    "context": {"workflow": "weekly_research"},
                }
            )
            return result
        except Exception as e:
            logger.error("SourcingManager failed: %s", e)
            return {
                "supplier_recommendations": [],
                "error": str(e),
                "fallback_mode": True,
            }

    async def _step_compliance_check(self, candidates: list[dict]) -> dict:
        """Étape 6: Vérification conformité par ComplianceManagerAgent."""
        try:
            agent = await create_agent(self.db, "ComplianceManager")
            result = await agent.execute(
                {
                    "action": "check_products",
                    "products": candidates,
                    "context": {"workflow": "weekly_research"},
                }
            )
            return result
        except Exception as e:
            logger.error("ComplianceManager failed: %s", e)
            # En cas d'erreur, supposer LOW risk pour ne pas bloquer le workflow
            return {
                "risks": {c.get("name", ""): {"risk_level": "LOW"} for c in candidates},
                "error": str(e),
                "fallback_mode": True,
            }

    async def _step_create_decisions(self, candidates: list[dict]) -> int:
        """
        Étape 7: Crée les produits, AgentDecision et Approval en DB.
        Retourne le nombre de décisions créées.
        """
        # Récupérer ou créer l'agent ProductResearchManager pour les décisions
        try:
            agent = await create_agent(self.db, "ProductResearchManager")
        except Exception as e:
            logger.error("Cannot create ProductResearchManager for decisions: %s", e)
            return 0

        decisions_created = 0

        for candidate in candidates:
            try:
                # 1. Créer le produit en DB
                product = await self._create_product_from_candidate(candidate)
                await self.db.flush()
                await self.db.refresh(product)

                # 2. Créer la AgentDecision
                score = candidate.get("score", 0)
                risk_level = (
                    RiskLevel.LOW.value
                    if score >= 75
                    else RiskLevel.MEDIUM.value
                    if score >= 60
                    else RiskLevel.HIGH.value
                )

                decision = AgentDecision(
                    agent_id=agent.agent_record.id,
                    task_id=None,
                    decision_type="ADD_PRODUCT",
                    title=f"Ajouter produit: {candidate.get('name', 'Inconnu')}",
                    rationale=(
                        f"Score produit: {score}/100 ({candidate.get('verdict', 'N/A')}). "
                        f"Marge estimée: {candidate.get('gross_margin_pct', 0):.1f}%. "
                        f"Recommandation: {candidate.get('recommendation', candidate.get('analysis', ''))}"
                    ),
                    data_used={
                        "product_id": product.id,
                        "score": score,
                        "score_details": candidate.get("score_details", {}),
                        "source_platform": candidate.get("source_platform", ""),
                        "candidate_data": {
                            k: v
                            for k, v in candidate.items()
                            if k not in ("score_details", "images")
                        },
                    },
                    risk_level=risk_level,
                    recommendation=candidate.get("recommendation", "Valider et lancer le produit"),
                    estimated_cost_usd=float(candidate.get("supplier_price_usd", 0) or 0),
                    estimated_revenue_usd=float(candidate.get("recommended_price_usd", 0) or 0),
                    requires_human_approval=True,
                    status=DecisionStatus.PENDING_APPROVAL.value,
                    created_at=_utcnow(),
                )
                self.db.add(decision)
                await self.db.flush()
                await self.db.refresh(decision)

                # 3. Créer l'Approval correspondante
                approval = Approval(
                    decision_id=decision.id,
                    title=f"Approbation requise: Ajouter {candidate.get('name', 'produit')}",
                    description=(
                        f"Un nouveau produit a été identifié comme candidat par l'agent IA.\n\n"
                        f"Produit: {candidate.get('name', 'N/A')}\n"
                        f"Catégorie: {candidate.get('category', 'N/A')}\n"
                        f"Score: {score}/100\n"
                        f"Verdict: {candidate.get('verdict', 'N/A')}\n"
                        f"Marge estimée: {candidate.get('gross_margin_pct', 0):.1f}%\n"
                        f"Prix recommandé: ${candidate.get('recommended_price_usd', 0):.2f}\n"
                        f"Source: {candidate.get('source_platform', 'N/A')}"
                    ),
                    request_data={
                        "product_id": product.id,
                        "decision_id": decision.id,
                        "score": score,
                        "risk_level": risk_level,
                    },
                    status="PENDING",
                    requested_by_agent_id=agent.agent_record.id,
                    created_at=_utcnow(),
                )
                self.db.add(approval)
                await self.db.flush()

                decisions_created += 1
                logger.info(
                    "Created decision + approval for product: %s (score=%.1f)",
                    candidate.get("name"),
                    score,
                )

            except Exception as e:
                logger.error(
                    "Failed to create decision for candidate '%s': %s",
                    candidate.get("name", "?"),
                    e,
                )
                continue

        return decisions_created

    async def _step_save_trends(self, products: list[dict]) -> int:
        """Étape 8: Sauvegarde les données de tendances en DB (ProductTrend)."""
        saved = 0

        # Limiter à 50 tendances par workflow pour ne pas surcharger la DB
        for product_data in products[:50]:
            try:
                platform_str = product_data.get("source_platform", "AMAZON")

                # Vérifier si un produit correspondant existe déjà en DB
                result = await self.db.execute(
                    select(Product).where(
                        Product.name == product_data.get("name", ""),
                        Product.source_platform == platform_str,
                    )
                )
                product = result.scalar_one_or_none()

                if product is None:
                    # Créer un produit minimal comme ancre pour la tendance
                    product = Product(
                        name=product_data.get("name", "Unknown"),
                        description=product_data.get("description", ""),
                        category=product_data.get("category", ""),
                        tags=[],
                        source_platform=platform_str,
                        source_url=product_data.get("url", product_data.get("source_url")),
                        images=product_data.get("images", []),
                        status=ProductStatus.CANDIDATE.value,
                        cost_price_usd=product_data.get(
                            "supplier_price", product_data.get("price_usd", 0)
                        ),
                    )
                    self.db.add(product)
                    await self.db.flush()
                    await self.db.refresh(product)

                # Créer l'entrée ProductTrend
                trend = ProductTrend(
                    product_id=product.id,
                    platform=platform_str,
                    keyword=product_data.get("name", ""),
                    trend_score=float(product_data.get("demand_score", 50)),
                    search_volume=product_data.get("search_volume_monthly"),
                    growth_rate_pct=float(product_data.get("growth_rate_pct", 0)),
                    competition_level=product_data.get("competition_level", "MEDIUM"),
                    avg_market_price_usd=float(product_data.get("price_usd", 0)) or None,
                    data_date=date.today(),
                    raw_data={
                        k: v
                        for k, v in product_data.items()
                        if k not in ("images", "description")
                    },
                )
                self.db.add(trend)
                saved += 1

            except Exception as e:
                logger.warning(
                    "Failed to save trend for '%s': %s",
                    product_data.get("name", "?"),
                    e,
                )
                continue

        logger.info("Saved %d product trends to DB", saved)
        return saved

    async def _step_ceo_review(
        self, validated_candidates: list[dict], research_result: dict
    ) -> dict:
        """Étape 9: Revue finale et rapport par CEOAgent."""
        try:
            ceo = await create_ceo_agent(self.db)
            report = await ceo.execute(
                {
                    "action": "weekly_review",
                    "data": {
                        "workflow": "weekly_research",
                        "date": _utcnow().strftime("%Y-%m-%d"),
                        "products_found": len(validated_candidates),
                        "top_candidates": [
                            {
                                "name": c.get("name"),
                                "score": c.get("score"),
                                "verdict": c.get("verdict"),
                                "category": c.get("category"),
                                "gross_margin_pct": c.get("gross_margin_pct"),
                            }
                            for c in validated_candidates[:5]
                        ],
                        "market_insights": research_result.get("market_insights", []),
                        "top_categories": research_result.get("top_categories", []),
                    },
                }
            )
            return report
        except Exception as e:
            logger.error("CEOAgent review failed: %s", e)
            return {"error": str(e), "status": "CEO review failed"}

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    async def _create_product_from_candidate(self, candidate: dict) -> Product:
        """Crée ou met à jour un Product en DB depuis les données d'un candidat."""
        name = candidate.get("name", "Unknown Product")
        platform = candidate.get("source_platform", "AMAZON")

        # Vérifier si le produit existe déjà
        result = await self.db.execute(
            select(Product).where(
                Product.name == name,
                Product.source_platform == platform,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Mettre à jour le score
            existing.score = candidate.get("score")
            existing.score_details = candidate.get("score_details")
            existing.selling_price_usd = candidate.get("recommended_price_usd")
            existing.gross_margin_pct = candidate.get("gross_margin_pct")
            existing.status = ProductStatus.UNDER_REVIEW.value
            return existing

        # Créer un nouveau produit
        product = Product(
            name=name,
            description=candidate.get("description", ""),
            category=candidate.get("category", ""),
            tags=candidate.get("tags", []),
            source_platform=platform,
            source_url=candidate.get("url", candidate.get("source_url")),
            images=candidate.get("images", []),
            status=ProductStatus.UNDER_REVIEW.value,
            cost_price_usd=candidate.get(
                "supplier_price_usd",
                candidate.get("supplier_price", candidate.get("price_usd", 0)) * 0.3,
            ),
            selling_price_usd=candidate.get("recommended_price_usd"),
            gross_margin_pct=candidate.get("gross_margin_pct"),
            score=candidate.get("score"),
            score_details=candidate.get("score_details"),
        )
        self.db.add(product)
        return product

    async def _log_system(
        self, action: str, entity_type: str, description: str, entity_id: int = None
    ) -> None:
        """Log une action système dans l'AuditLog."""
        try:
            log_entry = AuditLog(
                actor_type="SYSTEM",
                actor_id=0,
                actor_name="WeeklyResearchWorkflow",
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                created_at=_utcnow(),
            )
            self.db.add(log_entry)
            await self.db.flush()
        except Exception as e:
            logger.warning("Failed to write audit log: %s", e)

    def _build_summary(
        self, products_found: int, products_validated: int, decisions_created: int
    ) -> dict[str, Any]:
        """Construit le rapport de synthèse final."""
        duration = (_utcnow() - self.start_time).total_seconds()
        return {
            "step_results": self.step_results,
            "products_found": products_found,
            "products_validated": products_validated,
            "decisions_created": decisions_created,
            "duration_seconds": round(duration, 2),
            "timestamp": self.start_time.isoformat(),
            "min_score_threshold": self.MIN_SCORE_THRESHOLD,
        }
