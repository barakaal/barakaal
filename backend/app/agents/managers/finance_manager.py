"""
FinanceManagerAgent: manages financial reporting, budgets and cash flow.

Responsibilities:
  - Track revenue, costs, margins and profitability
  - Budget planning and variance analysis
  - Cash flow monitoring
  - Financial risk assessment
  - ALL financial transactions require human approval
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class FinanceManagerAgent(BaseAgent):
    """Manager responsible for financial oversight and planning."""

    SYSTEM_PROMPT = (
        "Tu es le Manager Finance de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu supervises les finances: revenus, coûts, marges, flux de trésorerie, et rentabilité. "
        "Tu prépares les rapports financiers, analyses les écarts budgétaires, et surveilles les KPIs financiers. "
        "Tu identifies les risques financiers et recommandes des actions correctives. "
        "RÈGLE ABSOLUE: Toute transaction financière réelle (paiement, remboursement, virement) "
        "nécessite une validation humaine explicite. Tu ne peux qu'analyser et recommander. "
        "Tu calcules: marges brutes/nettes, CAC, LTV, ROAS, point mort, et prévisions."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "financial_report")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Finance: {action}",
            description=f"Finance — action: {action}",
            input_data=task_input,
            priority=TaskPriority.HIGH.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "financial_report":
                result = await self._financial_report(data)
            elif action == "budget_analysis":
                result = await self._budget_analysis(data, task)
            elif action == "cash_flow_forecast":
                result = await self._cash_flow_forecast(data)
            elif action == "profitability_analysis":
                result = await self._profitability_analysis(data)
            elif action == "financial_risk":
                result = await self._financial_risk(data, task)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("FinanceManagerAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _financial_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a comprehensive financial report.

        Expected data:
          - period: str  (e.g. "Q1 2025", "Week 12")
          - revenue_usd: float
          - cogs_usd: float  (cost of goods sold)
          - ad_spend_usd: float
          - operating_expenses_usd: float
          - refunds_usd: float
          - orders_count: int
        """
        period = data.get("period", "période courante")
        revenue = float(data.get("revenue_usd", 0.0))
        cogs = float(data.get("cogs_usd", 0.0))
        ad_spend = float(data.get("ad_spend_usd", 0.0))
        opex = float(data.get("operating_expenses_usd", 0.0))

        prompt = (
            f"Génère un rapport financier complet pour la période: {period}\n\n"
            f"Données financières:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Calcule: marge brute, marge nette, EBITDA, CAC, LTV si possible.\n"
            "Format JSON:\n"
            "{\n"
            '  "period": "...",\n'
            '  "revenue_usd": 0.0,\n'
            '  "gross_profit_usd": 0.0,\n'
            '  "gross_margin_pct": 0.0,\n'
            '  "operating_profit_usd": 0.0,\n'
            '  "net_margin_pct": 0.0,\n'
            '  "ebitda_usd": 0.0,\n'
            '  "total_costs_usd": 0.0,\n'
            '  "roas": 0.0,\n'
            '  "cac_usd": 0.0,\n'
            '  "financial_health": "EXCELLENT|GOOD|AVERAGE|POOR|CRITICAL",\n'
            '  "key_insights": ["..."],\n'
            '  "recommendations": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="FINANCIAL_REPORT",
            entity_type="finance",
            entity_id=None,
            description=f"Rapport financier — période: {period}, revenus: ${revenue:.2f}",
            new_data={"period": period, "revenue_usd": revenue, "health": result.get("financial_health")},
        )

        health = result.get("financial_health", "AVERAGE")
        if health in ("POOR", "CRITICAL"):
            await self.create_decision(
                task=None,
                decision_type="FINANCIAL_ALERT",
                title=f"Alerte financière: {health} — {period}",
                rationale="; ".join(result.get("key_insights", [])),
                data_used=data,
                risk_level=RiskLevel.HIGH.value if health == "POOR" else RiskLevel.CRITICAL.value,
                recommendation="; ".join(result.get("recommendations", [])),
                estimated_revenue_usd=revenue,
                requires_human_approval=True,
            )

        return result

    async def _budget_analysis(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Analyze budget vs actuals and propose reallocation.

        Expected data:
          - period: str
          - budget_plan: dict  {category: budget_usd}
          - actuals: dict  {category: actual_usd}
          - remaining_budget_usd: float  (optional)
        """
        period = data.get("period", "période")
        prompt = (
            f"Analyse les écarts budget vs réel pour: {period}\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "overall_variance_pct": 0.0,\n'
            '  "over_budget_categories": [{"category": "...", "variance_usd": 0.0, "variance_pct": 0.0}],\n'
            '  "under_budget_categories": [{"category": "...", "variance_usd": 0.0, "variance_pct": 0.0}],\n'
            '  "reallocation_proposals": [{"from": "...", "to": "...", "amount_usd": 0.0, "reason": "..."}],\n'
            '  "budget_health": "ON_TRACK|MINOR_ISSUES|MAJOR_ISSUES|CRITICAL",\n'
            '  "corrective_actions": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        # Budget reallocation proposals require human approval
        total_reallocation = sum(
            p.get("amount_usd", 0.0) for p in result.get("reallocation_proposals", [])
        )
        if total_reallocation > 0:
            await self.create_decision(
                task=task,
                decision_type="BUDGET_REALLOCATION",
                title=f"Réallocation budgétaire: ${total_reallocation:.2f}",
                rationale="; ".join(result.get("corrective_actions", [])),
                data_used=data,
                risk_level=RiskLevel.MEDIUM.value,
                recommendation=f"{len(result.get('reallocation_proposals', []))} réallocation(s) proposée(s)",
                estimated_cost_usd=total_reallocation,
                requires_human_approval=True,
            )

        return result

    async def _cash_flow_forecast(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a cash flow forecast.

        Expected data:
          - current_cash_usd: float
          - monthly_revenue_usd: float
          - monthly_costs_usd: float
          - pending_payables_usd: float  (optional)
          - pending_receivables_usd: float  (optional)
          - forecast_months: int
        """
        months = data.get("forecast_months", 3)
        prompt = (
            f"Génère une prévision de flux de trésorerie sur {months} mois.\n\n"
            f"Données actuelles:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "current_runway_months": 0.0,\n'
            '  "monthly_forecast": [\n'
            '    {"month": 1, "projected_revenue_usd": 0.0, "projected_costs_usd": 0.0, "net_cash_flow_usd": 0.0, "cumulative_cash_usd": 0.0}\n'
            '  ],\n'
            '  "cash_flow_risk": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "breakeven_month": 0,\n'
            '  "recommendations": ["..."],\n'
            '  "contingency_plan": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _profitability_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze profitability by product, channel, or market.

        Expected data:
          - analysis_type: str  (PRODUCT|CHANNEL|MARKET|CUSTOMER)
          - items: list[dict]  (each with name, revenue_usd, cost_usd, orders_count)
        """
        analysis_type = data.get("analysis_type", "PRODUCT")
        prompt = (
            f"Analyse la rentabilité par {analysis_type}.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "analysis_type": "...",\n'
            '  "ranking": [\n'
            '    {"name": "...", "revenue_usd": 0.0, "cost_usd": 0.0, "margin_pct": 0.0, "profit_usd": 0.0}\n'
            '  ],\n'
            '  "top_performers": ["..."],\n'
            '  "unprofitable_items": ["..."],\n'
            '  "pareto_analysis": "...",\n'
            '  "optimization_opportunities": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _financial_risk(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Assess financial risks to the business.

        Expected data:
          - revenue_concentration: dict  {source: pct}
          - debt_obligations_usd: float  (optional)
          - currency_exposure: dict  {currency: amount_usd}  (optional)
          - supplier_payment_terms_days: int  (optional)
          - customer_payment_terms_days: int  (optional)
        """
        prompt = (
            "Effectue une évaluation des risques financiers.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "overall_risk": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "concentration_risk": "...",\n'
            '  "liquidity_risk": "...",\n'
            '  "currency_risk": "...",\n'
            '  "identified_risks": [{"risk": "...", "impact": "HIGH|MEDIUM|LOW", "probability": "HIGH|MEDIUM|LOW", "mitigation": "..."}],\n'
            '  "risk_score": 0.0,\n'
            '  "recommended_actions": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        overall_risk = result.get("overall_risk", RiskLevel.MEDIUM.value)
        if overall_risk in ("HIGH", "CRITICAL"):
            await self.create_decision(
                task=task,
                decision_type="FINANCIAL_RISK_ALERT",
                title=f"Alerte risque financier: {overall_risk}",
                rationale="; ".join(result.get("recommended_actions", [])),
                data_used=data,
                risk_level=overall_risk,
                recommendation="; ".join(result.get("recommended_actions", [])),
                requires_human_approval=True,
            )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Manager Finance, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "FinanceManager",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "current_mrr_usd": 0.0,\n'
            '  "gross_margin_pct": 0.0,\n'
            '  "cash_runway_months": 0.0,\n'
            '  "financial_alerts": ["..."],\n'
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
