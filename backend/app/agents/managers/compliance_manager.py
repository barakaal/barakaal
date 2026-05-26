"""
ComplianceManagerAgent: manages legal, regulatory and platform compliance.

Responsibilities:
  - Monitor compliance with platform policies (Amazon, eBay, Shopify)
  - Identify legal and regulatory risks
  - Review products for compliance issues (trademarks, prohibited items)
  - Monitor data privacy compliance (GDPR, CCPA)
  - Escalate all compliance risks immediately
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class ComplianceManagerAgent(BaseAgent):
    """Manager responsible for legal and regulatory compliance."""

    SYSTEM_PROMPT = (
        "Tu es le Manager Conformité et Juridique de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu surveilles la conformité légale et réglementaire de toutes les opérations. "
        "Tu vérifie: politiques des plateformes (Amazon, eBay, Shopify, TikTok Shop), "
        "droits de propriété intellectuelle, réglementations d'import/export, "
        "protection des données (RGPD, CCPA), et droit de la consommation. "
        "RÈGLE ABSOLUE: En cas de doute légal ou de conformité, tu dois REFUSER et ESCALADER. "
        "Tu ne peux jamais approuver une action dont la légalité est incertaine. "
        "Tu documentes tous les risques identifiés avec leur niveau de criticité et les actions requises."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "compliance_check")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Compliance: {action}",
            description=f"Conformité — action: {action}",
            input_data=task_input,
            priority=TaskPriority.HIGH.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "compliance_check":
                result = await self._compliance_check(data, task)
            elif action == "product_review":
                result = await self._product_review(data, task)
            elif action == "platform_policy_audit":
                result = await self._platform_policy_audit(data, task)
            elif action == "data_privacy_check":
                result = await self._data_privacy_check(data, task)
            elif action == "risk_register":
                result = await self._risk_register(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("ComplianceManagerAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _compliance_check(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        General compliance check for a business activity.

        Expected data:
          - activity_type: str  (e.g. "product_listing", "ad_campaign", "data_collection")
          - description: str
          - markets: list[str]  (e.g. ["US", "EU", "UK"])
          - details: dict  (activity-specific details)
        """
        activity = data.get("activity_type", "activité")
        markets = data.get("markets", ["US"])
        prompt = (
            f"Effectue une vérification de conformité pour: {activity} sur les marchés: {', '.join(markets)}\n\n"
            f"Détails:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "compliance_status": "COMPLIANT|CONDITIONAL|NON_COMPLIANT|BLOCKED",\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "issues_found": [{"issue": "...", "severity": "HIGH|MEDIUM|LOW", "regulation": "...", "action": "..."}],\n'
            '  "conditions": ["..."],\n'
            '  "recommendation": "APPROVE|MODIFY|REJECT|ESCALATE",\n'
            '  "legal_disclaimer": "...",\n'
            '  "requires_legal_review": true\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        compliance_status = result.get("compliance_status", "CONDITIONAL")
        risk_level = result.get("risk_level", RiskLevel.MEDIUM.value)

        # Always create a decision for compliance checks
        requires_approval = (
            compliance_status in ("NON_COMPLIANT", "BLOCKED")
            or risk_level in ("HIGH", "CRITICAL")
            or result.get("requires_legal_review", True)
        )

        await self.create_decision(
            task=task,
            decision_type="COMPLIANCE_CHECK",
            title=f"Conformité: {activity} — {compliance_status}",
            rationale=f"Vérification de conformité sur marchés: {', '.join(markets)}",
            data_used=data,
            risk_level=risk_level,
            recommendation=result.get("recommendation", "ESCALATE"),
            requires_human_approval=requires_approval,
        )

        return result

    async def _product_review(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Review a product for compliance issues (IP, platform rules, import/export).

        Expected data:
          - product_name: str
          - category: str
          - description: str
          - origin_country: str
          - target_markets: list[str]
          - images_description: str  (optional)
          - brand_claims: list[str]  (optional)
        """
        product = data.get("product_name", "produit")
        prompt = (
            f"Effectue une revue de conformité complète pour le produit: {product}\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Vérifie: droits de propriété intellectuelle, règles de plateformes, "
            "réglementations d'import, certifications requises, restrictions de vente.\n"
            "Format JSON:\n"
            "{\n"
            '  "product_name": "...",\n'
            '  "compliance_status": "APPROVED|CONDITIONAL|REJECTED|BLOCKED",\n'
            '  "ip_risk": "NONE|LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "platform_compliance": {"amazon": "OK|ISSUE", "ebay": "OK|ISSUE", "shopify": "OK|ISSUE"},\n'
            '  "import_restrictions": ["..."],\n'
            '  "required_certifications": ["..."],\n'
            '  "issues": [{"type": "...", "description": "...", "action": "..."}],\n'
            '  "conditions_to_list": ["..."],\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        compliance_status = result.get("compliance_status", "CONDITIONAL")
        risk_level = result.get("risk_level", RiskLevel.MEDIUM.value)

        if compliance_status in ("REJECTED", "BLOCKED") or risk_level in ("HIGH", "CRITICAL"):
            await self.create_decision(
                task=task,
                decision_type="PRODUCT_COMPLIANCE",
                title=f"Conformité produit: {product} — {compliance_status}",
                rationale="; ".join([i.get("description", "") for i in result.get("issues", [])]),
                data_used=data,
                risk_level=risk_level,
                recommendation=compliance_status,
                requires_human_approval=True,
            )

        return result

    async def _platform_policy_audit(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Audit compliance with specific platform policies.

        Expected data:
          - platform: str  (amazon|ebay|shopify|tiktok_shop|facebook)
          - audit_scope: list[str]  (e.g. ["listings", "ads", "returns_policy"])
          - current_practices: dict  (optional)
        """
        platform = data.get("platform", "marketplace")
        prompt = (
            f"Effectue un audit de conformité aux politiques de {platform}.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            f'  "platform": "{platform}",\n'
            '  "overall_compliance": "COMPLIANT|MINOR_ISSUES|MAJOR_ISSUES|CRITICAL",\n'
            '  "violations": [{"policy": "...", "description": "...", "severity": "HIGH|MEDIUM|LOW", "fix": "..."}],\n'
            '  "risk_of_suspension": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "compliance_score": 0.0,\n'
            '  "remediation_plan": [{"action": "...", "deadline_days": 0, "priority": "HIGH|MEDIUM|LOW"}]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        suspension_risk = result.get("risk_of_suspension", "LOW")
        if suspension_risk in ("HIGH", "CRITICAL"):
            await self.create_decision(
                task=task,
                decision_type="PLATFORM_COMPLIANCE_ALERT",
                title=f"Risque suspension {platform}: {suspension_risk}",
                rationale="; ".join([v.get("description", "") for v in result.get("violations", [])]),
                data_used=data,
                risk_level=RiskLevel.CRITICAL.value if suspension_risk == "CRITICAL" else RiskLevel.HIGH.value,
                recommendation="Action immédiate requise",
                requires_human_approval=True,
            )

        return result

    async def _data_privacy_check(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Check data collection and processing practices for privacy compliance.

        Expected data:
          - data_types_collected: list[str]  (e.g. ["email", "address", "payment"])
          - processing_purposes: list[str]
          - data_retention_days: int
          - third_party_sharing: list[str]  (optional)
          - markets: list[str]
        """
        markets = data.get("markets", ["US"])
        prompt = (
            f"Vérifie la conformité aux réglementations sur la protection des données pour: {', '.join(markets)}\n\n"
            f"Pratiques actuelles:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Vérifie: RGPD (EU), CCPA (California), PIPEDA (Canada) si applicable.\n"
            "Format JSON:\n"
            "{\n"
            '  "gdpr_compliant": true,\n'
            '  "ccpa_compliant": true,\n'
            '  "issues": [{"regulation": "...", "issue": "...", "severity": "HIGH|MEDIUM|LOW", "fix": "..."}],\n'
            '  "consent_requirements": ["..."],\n'
            '  "data_retention_recommendation_days": 0,\n'
            '  "dpo_required": false,\n'
            '  "privacy_policy_updates_needed": ["..."],\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        risk_level = result.get("risk_level", RiskLevel.MEDIUM.value)
        issues = result.get("issues", [])
        high_severity_issues = [i for i in issues if i.get("severity") == "HIGH"]

        if high_severity_issues or risk_level in ("HIGH", "CRITICAL"):
            await self.create_decision(
                task=task,
                decision_type="DATA_PRIVACY_COMPLIANCE",
                title=f"Alerte conformité données: {risk_level}",
                rationale="; ".join([i.get("issue", "") for i in high_severity_issues[:3]]),
                data_used=data,
                risk_level=risk_level,
                recommendation="Mettre en conformité immédiatement",
                requires_human_approval=True,
            )

        return result

    async def _risk_register(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Maintain and update the compliance risk register.

        Expected data:
          - business_activities: list[str]
          - current_risks: list[dict]  (optional, existing risk register entries)
          - recent_changes: list[str]  (optional, new activities or regulatory changes)
        """
        prompt = (
            "Génère ou mets à jour le registre des risques de conformité.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "risks": [\n'
            '    {\n'
            '      "risk_id": "R001",\n'
            '      "category": "LEGAL|PLATFORM|DATA_PRIVACY|IP|IMPORT_EXPORT",\n'
            '      "description": "...",\n'
            '      "likelihood": "HIGH|MEDIUM|LOW",\n'
            '      "impact": "CRITICAL|HIGH|MEDIUM|LOW",\n'
            '      "risk_score": 0.0,\n'
            '      "mitigation": "...",\n'
            '      "owner": "...",\n'
            '      "status": "OPEN|MITIGATED|CLOSED"\n'
            '    }\n'
            '  ],\n'
            '  "high_priority_risks": 0,\n'
            '  "overall_compliance_posture": "STRONG|ADEQUATE|WEAK|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="RISK_REGISTER_UPDATE",
            entity_type="compliance",
            entity_id=None,
            description=f"Registre risques — posture: {result.get('overall_compliance_posture')}",
            new_data={"high_priority_risks": result.get("high_priority_risks"), "posture": result.get("overall_compliance_posture")},
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Manager Conformité, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "ComplianceManager",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "open_compliance_issues": 0,\n'
            '  "high_risk_items": 0,\n'
            '  "platform_suspension_risks": [],\n'
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
