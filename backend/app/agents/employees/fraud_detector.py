"""
FraudDetectorAgent: detects fraudulent orders, chargebacks and suspicious activity.

Responsibilities:
  - Analyze orders for fraud signals (address mismatch, velocity, unusual patterns)
  - Score transactions by risk level
  - Flag suspicious orders for human review
  - Monitor chargeback rates and patterns
  - Maintain fraud rules and thresholds
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class FraudDetectorAgent(BaseAgent):
    """Employee agent specializing in fraud detection and prevention."""

    SYSTEM_PROMPT = (
        "Tu es un Détecteur de Fraude expert de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu analyses les commandes et transactions pour détecter les fraudes potentielles. "
        "Tu évalues: correspondance adresse/IP, vélocité de commandes, valeurs anormales, "
        "comportements suspects, chargebacks répétés, cartes volées. "
        "Tu assignes un score de risque (0-100) à chaque transaction. "
        "RÈGLE ABSOLUE: En cas de doute sur une fraude, tu BLOQUES et ESCALADES. "
        "Tu ne peux jamais autoriser une transaction frauduleuse même sous pression. "
        "Tu documentes tous les signaux d'alerte avec des preuves et des données."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_order")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Fraud Detection: {action}",
            description=f"Détection fraude — action: {action}",
            input_data=task_input,
            priority=TaskPriority.CRITICAL.value,  # Fraud detection is always critical priority
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "analyze_order":
                result = await self._analyze_order(data, task)
            elif action == "batch_screening":
                result = await self._batch_screening(data, task)
            elif action == "chargeback_analysis":
                result = await self._chargeback_analysis(data, task)
            elif action == "customer_risk_profile":
                result = await self._customer_risk_profile(data)
            elif action == "fraud_report":
                result = await self._fraud_report(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("FraudDetectorAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_order(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Analyze a single order for fraud signals.

        Expected data:
          - order_id: str
          - customer_id: str
          - order_value_usd: float
          - payment_method: str
          - billing_address: dict  (country, zip, city)
          - shipping_address: dict
          - ip_address: str  (optional)
          - ip_country: str  (optional)
          - customer_email: str
          - is_first_order: bool
          - device_fingerprint: str  (optional)
          - previous_orders_count: int  (optional)
          - previous_chargebacks: int  (optional)
        """
        order_id = data.get("order_id", "N/A")
        order_value = float(data.get("order_value_usd", 0.0))
        prompt = (
            f"Analyse la commande #{order_id} (valeur: ${order_value:.2f}) pour détecter les fraudes.\n\n"
            f"Données de la commande:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Évalue tous les signaux d'alerte:\n"
            "- Correspondance adresses facturation/livraison/IP\n"
            "- Vélocité (commandes multiples en peu de temps)\n"
            "- Valeur inhabituelle\n"
            "- Historique client\n"
            "- Signaux de chargeback\n\n"
            "Format JSON:\n"
            "{\n"
            '  "order_id": "...",\n'
            '  "fraud_score": 0,\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "decision": "APPROVE|REVIEW|BLOCK",\n'
            '  "fraud_signals": [\n'
            '    {"signal": "...", "severity": "HIGH|MEDIUM|LOW", "weight": 0}\n'
            '  ],\n'
            '  "address_match": true,\n'
            '  "geo_match": true,\n'
            '  "velocity_alert": false,\n'
            '  "rationale": "...",\n'
            '  "recommended_action": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        fraud_score = int(result.get("fraud_score", 0))
        risk_level = result.get("risk_level", RiskLevel.LOW.value)
        decision = result.get("decision", "REVIEW")

        # Always log fraud analysis
        await self.log_action(
            action="FRAUD_ANALYSIS",
            entity_type="order",
            entity_id=None,
            description=f"Analyse fraude commande #{order_id} — score: {fraud_score}, décision: {decision}",
            new_data={"order_id": order_id, "fraud_score": fraud_score, "decision": decision, "risk_level": risk_level},
        )

        # Create decision for high-risk or blocked orders
        if decision in ("REVIEW", "BLOCK") or risk_level in ("HIGH", "CRITICAL"):
            await self.create_decision(
                task=task,
                decision_type="FRAUD_DETECTION",
                title=f"Fraude potentielle — commande #{order_id} (score: {fraud_score})",
                rationale=result.get("rationale", ""),
                data_used={
                    "order_id": order_id,
                    "fraud_score": fraud_score,
                    "signals": [s.get("signal") for s in result.get("fraud_signals", [])],
                },
                risk_level=risk_level,
                recommendation=decision,
                estimated_cost_usd=order_value if decision == "BLOCK" else None,
                requires_human_approval=decision in ("REVIEW", "BLOCK"),
            )

        return result

    async def _batch_screening(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Screen a batch of orders for fraud patterns.

        Expected data:
          - orders: list[dict]  (each with order_id, value_usd, customer_id, payment_method,
                                  billing_country, shipping_country)
          - threshold_score: int  (default 70, flag orders above this)
        """
        orders = data.get("orders", [])
        threshold = data.get("threshold_score", 70)
        prompt = (
            f"Effectue un screening anti-fraude sur {len(orders)} commandes (seuil: {threshold}/100).\n\n"
            f"Commandes:\n{json.dumps(orders, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "total_screened": 0,\n'
            '  "approved": 0,\n'
            '  "flagged_for_review": 0,\n'
            '  "blocked": 0,\n'
            '  "flagged_orders": [\n'
            '    {"order_id": "...", "fraud_score": 0, "decision": "REVIEW|BLOCK", "top_signal": "..."}\n'
            '  ],\n'
            '  "patterns_detected": ["..."],\n'
            '  "total_blocked_value_usd": 0.0,\n'
            '  "fraud_rate_pct": 0.0\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        blocked_value = float(result.get("total_blocked_value_usd", 0.0))
        flagged_count = result.get("flagged_for_review", 0) + result.get("blocked", 0)

        if flagged_count > 0:
            await self.create_decision(
                task=task,
                decision_type="BATCH_FRAUD_DETECTION",
                title=f"Fraude batch: {flagged_count} commande(s) suspecte(s) sur {len(orders)}",
                rationale=f"Patterns détectés: {', '.join(result.get('patterns_detected', []))}",
                data_used={"total_screened": len(orders), "flagged": flagged_count},
                risk_level=RiskLevel.HIGH.value if blocked_value > 500 else RiskLevel.MEDIUM.value,
                recommendation=f"Réviser {flagged_count} commande(s) — valeur bloquée: ${blocked_value:.2f}",
                estimated_cost_usd=blocked_value if blocked_value > 0 else None,
                requires_human_approval=flagged_count > 0,
            )

        return result

    async def _chargeback_analysis(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Analyze chargeback patterns to identify systemic fraud or process issues.

        Expected data:
          - period_days: int
          - chargebacks: list[dict]  (order_id, amount_usd, reason, customer_id, date)
          - total_transactions: int
          - total_revenue_usd: float
        """
        chargebacks = data.get("chargebacks", [])
        total_cb_value = sum(cb.get("amount_usd", 0.0) for cb in chargebacks)
        total_revenue = float(data.get("total_revenue_usd", 1.0))
        cb_rate = (total_cb_value / total_revenue * 100) if total_revenue > 0 else 0

        prompt = (
            f"Analyse les chargebacks: {len(chargebacks)} chargebacks, "
            f"valeur totale: ${total_cb_value:.2f}, taux: {cb_rate:.2f}%\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "total_chargebacks": 0,\n'
            '  "total_chargeback_value_usd": 0.0,\n'
            '  "chargeback_rate_pct": 0.0,\n'
            '  "platform_risk": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "top_reasons": [{"reason": "...", "count": 0, "value_usd": 0.0}],\n'
            '  "fraudulent_patterns": ["..."],\n'
            '  "process_issues": ["..."],\n'
            '  "recommended_actions": ["..."],\n'
            '  "threshold_alert": false\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        # Alert if chargeback rate is high (>1% is payment processor warning threshold)
        if cb_rate > 1.0 or result.get("threshold_alert", False):
            await self.create_decision(
                task=task,
                decision_type="CHARGEBACK_ALERT",
                title=f"Alerte chargebacks: {cb_rate:.2f}% — risque processeur paiement",
                rationale=f"Taux de chargeback: {cb_rate:.2f}% (seuil: 1%). Valeur totale: ${total_cb_value:.2f}",
                data_used={"chargeback_rate_pct": cb_rate, "total_value_usd": total_cb_value},
                risk_level=RiskLevel.CRITICAL.value if cb_rate > 2.0 else RiskLevel.HIGH.value,
                recommendation="; ".join(result.get("recommended_actions", [])),
                estimated_cost_usd=total_cb_value,
                requires_human_approval=True,
            )

        return result

    async def _customer_risk_profile(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Build or update a customer risk profile.

        Expected data:
          - customer_id: str
          - order_history: list[dict]  (order_id, value_usd, status, date)
          - chargeback_history: list[dict]  (optional)
          - dispute_history: list[dict]  (optional)
          - account_age_days: int  (optional)
          - email_domain: str  (optional)
        """
        customer_id = data.get("customer_id", "N/A")
        prompt = (
            f"Crée un profil de risque pour le client: {customer_id}\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "customer_id": "...",\n'
            '  "risk_score": 0,\n'
            '  "risk_category": "TRUSTED|STANDARD|ELEVATED|HIGH_RISK|BLOCKED",\n'
            '  "chargeback_rate_pct": 0.0,\n'
            '  "lifetime_value_usd": 0.0,\n'
            '  "risk_factors": ["..."],\n'
            '  "positive_factors": ["..."],\n'
            '  "recommended_limits": {"max_order_usd": 0.0, "requires_review_above_usd": 0.0},\n'
            '  "notes": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        risk_category = result.get("risk_category", "STANDARD")
        await self.log_action(
            action="CUSTOMER_RISK_PROFILE",
            entity_type="customer",
            entity_id=None,
            description=f"Profil risque client {customer_id}: {risk_category} (score: {result.get('risk_score')})",
            new_data={"customer_id": customer_id, "risk_category": risk_category, "risk_score": result.get("risk_score")},
        )

        return result

    async def _fraud_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a comprehensive fraud summary report.

        Expected data:
          - period_days: int
          - fraud_stats: dict  (blocked_orders, blocked_value_usd, fraud_rate_pct)
          - top_fraud_types: list[str]  (optional)
          - rule_performance: dict  (optional)
        """
        period = data.get("period_days", 7)
        prompt = (
            f"Génère un rapport de synthèse anti-fraude pour les {period} derniers jours.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            f'  "period_days": {period},\n'
            '  "total_fraud_prevented_usd": 0.0,\n'
            '  "fraud_rate_pct": 0.0,\n'
            '  "top_fraud_vectors": [{"vector": "...", "count": 0, "value_usd": 0.0}],\n'
            '  "rule_effectiveness": [{"rule": "...", "catches": 0, "false_positives": 0}],\n'
            '  "emerging_threats": ["..."],\n'
            '  "recommended_rule_updates": ["..."],\n'
            '  "fraud_trend": "IMPROVING|STABLE|WORSENING"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="FRAUD_REPORT",
            entity_type="fraud_report",
            entity_id=None,
            description=f"Rapport fraude {period}j — prévenu: ${result.get('total_fraud_prevented_usd', 0):.2f}",
            new_data={
                "period_days": period,
                "fraud_rate_pct": result.get("fraud_rate_pct"),
                "trend": result.get("fraud_trend"),
            },
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Détecteur de Fraude, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "FraudDetector",\n'
            '  "status": "operational",\n'
            '  "orders_screened_today": 0,\n'
            '  "fraud_blocked_today": 0,\n'
            '  "current_fraud_rate_pct": 0.0,\n'
            '  "active_alerts": ["..."],\n'
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
