"""
CustomerSupportManagerAgent: manages customer satisfaction and support operations.

Responsibilities:
  - Analyze support ticket trends
  - Define escalation policies
  - Monitor CSAT, NPS, response times
  - Identify systemic product or process issues
  - Propose refund/resolution policies
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class CustomerSupportManagerAgent(BaseAgent):
    """Manager responsible for customer support and satisfaction."""

    SYSTEM_PROMPT = (
        "Tu es le Manager Support Client de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu supervises toutes les interactions clients: tickets, réclamations, avis et retours. "
        "Tu analyses les tendances de support pour identifier les problèmes systémiques. "
        "Tu gères les métriques: CSAT, NPS, temps de réponse moyen, taux de résolution au premier contact. "
        "Tu définis les politiques d'escalade et formes les équipes de support. "
        "Tu protèges la réputation de la marque en résolvant proactivement les problèmes clients. "
        "Toute décision de remboursement ou compensation > $0 requiert une validation humaine."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_tickets")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Support: {action}",
            description=f"Support client — action: {action}",
            input_data=task_input,
            priority=TaskPriority.HIGH.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "analyze_tickets":
                result = await self._analyze_tickets(data)
            elif action == "escalation_policy":
                result = await self._escalation_policy(data)
            elif action == "csat_analysis":
                result = await self._csat_analysis(data)
            elif action == "resolve_complaint":
                result = await self._resolve_complaint(data, task)
            elif action == "support_optimization":
                result = await self._support_optimization(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("CustomerSupportManagerAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_tickets(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze support ticket volume and categories.

        Expected data:
          - period_days: int
          - tickets: list[dict]  (category, count, avg_resolution_hours, escalated_count)
          - total_tickets: int
          - open_tickets: int
        """
        prompt = (
            "Analyse les tickets de support client.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "total_volume": 0,\n'
            '  "top_categories": [{"category": "...", "count": 0, "pct": 0.0}],\n'
            '  "avg_resolution_hours": 0.0,\n'
            '  "escalation_rate_pct": 0.0,\n'
            '  "systemic_issues": ["..."],\n'
            '  "root_causes": ["..."],\n'
            '  "recommended_fixes": [{"issue": "...", "fix": "...", "owner": "..."}],\n'
            '  "support_health": "EXCELLENT|GOOD|AVERAGE|POOR|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        health = result.get("support_health", "AVERAGE")
        if health in ("POOR", "CRITICAL"):
            await self.create_decision(
                task=None,
                decision_type="SUPPORT_ALERT",
                title=f"Alerte support client: {health}",
                rationale="; ".join(result.get("systemic_issues", [])),
                data_used=data,
                risk_level=RiskLevel.HIGH.value,
                recommendation="; ".join([f["fix"] for f in result.get("recommended_fixes", [])]),
                requires_human_approval=True,
            )

        return result

    async def _escalation_policy(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Define or update escalation policies based on ticket patterns.

        Expected data:
          - current_policy: dict  (optional)
          - ticket_patterns: dict  (categories with avg resolution times)
          - team_capacity: dict  (optional, agents per tier)
        """
        prompt = (
            "Définis une politique d'escalade pour le support client.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "escalation_tiers": [\n'
            '    {"tier": 1, "description": "...", "criteria": ["..."], "response_time_hours": 0, "resolution_time_hours": 0}\n'
            '  ],\n'
            '  "auto_escalation_rules": [{"trigger": "...", "action": "..."}],\n'
            '  "vip_customer_policy": "...",\n'
            '  "refund_authority": {"tier1_max_usd": 0.0, "tier2_max_usd": 0.0, "above_requires_approval": true},\n'
            '  "implementation_steps": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _csat_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze customer satisfaction metrics.

        Expected data:
          - period_days: int
          - csat_score: float  (0-100)
          - nps_score: float  (-100 to 100)
          - reviews: dict  {platform: {avg_rating, count, sentiment}}
          - top_complaints: list[str]  (optional)
          - top_praises: list[str]  (optional)
        """
        csat = data.get("csat_score", 0)
        nps = data.get("nps_score", 0)
        prompt = (
            f"Analyse la satisfaction client: CSAT={csat}, NPS={nps}\n\n"
            f"Données complètes:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "csat_benchmark": "EXCELLENT|GOOD|AVERAGE|POOR",\n'
            '  "nps_category": "PROMOTER_ZONE|NEUTRAL|DETRACTOR_ZONE",\n'
            '  "sentiment_analysis": "...",\n'
            '  "key_satisfaction_drivers": ["..."],\n'
            '  "key_dissatisfaction_drivers": ["..."],\n'
            '  "action_plan": [{"action": "...", "expected_csat_impact": "+0.0", "priority": "HIGH|MEDIUM|LOW"}],\n'
            '  "csat_target_90_days": 0.0\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _resolve_complaint(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Resolve a specific customer complaint.

        Expected data:
          - complaint_id: str
          - customer_id: str
          - complaint_text: str
          - order_id: str  (optional)
          - order_value_usd: float  (optional)
          - customer_history: dict  (optional, orders_count, lifetime_value_usd)
        """
        complaint_id = data.get("complaint_id", "N/A")
        order_value = float(data.get("order_value_usd", 0.0))
        ltv = float(data.get("customer_history", {}).get("lifetime_value_usd", 0.0))

        prompt = (
            f"Résous la réclamation client #{complaint_id}.\n\n"
            f"Détails:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "complaint_category": "...",\n'
            '  "severity": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "resolution": "REFUND|REPLACE|DISCOUNT|APOLOGY|ESCALATE",\n'
            '  "compensation_usd": 0.0,\n'
            '  "customer_response": "...",\n'
            '  "internal_action": "...",\n'
            '  "customer_retention_risk": "LOW|MEDIUM|HIGH",\n'
            '  "requires_human_approval": true\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        compensation = float(result.get("compensation_usd", 0.0))
        requires_approval = result.get("requires_human_approval", True) or compensation > 0

        if requires_approval:
            await self.create_decision(
                task=task,
                decision_type="COMPLAINT_RESOLUTION",
                title=f"Résolution réclamation #{complaint_id}",
                rationale=result.get("internal_action", ""),
                data_used={
                    "complaint_id": complaint_id,
                    "order_value_usd": order_value,
                    "customer_ltv_usd": ltv,
                },
                risk_level=RiskLevel.MEDIUM.value if compensation < 100 else RiskLevel.HIGH.value,
                recommendation=result.get("resolution", "ESCALATE"),
                estimated_cost_usd=compensation if compensation > 0 else None,
                requires_human_approval=True,
            )

        return result

    async def _support_optimization(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Propose support process improvements.

        Expected data:
          - avg_response_time_hours: float
          - first_contact_resolution_pct: float
          - agent_utilization_pct: float
          - top_ticket_categories: list[str]
          - automation_potential: dict  (optional)
        """
        prompt = (
            "Identifie les opportunités d'optimisation du support client.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "efficiency_score": 0.0,\n'
            '  "automation_opportunities": [{"category": "...", "automation_pct": 0.0, "tool": "..."}],\n'
            '  "process_improvements": [{"improvement": "...", "impact": "HIGH|MEDIUM|LOW", "effort": "LOW|MEDIUM|HIGH"}],\n'
            '  "training_recommendations": ["..."],\n'
            '  "technology_recommendations": ["..."],\n'
            '  "expected_response_time_improvement_hrs": 0.0,\n'
            '  "expected_fcr_improvement_pct": 0.0\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Manager Support Client, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "CustomerSupportManager",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "open_tickets": 0,\n'
            '  "csat_score": 0.0,\n'
            '  "avg_response_time_hours": 0.0,\n'
            '  "escalated_tickets": 0,\n'
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
