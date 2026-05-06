"""
MarketingManagerAgent: manages advertising campaigns and brand presence.

Responsibilities:
  - Plan and analyze ad campaigns (Facebook, TikTok, Google Ads)
  - Optimize ROAS, CPA, CTR
  - Content strategy and product listing optimization
  - Budget allocation across channels
  - Ad spend requires human approval
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.core.config import settings
from app.models.agent import RiskLevel, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class MarketingManagerAgent(BaseAgent):
    """Manager responsible for marketing campaigns and growth."""

    SYSTEM_PROMPT = (
        "Tu es le Manager Marketing de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu planifies et optimises les campagnes publicitaires sur Facebook Ads, TikTok Ads et Google Ads. "
        "Tu analyses les métriques clés: ROAS, CPA, CTR, taux de conversion, CAC. "
        "Tu gères le budget marketing, optimises les créatifs et les audiences. "
        "Tu développes la stratégie de contenu et optimises les listings produits. "
        "Tout budget publicitaire > $0 nécessite une validation humaine. "
        "Tu maximises le retour sur investissement publicitaire tout en maintenant des marges saines."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_campaigns")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Marketing: {action}",
            description=f"Marketing — action: {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "analyze_campaigns":
                result = await self._analyze_campaigns(data)
            elif action == "optimize_budget":
                result = await self._optimize_budget(data, task)
            elif action == "content_strategy":
                result = await self._content_strategy(data)
            elif action == "audience_analysis":
                result = await self._audience_analysis(data)
            elif action == "campaign_proposal":
                result = await self._campaign_proposal(data, task)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("MarketingManagerAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_campaigns(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze active marketing campaign performance.

        Expected data:
          - campaigns: list[dict]  (name, platform, spend_usd, impressions, clicks,
                                    conversions, revenue_usd, period_days)
        """
        prompt = (
            "Analyse les performances des campagnes marketing suivantes.\n\n"
            f"Campagnes:\n{json.dumps(data.get('campaigns', []), indent=2, ensure_ascii=False)}\n\n"
            "Calcule pour chaque campagne: ROAS, CPA, CTR, taux de conversion.\n"
            "Format JSON:\n"
            "{\n"
            '  "campaign_analysis": [\n'
            '    {\n'
            '      "name": "...",\n'
            '      "platform": "...",\n'
            '      "roas": 0.0,\n'
            '      "cpa_usd": 0.0,\n'
            '      "ctr_pct": 0.0,\n'
            '      "conversion_rate_pct": 0.0,\n'
            '      "performance": "EXCELLENT|GOOD|AVERAGE|POOR",\n'
            '      "recommendation": "SCALE|MAINTAIN|OPTIMIZE|PAUSE"\n'
            '    }\n'
            '  ],\n'
            '  "total_spend_usd": 0.0,\n'
            '  "total_revenue_usd": 0.0,\n'
            '  "blended_roas": 0.0,\n'
            '  "top_performer": "campaign_name",\n'
            '  "worst_performer": "campaign_name",\n'
            '  "action_items": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _optimize_budget(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Propose budget reallocation across campaigns/channels.

        Expected data:
          - total_budget_usd: float
          - current_allocation: dict  {channel: amount_usd}
          - performance_data: dict  {channel: {roas, cpa, conversion_rate}}
        """
        total = data.get("total_budget_usd", 0.0)
        prompt = (
            f"Optimise l'allocation du budget marketing de ${total:.2f} entre les canaux.\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "recommended_allocation": {"channel": 0.0},\n'
            '  "changes": [{"channel": "...", "old_budget_usd": 0.0, "new_budget_usd": 0.0, "reason": "..."}],\n'
            '  "expected_roas_improvement": "...",\n'
            '  "total_budget_usd": 0.0,\n'
            '  "rationale": "...",\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        # Budget changes require human approval
        if total > settings.MAX_AUTO_SPEND_USD:
            await self.create_decision(
                task=task,
                decision_type="BUDGET_ALLOCATION",
                title=f"Optimisation budget marketing: ${total:.2f}",
                rationale=result.get("rationale", ""),
                data_used=data,
                risk_level=result.get("risk_level", RiskLevel.MEDIUM.value),
                recommendation=f"Réallocation proposée: {result.get('recommended_allocation', {})}",
                estimated_cost_usd=total,
                requires_human_approval=True,
            )

        return result

    async def _content_strategy(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Develop content and creative strategy for products.

        Expected data:
          - products: list[dict]  (name, category, target_audience, price_usd)
          - platforms: list[str]  (facebook|tiktok|instagram|google)
          - budget_usd: float  (optional)
        """
        platforms = data.get("platforms", ["facebook", "tiktok"])
        prompt = (
            f"Développe une stratégie de contenu pour les plateformes: {', '.join(platforms)}\n\n"
            f"Données produits et contexte:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "content_pillars": ["..."],\n'
            '  "platform_strategies": {\n'
            '    "platform_name": {\n'
            '      "content_types": ["..."],\n'
            '      "posting_frequency": "...",\n'
            '      "key_messages": ["..."],\n'
            '      "cta": "..."\n'
            '    }\n'
            '  },\n'
            '  "creative_recommendations": ["..."],\n'
            '  "seasonal_calendar": [{"month": "...", "theme": "...", "promotions": ["..."]}],\n'
            '  "ugc_strategy": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _audience_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze and define target audiences for products.

        Expected data:
          - product_category: str
          - current_customer_data: dict  (optional: age_range, gender_split, top_locations)
          - competitor_audiences: list[str]  (optional)
        """
        category = data.get("product_category", "produit")
        prompt = (
            f"Analyse et définit les audiences cibles pour: {category}\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "primary_audience": {\n'
            '    "description": "...",\n'
            '    "age_range": "...",\n'
            '    "interests": ["..."],\n'
            '    "pain_points": ["..."],\n'
            '    "estimated_size": "..."\n'
            '  },\n'
            '  "secondary_audiences": [{"description": "...", "potential": "HIGH|MEDIUM|LOW"}],\n'
            '  "lookalike_strategy": "...",\n'
            '  "targeting_recommendations": ["..."],\n'
            '  "excluded_audiences": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _campaign_proposal(self, data: dict[str, Any], task: Any) -> dict[str, Any]:
        """
        Create a new marketing campaign proposal.

        Expected data:
          - product_name: str
          - objective: str  (AWARENESS|TRAFFIC|CONVERSIONS|RETENTION)
          - budget_usd: float
          - duration_days: int
          - platform: str
        """
        product = data.get("product_name", "produit")
        budget = float(data.get("budget_usd", 0.0))
        platform = data.get("platform", "facebook")
        prompt = (
            f"Crée une proposition de campagne marketing pour: {product} sur {platform}\n\n"
            f"Paramètres:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "campaign_name": "...",\n'
            '  "objective": "...",\n'
            '  "platform": "...",\n'
            '  "budget_usd": 0.0,\n'
            '  "duration_days": 0,\n'
            '  "target_audience": "...",\n'
            '  "ad_formats": ["..."],\n'
            '  "key_messages": ["..."],\n'
            '  "kpis": {"roas_target": 0.0, "cpa_target_usd": 0.0, "impressions_target": 0},\n'
            '  "creative_brief": "...",\n'
            '  "expected_results": "...",\n'
            '  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        # Campaign budget requires human approval
        await self.create_decision(
            task=task,
            decision_type="CAMPAIGN_LAUNCH",
            title=f"Lancement campagne: {result.get('campaign_name', product)}",
            rationale=result.get("creative_brief", ""),
            data_used=data,
            risk_level=result.get("risk_level", RiskLevel.MEDIUM.value),
            recommendation=result.get("expected_results", ""),
            estimated_cost_usd=budget,
            requires_human_approval=budget > settings.MAX_AUTO_SPEND_USD,
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Manager Marketing, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "MarketingManager",\n'
            '  "status": "operational|degraded|offline",\n'
            '  "active_campaigns": 0,\n'
            '  "total_spend_this_week_usd": 0.0,\n'
            '  "blended_roas": 0.0,\n'
            '  "top_performing_channel": "...",\n'
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
