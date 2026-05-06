"""
SourcingManagerAgent: manages supplier relationships and procurement.

Responsibilities:
  - Identify and evaluate suppliers (AliExpress, Alibaba, etc.)
  - Negotiate pricing and terms
  - Monitor supplier performance (lead times, quality, reliability)
  - Recommend supplier switches or diversification
  - All purchase orders above threshold require human approval
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.config import settings
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class SourcingManagerAgent(BaseAgent):
    """Manager responsible for supplier sourcing and procurement strategy."""

    SYSTEM_PROMPT = (
        "Tu es le Manager Sourcing de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu gères les relations fournisseurs sur AliExpress, Alibaba et autres plateformes. "
        "Tu évalues les fournisseurs selon: prix, délais de livraison, qualité, fiabilité et service. "
        "Tu négocie les meilleures conditions et diversifie les sources pour réduire les risques. "
        "Toute commande fournisseur > $0 nécessite une validation humaine selon les règles de sécurité. "
        "Tu surveilles en permanence les performances fournisseurs et escalades les problèmes critiques."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "evaluate_supplier")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Sourcing: {action}",
            description=f"Sourcing — action: {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "evaluate_supplier":
                result = await self._evaluate_supplier(data, task)
            elif action == "compare_suppliers":
                result = await self._compare_suppliers(data)
            elif action == "monitor_performance":
                result = await self._monitor_performance(data)
            elif action == "recommend_order":
                result = await self._recommend_order(data, task)
            elif action == "risk_assessment":
                result = await self._risk_assessment(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("SourcingManagerAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _evaluate_supplier(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Evaluate a potential or existing supplier.

        Expected data:
          - supplier_name: str
          - platform: str  (aliexpress|alibaba|other)
          - products: list[dict]  (name, price_usd, moq, lead_time_days)
          - seller_rating: float  (optional)
          - reviews_count: int  (optional)
          - return_rate_pct: float  (optional)
        """
        supplier = data.get("supplier_name", "fournisseur inconnu")
        prompt = (
            f"Évalue le fournisseur suivant pour le dropshipping:\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "supplier_name": "...",\n'
            '  "overall_score": 0.0,\n'
            '  "price_competitiveness": 0.0,\n'
            '  "quality_score": 0.0,\n'
            '  "reliability_score": 0.0,\n'
            '  "lead_time_score": 0.0,\n'
            '  "recommendation": "APPROUVER|REJETER|SURVEILLER",\n'
            '  "strengths": ["..."],\n'
            '  "weaknesses": ["..."],\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "rationale": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.create_decision(
            task=task,
            decision_type="SUPPLIER_EVALUATION",
            title=f"Évaluation fournisseur: {supplier}",
            rationale=result.get("rationale", ""),
            data_used=data,
            risk_level=result.get("risk_level", RiskLevel.MEDIUM.value),
            recommendation=result.get("recommendation", "SURVEILLER"),
            requires_human_approval=result.get("risk_level") in ("HIGH", "CRITICAL"),
        )

        return result

    async def _compare_suppliers(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Compare multiple suppliers for the same product category.

        Expected data:
          - product_category: str
          - suppliers: list[dict]  (each with name, price_usd, lead_time_days, rating, moq)
        """
        category = data.get("product_category", "catégorie")
        prompt = (
            f"Compare ces fournisseurs pour la catégorie: {category}\n\n"
            f"Fournisseurs:\n{json.dumps(data.get('suppliers', []), indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "winner": "supplier_name",\n'
            '  "runner_up": "supplier_name",\n'
            '  "comparison_matrix": [\n'
            '    {"supplier": "...", "price_rank": 1, "quality_rank": 1, "speed_rank": 1, "overall_rank": 1}\n'
            '  ],\n'
            '  "recommendation": "...",\n'
            '  "diversification_advice": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _monitor_performance(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Monitor and report on supplier performance metrics.

        Expected data:
          - supplier_name: str
          - period_days: int
          - metrics: dict  (on_time_delivery_pct, defect_rate_pct, avg_lead_time_days, disputes_count)
        """
        supplier = data.get("supplier_name", "fournisseur")
        metrics = data.get("metrics", {})
        prompt = (
            f"Analyse les performances du fournisseur: {supplier}\n\n"
            f"Métriques:\n{json.dumps(metrics, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "performance_grade": "A|B|C|D|F",\n'
            '  "on_time_delivery_assessment": "...",\n'
            '  "quality_assessment": "...",\n'
            '  "issues_detected": ["..."],\n'
            '  "action_required": true,\n'
            '  "action": "NONE|WARNING|REPLACE|ESCALATE",\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "recommendation": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        # Escalate if supplier performance is critically poor
        if result.get("action") in ("REPLACE", "ESCALATE"):
            await self.create_decision(
                task=None,
                decision_type="SUPPLIER_PERFORMANCE_ALERT",
                title=f"Alerte performance fournisseur: {supplier}",
                rationale=result.get("recommendation", ""),
                data_used=metrics,
                risk_level=result.get("risk_level", RiskLevel.HIGH.value),
                recommendation=result.get("action", "ESCALATE"),
                requires_human_approval=True,
            )

        return result

    async def _recommend_order(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Recommend a purchase order from a supplier.

        Expected data:
          - supplier_name: str
          - products: list[dict]  (name, quantity, unit_price_usd)
          - reason: str
          - urgency: str  (LOW|MEDIUM|HIGH)
        """
        supplier = data.get("supplier_name", "fournisseur")
        products = data.get("products", [])
        total_cost = sum(
            p.get("quantity", 0) * p.get("unit_price_usd", 0.0) for p in products
        )

        prompt = (
            f"Analyse cette recommandation de commande fournisseur:\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            f"Coût total estimé: ${total_cost:.2f}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "order_justified": true,\n'
            '  "total_cost_usd": 0.0,\n'
            '  "risk_assessment": "...",\n'
            '  "alternatives": ["..."],\n'
            '  "recommendation": "APPROUVER|MODIFIER|REJETER",\n'
            '  "conditions": ["..."],\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        # All orders require human approval per safety rules
        requires_approval = total_cost > settings.MAX_AUTO_SPEND_USD
        risk = result.get("risk_level", RiskLevel.MEDIUM.value)
        if total_cost > 0:
            risk = RiskLevel.HIGH.value if total_cost > 500 else RiskLevel.MEDIUM.value

        await self.create_decision(
            task=task,
            decision_type="PURCHASE_ORDER",
            title=f"Commande fournisseur: {supplier} — ${total_cost:.2f}",
            rationale=result.get("risk_assessment", ""),
            data_used=data,
            risk_level=risk,
            recommendation=result.get("recommendation", "APPROUVER"),
            estimated_cost_usd=total_cost,
            requires_human_approval=requires_approval or total_cost > 0,
        )

        result["total_cost_usd"] = total_cost
        result["requires_human_approval"] = requires_approval or total_cost > 0
        return result

    async def _risk_assessment(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Assess sourcing risks across the supply chain.

        Expected data:
          - suppliers: list[dict]  (name, dependency_pct, country, category)
          - current_issues: list[str]  (optional)
        """
        prompt = (
            "Effectue une évaluation des risques de sourcing pour la chaîne d'approvisionnement.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "overall_risk": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "concentration_risk": "...",\n'
            '  "geographic_risk": "...",\n'
            '  "identified_risks": [{"risk": "...", "impact": "HIGH|MEDIUM|LOW", "mitigation": "..."}],\n'
            '  "diversification_score": 0.0,\n'
            '  "recommended_actions": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Manager Sourcing, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "SourcingManager",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "active_suppliers_count": 0,\n'
            '  "pending_orders": 0,\n'
            '  "supplier_alerts": ["..."],\n'
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
