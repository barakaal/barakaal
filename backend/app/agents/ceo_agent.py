"""
CEOAgent: top-level orchestrator for AI Dropship Company OS.

Responsibilities:
  - Weekly performance review across all departments
  - Strategic decisions (product lines, market expansion, budget allocation)
  - Department summary consolidation
  - Growth planning with multi-month horizon
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class CEOAgent(BaseAgent):
    """AI CEO — orchestrates the entire dropshipping operation."""

    SYSTEM_PROMPT = (
        "Tu es le CEO IA de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu supervises toutes les opérations: produits, sourcing, marketing, commandes, "
        "finances, support client et conformité. "
        "Ton rôle est de prendre des décisions stratégiques basées sur les données, "
        "de coordonner les managers, et de maximiser la croissance durable de l'entreprise. "
        "Tu analyses les performances globales, identifies les opportunités et les risques, "
        "et formules des recommandations précises et actionnables. "
        "Toutes tes décisions financières importantes nécessitent une validation humaine."
    )

    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch to the correct action handler based on task_input['action'].

        Supported actions:
          - weekly_review
          - strategic_decision
          - department_report
          - growth_planning
        """
        action = task_input.get("action", "strategic_decision")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"CEO Action: {action}",
            description=f"Exécution de l'action CEO: {action}",
            input_data=task_input,
            priority=TaskPriority.HIGH.value,
        )

        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "weekly_review":
                result = await self._weekly_review(data)
            elif action == "strategic_decision":
                result = await self._strategic_decision(data)
            elif action == "department_report":
                result = await self._department_report(data)
            elif action == "growth_planning":
                result = await self._growth_planning(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(
                task,
                TaskStatus.COMPLETED.value,
                output_data=result,
            )
            return result

        except Exception as exc:
            logger.exception(
                "CEOAgent.execute failed for action=%s: %s", action, exc
            )
            await self.update_task_status(
                task,
                TaskStatus.FAILED.value,
                error=str(exc),
            )
            raise

    # ------------------------------------------------------------------ #
    # Action handlers
    # ------------------------------------------------------------------ #

    async def _weekly_review(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Consolidated weekly review of all departmental KPIs.

        Expected data keys:
          - revenue_usd: float
          - orders_count: int
          - return_rate_pct: float
          - ad_spend_usd: float
          - new_products_listed: int
          - customer_satisfaction_score: float  (0-10)
          - department_summaries: dict  (optional)
        """
        prompt = (
            "Effectue la revue hebdomadaire complète de l'entreprise de dropshipping.\n\n"
            f"Données de la semaine:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Fournis une analyse structurée en JSON avec les champs suivants:\n"
            "{\n"
            '  "overall_health": "EXCELLENT|GOOD|AVERAGE|POOR|CRITICAL",\n'
            '  "revenue_analysis": "...",\n'
            '  "key_achievements": ["..."],\n'
            '  "key_issues": ["..."],\n'
            '  "department_grades": {"marketing": "A|B|C|D|F", ...},\n'
            '  "priority_actions": ["..."],\n'
            '  "budget_recommendations": {"...": ...},\n'
            '  "next_week_targets": {"revenue_usd": ..., "orders_count": ...},\n'
            '  "risk_alerts": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        analysis = self._parse_json_response(response)

        # Create a strategic decision if the health is poor or critical
        health = analysis.get("overall_health", "AVERAGE")
        if health in ("POOR", "CRITICAL"):
            risk = RiskLevel.HIGH.value if health == "POOR" else RiskLevel.CRITICAL.value
            await self.create_decision(
                task=None,
                decision_type="WEEKLY_REVIEW_ALERT",
                title=f"Alerte santé entreprise: {health}",
                rationale=f"La revue hebdomadaire indique un état {health}. Actions immédiates requises.",
                data_used=data,
                risk_level=risk,
                recommendation="; ".join(analysis.get("priority_actions", [])),
                requires_human_approval=True,
            )

        await self.log_action(
            action="WEEKLY_REVIEW",
            entity_type="ceo_review",
            entity_id=None,
            description=f"Revue hebdomadaire CEO — santé globale: {health}",
            new_data={"overall_health": health, "priority_actions": analysis.get("priority_actions", [])},
        )

        return analysis

    async def _strategic_decision(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a strategic decision proposal and produce a recommendation.

        Expected data keys:
          - topic: str  (e.g. "expansion vers marché européen")
          - context: str
          - options: list[dict]  (optional, list of alternatives)
          - budget_available_usd: float  (optional)
          - timeline_months: int  (optional)
        """
        topic = data.get("topic", "Décision stratégique")
        prompt = (
            f"Analyse la décision stratégique suivante pour l'entreprise de dropshipping:\n\n"
            f"Sujet: {topic}\n"
            f"Contexte et données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Fournis une analyse stratégique complète en JSON:\n"
            "{\n"
            '  "decision_title": "...",\n'
            '  "recommended_option": "...",\n'
            '  "rationale": "...",\n'
            '  "pros": ["..."],\n'
            '  "cons": ["..."],\n'
            '  "risks": [{"risk": "...", "mitigation": "..."}],\n'
            '  "estimated_cost_usd": 0.0,\n'
            '  "estimated_revenue_impact_usd": 0.0,\n'
            '  "timeline_months": 0,\n'
            '  "kpis_to_track": ["..."],\n'
            '  "requires_human_approval": true,\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        analysis = self._parse_json_response(response)

        estimated_cost = float(analysis.get("estimated_cost_usd", 0.0))
        risk_level = analysis.get("risk_level", RiskLevel.MEDIUM.value)
        requires_approval = analysis.get("requires_human_approval", True)

        decision = await self.create_decision(
            task=None,
            decision_type="STRATEGIC_DECISION",
            title=analysis.get("decision_title", topic),
            rationale=analysis.get("rationale", ""),
            data_used=data,
            risk_level=risk_level,
            recommendation=analysis.get("recommended_option", ""),
            estimated_cost_usd=estimated_cost if estimated_cost > 0 else None,
            estimated_revenue_usd=float(analysis.get("estimated_revenue_impact_usd", 0.0)) or None,
            requires_human_approval=requires_approval,
        )

        analysis["decision_id"] = decision.id
        return analysis

    async def _department_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate an executive summary report from department data.

        Expected data keys:
          - departments: dict  (department_name → metrics dict)
          - period: str  (e.g. "Q1 2025")
        """
        period = data.get("period", "période courante")
        prompt = (
            f"Génère un rapport exécutif consolidé pour la période: {period}\n\n"
            f"Données par département:\n{json.dumps(data.get('departments', {}), indent=2, ensure_ascii=False)}\n\n"
            "Format JSON attendu:\n"
            "{\n"
            '  "period": "...",\n'
            '  "executive_summary": "...",\n'
            '  "top_performers": ["dept1", "dept2"],\n'
            '  "underperformers": ["dept3"],\n'
            '  "cross_department_insights": ["..."],\n'
            '  "resource_reallocation_suggestions": [{"from": "...", "to": "...", "reason": "..."}],\n'
            '  "overall_score": 0.0,\n'
            '  "department_scores": {"dept_name": 0.0},\n'
            '  "strategic_recommendations": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        report = self._parse_json_response(response)

        await self.log_action(
            action="DEPARTMENT_REPORT",
            entity_type="ceo_report",
            entity_id=None,
            description=f"Rapport départemental CEO — période: {period}",
            new_data={"period": period, "overall_score": report.get("overall_score")},
        )

        return report

    async def _growth_planning(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Build a multi-month growth plan for the company.

        Expected data keys:
          - current_mrr_usd: float
          - target_mrr_usd: float
          - horizon_months: int
          - available_budget_usd: float
          - current_strengths: list[str]  (optional)
          - current_weaknesses: list[str]  (optional)
          - market_opportunities: list[str]  (optional)
        """
        horizon = data.get("horizon_months", 12)
        target_mrr = data.get("target_mrr_usd", 0)
        prompt = (
            f"Élabore un plan de croissance sur {horizon} mois pour l'entreprise de dropshipping.\n\n"
            f"Données actuelles et objectifs:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON du plan:\n"
            "{\n"
            '  "plan_title": "...",\n'
            '  "horizon_months": 0,\n'
            '  "current_mrr_usd": 0.0,\n'
            '  "target_mrr_usd": 0.0,\n'
            '  "monthly_milestones": [{"month": 1, "target_mrr_usd": 0.0, "key_actions": ["..."]}],\n'
            '  "growth_levers": [{"lever": "...", "impact": "HIGH|MEDIUM|LOW", "effort": "HIGH|MEDIUM|LOW", "cost_usd": 0.0}],\n'
            '  "required_investments": [{"category": "...", "amount_usd": 0.0, "rationale": "..."}],\n'
            '  "total_investment_usd": 0.0,\n'
            '  "projected_roi_pct": 0.0,\n'
            '  "key_risks": [{"risk": "...", "probability": "HIGH|MEDIUM|LOW", "mitigation": "..."}],\n'
            '  "team_scaling_needs": ["..."],\n'
            '  "technology_needs": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        plan = self._parse_json_response(response)

        total_investment = float(plan.get("total_investment_usd", 0.0))
        risk_level = RiskLevel.HIGH.value if total_investment > 10000 else RiskLevel.MEDIUM.value

        decision = await self.create_decision(
            task=None,
            decision_type="GROWTH_PLAN",
            title=plan.get("plan_title", f"Plan de croissance {horizon} mois"),
            rationale=f"Plan pour atteindre {target_mrr} USD MRR en {horizon} mois",
            data_used=data,
            risk_level=risk_level,
            recommendation=f"Investissement total requis: {total_investment} USD",
            estimated_cost_usd=total_investment if total_investment > 0 else None,
            estimated_revenue_usd=float(data.get("target_mrr_usd", 0.0)) * horizon or None,
            requires_human_approval=True,
        )

        plan["decision_id"] = decision.id
        return plan

    # ------------------------------------------------------------------ #
    # Report
    # ------------------------------------------------------------------ #

    async def generate_report(self) -> dict[str, Any]:
        """Return a structured status report for the CEO agent."""
        prompt = (
            "En tant que CEO de l'entreprise de dropshipping, génère un rapport de statut "
            "résumant les activités récentes, les décisions prises, et les priorités immédiates. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "CEO",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "recent_activities": ["..."],\n'
            '  "pending_decisions": 0,\n'
            '  "key_metrics": {},\n'
            '  "next_actions": ["..."]\n'
            "}"
        )
        response = await self.think(prompt)
        return self._parse_json_response(response)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from Claude's response, with graceful fallback."""
        # Try to extract JSON block if wrapped in markdown code fences
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
            logger.warning("CEOAgent: could not parse JSON response, returning raw")
            return {"raw": response}
