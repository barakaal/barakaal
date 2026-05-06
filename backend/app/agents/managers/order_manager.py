"""
OrderManagerAgent: manages order processing, fulfillment and returns.

Responsibilities:
  - Monitor order status and fulfillment pipeline
  - Handle escalated order issues (delays, disputes, fraud flags)
  - Optimize fulfillment workflows
  - Coordinate with suppliers on shipping
  - Report order KPIs (on-time rate, return rate, satisfaction)
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class OrderManagerAgent(BaseAgent):
    """Manager responsible for order operations and fulfillment."""

    SYSTEM_PROMPT = (
        "Tu es le Manager Commandes de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu supervises tout le cycle de vie des commandes: réception, traitement, expédition, livraison, retours. "
        "Tu monitores les métriques: taux de livraison à temps, taux de retour, satisfaction client, délai moyen. "
        "Tu identifies et résous les problèmes de fulfillment, coordonnes avec les fournisseurs. "
        "Tu détectes les anomalies (pics de retours, délais anormaux, fraudes potentielles) et escalades. "
        "Tout remboursement > $0 nécessite une validation humaine."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "monitor_orders")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Orders: {action}",
            description=f"Commandes — action: {action}",
            input_data=task_input,
            priority=TaskPriority.HIGH.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "monitor_orders":
                result = await self._monitor_orders(data)
            elif action == "handle_issue":
                result = await self._handle_issue(data, task)
            elif action == "process_returns":
                result = await self._process_returns(data, task)
            elif action == "fulfillment_optimization":
                result = await self._fulfillment_optimization(data)
            elif action == "order_analytics":
                result = await self._order_analytics(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("OrderManagerAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _monitor_orders(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Monitor current order pipeline status.

        Expected data:
          - orders_summary: dict  (pending, processing, shipped, delivered, returned, cancelled)
          - delayed_orders: list[dict]  (order_id, days_delayed, customer_country)
          - period_days: int
        """
        prompt = (
            "Analyse l'état actuel du pipeline de commandes.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "pipeline_health": "EXCELLENT|GOOD|AVERAGE|POOR|CRITICAL",\n'
            '  "on_time_delivery_pct": 0.0,\n'
            '  "average_delivery_days": 0.0,\n'
            '  "issues_detected": ["..."],\n'
            '  "orders_at_risk": [{"order_id": "...", "risk": "..."}],\n'
            '  "immediate_actions": ["..."],\n'
            '  "capacity_status": "OK|STRAINED|OVERLOADED"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        health = result.get("pipeline_health", "AVERAGE")
        if health in ("POOR", "CRITICAL"):
            await self.create_decision(
                task=None,
                decision_type="ORDER_PIPELINE_ALERT",
                title=f"Alerte pipeline commandes: {health}",
                rationale="; ".join(result.get("issues_detected", [])),
                data_used=data,
                risk_level=RiskLevel.HIGH.value if health == "POOR" else RiskLevel.CRITICAL.value,
                recommendation="; ".join(result.get("immediate_actions", [])),
                requires_human_approval=True,
            )

        return result

    async def _handle_issue(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Handle a specific order issue.

        Expected data:
          - order_id: str
          - issue_type: str  (DELAY|LOST|DAMAGED|WRONG_ITEM|DISPUTE)
          - customer_email: str  (optional)
          - order_value_usd: float
          - details: str
        """
        order_id = data.get("order_id", "N/A")
        issue_type = data.get("issue_type", "UNKNOWN")
        order_value = float(data.get("order_value_usd", 0.0))
        prompt = (
            f"Résous le problème de commande #{order_id}: {issue_type}\n\n"
            f"Détails:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "issue_type": "...",\n'
            '  "severity": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "resolution": "REFUND|REPLACE|RESHIP|DISCOUNT|ESCALATE|CLOSE",\n'
            '  "resolution_details": "...",\n'
            '  "refund_amount_usd": 0.0,\n'
            '  "customer_message": "...",\n'
            '  "internal_notes": "...",\n'
            '  "requires_human_approval": true\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        refund_amount = float(result.get("refund_amount_usd", 0.0))
        requires_approval = result.get("requires_human_approval", True) or refund_amount > 0

        if requires_approval:
            await self.create_decision(
                task=task,
                decision_type="ORDER_RESOLUTION",
                title=f"Résolution commande #{order_id}: {issue_type}",
                rationale=result.get("resolution_details", ""),
                data_used=data,
                risk_level=RiskLevel.MEDIUM.value if order_value < 100 else RiskLevel.HIGH.value,
                recommendation=result.get("resolution", "ESCALATE"),
                estimated_cost_usd=refund_amount if refund_amount > 0 else None,
                requires_human_approval=True,
            )

        return result

    async def _process_returns(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Process a batch of return requests.

        Expected data:
          - returns: list[dict]  (order_id, reason, product_name, value_usd, customer_id)
          - return_policy: str  (optional)
        """
        returns = data.get("returns", [])
        total_value = sum(r.get("value_usd", 0.0) for r in returns)
        prompt = (
            f"Traite ces {len(returns)} demandes de retour (valeur totale: ${total_value:.2f}).\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "processed_returns": [\n'
            '    {"order_id": "...", "decision": "APPROVE|REJECT|PARTIAL", "refund_usd": 0.0, "reason": "..."}\n'
            '  ],\n'
            '  "total_approved_refund_usd": 0.0,\n'
            '  "total_rejected": 0,\n'
            '  "return_patterns": ["..."],\n'
            '  "policy_recommendations": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        total_refund = float(result.get("total_approved_refund_usd", 0.0))
        if total_refund > 0:
            await self.create_decision(
                task=task,
                decision_type="BATCH_REFUNDS",
                title=f"Remboursements en lot: ${total_refund:.2f} pour {len(returns)} retour(s)",
                rationale=f"Traitement de {len(returns)} retours avec remboursement total de ${total_refund:.2f}",
                data_used={"returns_count": len(returns), "total_value_usd": total_value},
                risk_level=RiskLevel.HIGH.value if total_refund > 500 else RiskLevel.MEDIUM.value,
                recommendation=f"Approuver remboursements: ${total_refund:.2f}",
                estimated_cost_usd=total_refund,
                requires_human_approval=True,
            )

        return result

    async def _fulfillment_optimization(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze and optimize the fulfillment process.

        Expected data:
          - avg_processing_hours: float
          - avg_shipping_days: float
          - carrier_performance: dict  {carrier: {on_time_pct, avg_days, cost_per_order_usd}}
          - bottlenecks: list[str]  (optional)
        """
        prompt = (
            "Analyse et optimise le processus de fulfillment.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "current_efficiency_score": 0.0,\n'
            '  "bottlenecks_identified": ["..."],\n'
            '  "carrier_ranking": [{"carrier": "...", "score": 0.0, "recommendation": "USE|REDUCE|ELIMINATE"}],\n'
            '  "process_improvements": [{"improvement": "...", "impact": "HIGH|MEDIUM|LOW", "effort": "HIGH|MEDIUM|LOW"}],\n'
            '  "expected_time_savings_days": 0.0,\n'
            '  "expected_cost_savings_pct": 0.0\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _order_analytics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate comprehensive order analytics report.

        Expected data:
          - period_days: int
          - orders_data: dict  (total, gmv_usd, avg_order_value, by_country, by_product_category)
          - return_rate_pct: float
          - cancellation_rate_pct: float
        """
        prompt = (
            "Génère un rapport analytique complet des commandes.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "period_summary": "...",\n'
            '  "gmv_usd": 0.0,\n'
            '  "avg_order_value_usd": 0.0,\n'
            '  "top_markets": ["..."],\n'
            '  "top_product_categories": ["..."],\n'
            '  "return_analysis": "...",\n'
            '  "cancellation_analysis": "...",\n'
            '  "trends": ["..."],\n'
            '  "forecasted_next_period": {"orders": 0, "gmv_usd": 0.0}\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Manager Commandes, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "OrderManager",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "orders_today": 0,\n'
            '  "pending_issues": 0,\n'
            '  "on_time_delivery_pct": 0.0,\n'
            '  "return_rate_pct": 0.0,\n'
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
