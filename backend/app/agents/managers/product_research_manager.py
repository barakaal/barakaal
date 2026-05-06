"""
ProductResearchManagerAgent: manages product discovery and trend analysis.

Responsibilities:
  - Coordinate trend analysts (Amazon, AliExpress, TikTok, Google, eBay)
  - Evaluate product viability (margins, competition, demand)
  - Decide which products to add to the catalog
  - Report top opportunities to the CEO
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class ProductResearchManagerAgent(BaseAgent):
    """Manager responsible for product research and catalog strategy."""

    SYSTEM_PROMPT = (
        "Tu es le Manager Recherche Produits de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu coordonnes les analystes de tendances sur Amazon, AliExpress, TikTok, Google et eBay. "
        "Tu évalues la viabilité des produits (marges, concurrence, demande, potentiel viral), "
        "décides quels produits ajouter au catalogue, et reportes les meilleures opportunités au CEO. "
        "Tu analyses les données de marché de manière objective et données-drivée. "
        "Tu priorises les produits avec: marge > 30%, potentiel de demande élevé, concurrence modérée."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "evaluate_products")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Product Research: {action}",
            description=f"Recherche produits — action: {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "evaluate_products":
                result = await self._evaluate_products(data)
            elif action == "trend_analysis":
                result = await self._trend_analysis(data)
            elif action == "catalog_update":
                result = await self._catalog_update(data)
            elif action == "competitive_analysis":
                result = await self._competitive_analysis(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("ProductResearchManagerAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _evaluate_products(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate a list of product candidates for catalog inclusion.

        Expected data:
          - products: list[dict] each with: name, category, cost_usd, suggested_price_usd,
                      platform_data (dict), search_volume (optional)
        """
        prompt = (
            "Évalue les candidats produits suivants pour inclusion dans le catalogue dropshipping.\n\n"
            f"Données produits:\n{json.dumps(data.get('products', []), indent=2, ensure_ascii=False)}\n\n"
            "Pour chaque produit, évalue:\n"
            "- Marge brute (%)\n"
            "- Potentiel de demande (score 1-10)\n"
            "- Niveau de concurrence (LOW/MEDIUM/HIGH)\n"
            "- Risque (LOW/MEDIUM/HIGH/CRITICAL)\n"
            "- Recommandation (AJOUTER/REJETER/TESTER)\n\n"
            "Format JSON:\n"
            "{\n"
            '  "evaluated_products": [\n'
            '    {\n'
            '      "name": "...",\n'
            '      "margin_pct": 0.0,\n'
            '      "demand_score": 0,\n'
            '      "competition_level": "LOW|MEDIUM|HIGH",\n'
            '      "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '      "recommendation": "AJOUTER|REJETER|TESTER",\n'
            '      "rationale": "..."\n'
            '    }\n'
            '  ],\n'
            '  "top_picks": ["product_name"],\n'
            '  "summary": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        # Create decisions for products recommended for addition
        top_picks = result.get("top_picks", [])
        if top_picks:
            await self.create_decision(
                task=None,
                decision_type="PRODUCT_CATALOG_UPDATE",
                title=f"Ajout de {len(top_picks)} produit(s) au catalogue",
                rationale=result.get("summary", ""),
                data_used={"top_picks": top_picks, "evaluated_count": len(data.get("products", []))},
                risk_level=RiskLevel.LOW.value,
                recommendation=f"Ajouter: {', '.join(top_picks)}",
                requires_human_approval=False,
            )

        return result

    async def _trend_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Synthesize trend reports from multiple platforms.

        Expected data:
          - platform_reports: dict  {platform_name: report_data}
          - category_focus: str  (optional)
          - date_range: str  (optional)
        """
        category = data.get("category_focus", "tous secteurs")
        prompt = (
            f"Synthétise les rapports de tendances de plusieurs plateformes pour: {category}\n\n"
            f"Rapports par plateforme:\n{json.dumps(data.get('platform_reports', {}), indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "trending_categories": [{"category": "...", "growth_pct": 0.0, "platforms": ["..."]}],\n'
            '  "top_trending_products": [{"product": "...", "trend_score": 0, "platforms": ["..."]}],\n'
            '  "emerging_trends": ["..."],\n'
            '  "declining_trends": ["..."],\n'
            '  "seasonal_insights": "...",\n'
            '  "recommended_focus": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _catalog_update(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a catalog update plan based on performance data.

        Expected data:
          - current_catalog: list[dict]  (products with performance metrics)
          - products_to_add: list[dict]  (optional)
        """
        prompt = (
            "Génère un plan de mise à jour du catalogue produits.\n\n"
            f"Données catalogue actuel:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "products_to_add": [{"name": "...", "reason": "..."}],\n'
            '  "products_to_remove": [{"name": "...", "reason": "..."}],\n'
            '  "products_to_optimize": [{"name": "...", "suggestion": "..."}],\n'
            '  "catalog_health_score": 0.0,\n'
            '  "summary": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="CATALOG_UPDATE_PLAN",
            entity_type="product_catalog",
            entity_id=None,
            description=f"Plan de mise à jour catalogue — score santé: {result.get('catalog_health_score')}",
            new_data=result,
        )

        return result

    async def _competitive_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Perform competitive analysis for a product or category.

        Expected data:
          - product_or_category: str
          - competitors: list[dict]  (optional, each with name, price, features)
          - our_price_usd: float  (optional)
        """
        subject = data.get("product_or_category", "produit")
        prompt = (
            f"Effectue une analyse concurrentielle pour: {subject}\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "market_position": "LEADER|CHALLENGER|FOLLOWER|NICHE",\n'
            '  "price_competitiveness": "VERY_COMPETITIVE|COMPETITIVE|AVERAGE|EXPENSIVE",\n'
            '  "our_advantages": ["..."],\n'
            '  "our_disadvantages": ["..."],\n'
            '  "competitor_insights": [{"competitor": "...", "strength": "...", "weakness": "..."}],\n'
            '  "recommended_price_usd": 0.0,\n'
            '  "differentiation_strategy": "...",\n'
            '  "threat_level": "LOW|MEDIUM|HIGH|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Manager Recherche Produits, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "ProductResearchManager",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "products_evaluated_this_week": 0,\n'
            '  "products_added_to_catalog": 0,\n'
            '  "top_opportunities": ["..."],\n'
            '  "next_actions": ["..."]\n'
            "}"
        )
        response = await self.think(prompt)
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        text = response.strip()
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return {"raw": response}
