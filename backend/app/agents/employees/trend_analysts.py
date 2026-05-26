"""
Trend Analyst Employees: specialized agents for platform-specific trend monitoring.

Five concrete analyst classes, each inheriting BaseAgent:
  - AmazonTrendAnalyst
  - AliExpressTrendAnalyst
  - TikTokTrendAnalyst
  - GoogleTrendAnalyst
  - EbayTrendAnalyst

Each analyst specializes in surfacing trending products and categories
on its target platform and reporting findings to the ProductResearchManagerAgent.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Shared helpers mixin — avoids code duplication across analysts
# --------------------------------------------------------------------------- #

class _TrendAnalystMixin:
    """Common JSON parsing and execute scaffolding for all trend analysts."""

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


# --------------------------------------------------------------------------- #
# Amazon Trend Analyst
# --------------------------------------------------------------------------- #

class AmazonTrendAnalyst(_TrendAnalystMixin, BaseAgent):
    """Employee analyst specializing in Amazon marketplace trends."""

    SYSTEM_PROMPT = (
        "Tu es un analyste de tendances spécialisé sur Amazon pour la compagnie de dropshipping "
        "AI Dropship Company OS. "
        "Tu analyses les Best Sellers, les produits en montée, les nouvelles tendances par catégorie. "
        "Tu identifies les produits avec fort potentiel de vente, bonne marge et faible concurrence. "
        "Tu surveilles les avis clients, les évolutions de prix et les opportunités de niche. "
        "Tu rapportes des données précises et actionnables au Manager Recherche Produits."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_trends")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Amazon Trends: {action}",
            description=f"Analyse tendances Amazon — {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            result = await self._analyze_amazon_trends(data)
            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result
        except Exception as exc:
            logger.exception("AmazonTrendAnalyst.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_amazon_trends(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze Amazon marketplace trends.

        Expected data:
          - category: str  (optional, focus category)
          - bestseller_data: list[dict]  (optional, scraped BSR data)
          - date_range: str  (optional)
          - min_rating: float  (optional, default 4.0)
        """
        category = data.get("category", "toutes catégories")
        prompt = (
            f"Analyse les tendances Amazon pour: {category}\n\n"
            f"Données disponibles:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "platform": "amazon",\n'
            '  "trending_products": [\n'
            '    {\n'
            '      "name": "...",\n'
            '      "category": "...",\n'
            '      "bsr_rank": 0,\n'
            '      "avg_rating": 0.0,\n'
            '      "reviews_count": 0,\n'
            '      "estimated_monthly_sales": 0,\n'
            '      "avg_price_usd": 0.0,\n'
            '      "opportunity_score": 0,\n'
            '      "competition_level": "LOW|MEDIUM|HIGH"\n'
            '    }\n'
            '  ],\n'
            '  "trending_categories": [{"category": "...", "growth_trend": "UP|STABLE|DOWN", "opportunity": "HIGH|MEDIUM|LOW"}],\n'
            '  "key_insights": ["..."],\n'
            '  "recommended_products": ["..."],\n'
            '  "market_observations": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="AMAZON_TREND_ANALYSIS",
            entity_type="trend_report",
            entity_id=None,
            description=f"Analyse tendances Amazon — catégorie: {category}",
            new_data={"category": category, "products_identified": len(result.get("trending_products", []))},
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant qu'analyste tendances Amazon, génère un rapport de statut. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "AmazonTrendAnalyst",\n'
            '  "platform": "amazon",\n'
            '  "status": "operational",\n'
            '  "last_analysis_summary": "...",\n'
            '  "top_opportunities": ["..."]\n'
            "}"
        )
        response = await self.think(prompt)
        return self._parse_json_response(response)


# --------------------------------------------------------------------------- #
# AliExpress Trend Analyst
# --------------------------------------------------------------------------- #

class AliExpressTrendAnalyst(_TrendAnalystMixin, BaseAgent):
    """Employee analyst specializing in AliExpress sourcing trends."""

    SYSTEM_PROMPT = (
        "Tu es un analyste de tendances spécialisé sur AliExpress pour la compagnie de dropshipping "
        "AI Dropship Company OS. "
        "Tu identifies les produits populaires sur AliExpress avec fort potentiel dropshipping. "
        "Tu analyses: nombre de commandes, évaluations fournisseurs, délais de livraison, prix. "
        "Tu repères les produits en montée avant qu'ils deviennent saturés. "
        "Tu évalues la fiabilité des fournisseurs et le potentiel de marge pour le dropshipping."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_trends")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"AliExpress Trends: {action}",
            description=f"Analyse tendances AliExpress — {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            result = await self._analyze_aliexpress_trends(data)
            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result
        except Exception as exc:
            logger.exception("AliExpressTrendAnalyst.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_aliexpress_trends(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze AliExpress product trends for dropshipping opportunities.

        Expected data:
          - category: str  (optional)
          - max_price_usd: float  (optional, filter for low-cost sourcing)
          - min_orders: int  (optional, minimum order count threshold)
          - product_data: list[dict]  (optional, scraped data)
        """
        category = data.get("category", "toutes catégories")
        max_price = data.get("max_price_usd", 20.0)
        prompt = (
            f"Analyse les tendances AliExpress pour le dropshipping — catégorie: {category}, "
            f"prix max sourcing: ${max_price}\n\n"
            f"Données disponibles:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "platform": "aliexpress",\n'
            '  "trending_products": [\n'
            '    {\n'
            '      "name": "...",\n'
            '      "category": "...",\n'
            '      "sourcing_price_usd": 0.0,\n'
            '      "suggested_sell_price_usd": 0.0,\n'
            '      "margin_pct": 0.0,\n'
            '      "orders_count": 0,\n'
            '      "supplier_rating": 0.0,\n'
            '      "shipping_days_estimate": 0,\n'
            '      "dropship_potential": "EXCELLENT|GOOD|AVERAGE|POOR"\n'
            '    }\n'
            '  ],\n'
            '  "emerging_niches": ["..."],\n'
            '  "supplier_quality_notes": ["..."],\n'
            '  "key_insights": ["..."],\n'
            '  "recommended_products": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="ALIEXPRESS_TREND_ANALYSIS",
            entity_type="trend_report",
            entity_id=None,
            description=f"Analyse tendances AliExpress — catégorie: {category}",
            new_data={"category": category, "products_identified": len(result.get("trending_products", []))},
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant qu'analyste tendances AliExpress, génère un rapport de statut. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "AliExpressTrendAnalyst",\n'
            '  "platform": "aliexpress",\n'
            '  "status": "operational",\n'
            '  "last_analysis_summary": "...",\n'
            '  "top_opportunities": ["..."]\n'
            "}"
        )
        response = await self.think(prompt)
        return self._parse_json_response(response)


# --------------------------------------------------------------------------- #
# TikTok Trend Analyst
# --------------------------------------------------------------------------- #

class TikTokTrendAnalyst(_TrendAnalystMixin, BaseAgent):
    """Employee analyst specializing in TikTok viral product trends."""

    SYSTEM_PROMPT = (
        "Tu es un analyste de tendances spécialisé sur TikTok pour la compagnie de dropshipping "
        "AI Dropship Company OS. "
        "Tu surveilles les produits viraux sur TikTok, TikTok Shop et les hashtags tendance. "
        "Tu analyses: vues, engagement, vitesse de viralité, produits mentionnés par les créateurs. "
        "Tu identifies les produits avant leur pic de popularité pour capturer la vague. "
        "Tu évalues le potentiel de contenu UGC et les opportunités de partenariat créateurs."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_trends")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"TikTok Trends: {action}",
            description=f"Analyse tendances TikTok — {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            result = await self._analyze_tiktok_trends(data)
            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result
        except Exception as exc:
            logger.exception("TikTokTrendAnalyst.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_tiktok_trends(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze TikTok viral trends and product opportunities.

        Expected data:
          - trending_hashtags: list[str]  (optional)
          - viral_videos_data: list[dict]  (optional)
          - category: str  (optional)
          - target_demographics: list[str]  (optional)
        """
        category = data.get("category", "général")
        prompt = (
            f"Analyse les tendances virales TikTok pour: {category}\n\n"
            f"Données disponibles:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "platform": "tiktok",\n'
            '  "viral_products": [\n'
            '    {\n'
            '      "name": "...",\n'
            '      "category": "...",\n'
            '      "viral_score": 0,\n'
            '      "avg_views": 0,\n'
            '      "trend_velocity": "EXPLODING|RISING|STABLE|DECLINING",\n'
            '      "target_demographic": "...",\n'
            '      "ugc_potential": "HIGH|MEDIUM|LOW",\n'
            '      "peak_predicted_in_days": 0\n'
            '    }\n'
            '  ],\n'
            '  "trending_hashtags": [{"hashtag": "...", "views_millions": 0.0}],\n'
            '  "content_trends": ["..."],\n'
            '  "creator_partnership_opportunities": ["..."],\n'
            '  "key_insights": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="TIKTOK_TREND_ANALYSIS",
            entity_type="trend_report",
            entity_id=None,
            description=f"Analyse tendances TikTok — catégorie: {category}",
            new_data={"category": category, "viral_products_found": len(result.get("viral_products", []))},
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant qu'analyste tendances TikTok, génère un rapport de statut. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "TikTokTrendAnalyst",\n'
            '  "platform": "tiktok",\n'
            '  "status": "operational",\n'
            '  "last_analysis_summary": "...",\n'
            '  "top_viral_opportunities": ["..."]\n'
            "}"
        )
        response = await self.think(prompt)
        return self._parse_json_response(response)


# --------------------------------------------------------------------------- #
# Google Trend Analyst
# --------------------------------------------------------------------------- #

class GoogleTrendAnalyst(_TrendAnalystMixin, BaseAgent):
    """Employee analyst specializing in Google search trends and SEO opportunities."""

    SYSTEM_PROMPT = (
        "Tu es un analyste de tendances spécialisé sur Google pour la compagnie de dropshipping "
        "AI Dropship Company OS. "
        "Tu analyses les tendances de recherche Google, Google Shopping et Google Trends. "
        "Tu identifies les intentions d'achat, les mots-clés à fort potentiel, et les opportunités SEO. "
        "Tu surveilles les volumes de recherche, la saisonnalité, et la concurrence sur les keywords. "
        "Tu identifies les niches sous-exploitées avec fort potentiel commercial."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_trends")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Google Trends: {action}",
            description=f"Analyse tendances Google — {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            result = await self._analyze_google_trends(data)
            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result
        except Exception as exc:
            logger.exception("GoogleTrendAnalyst.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_google_trends(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze Google search trends for product and SEO opportunities.

        Expected data:
          - keywords: list[str]  (optional, seed keywords)
          - category: str  (optional)
          - geo: str  (optional, e.g. "US", "GB")
          - timeframe: str  (optional, e.g. "today 3-m")
          - search_volume_data: dict  (optional)
        """
        category = data.get("category", "e-commerce")
        geo = data.get("geo", "US")
        prompt = (
            f"Analyse les tendances de recherche Google pour: {category} — marché: {geo}\n\n"
            f"Données disponibles:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "platform": "google",\n'
            '  "trending_searches": [\n'
            '    {\n'
            '      "keyword": "...",\n'
            '      "monthly_search_volume": 0,\n'
            '      "trend_direction": "UP|STABLE|DOWN",\n'
            '      "competition": "LOW|MEDIUM|HIGH",\n'
            '      "cpc_usd": 0.0,\n'
            '      "commercial_intent": "HIGH|MEDIUM|LOW",\n'
            '      "seasonal_peaks": ["..."]\n'
            '    }\n'
            '  ],\n'
            '  "niche_opportunities": [{"niche": "...", "potential": "HIGH|MEDIUM|LOW", "reason": "..."}],\n'
            '  "seo_opportunities": ["..."],\n'
            '  "seasonal_insights": "...",\n'
            '  "key_insights": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="GOOGLE_TREND_ANALYSIS",
            entity_type="trend_report",
            entity_id=None,
            description=f"Analyse tendances Google — catégorie: {category}, marché: {geo}",
            new_data={"category": category, "geo": geo, "keywords_analyzed": len(result.get("trending_searches", []))},
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant qu'analyste tendances Google, génère un rapport de statut. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "GoogleTrendAnalyst",\n'
            '  "platform": "google",\n'
            '  "status": "operational",\n'
            '  "last_analysis_summary": "...",\n'
            '  "top_seo_opportunities": ["..."]\n'
            "}"
        )
        response = await self.think(prompt)
        return self._parse_json_response(response)


# --------------------------------------------------------------------------- #
# eBay Trend Analyst
# --------------------------------------------------------------------------- #

class EbayTrendAnalyst(_TrendAnalystMixin, BaseAgent):
    """Employee analyst specializing in eBay marketplace trends."""

    SYSTEM_PROMPT = (
        "Tu es un analyste de tendances spécialisé sur eBay pour la compagnie de dropshipping "
        "AI Dropship Company OS. "
        "Tu analyses les tendances eBay: enchères populaires, Buy It Now, catégories en croissance. "
        "Tu identifies les produits avec fort volume de ventes, prix compétitifs et faible concurrence. "
        "Tu surveilles les Sold Listings pour valider la demande réelle. "
        "Tu identifies les opportunités d'arbitrage et les niches sous-servies sur eBay."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "analyze_trends")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"eBay Trends: {action}",
            description=f"Analyse tendances eBay — {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            result = await self._analyze_ebay_trends(data)
            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result
        except Exception as exc:
            logger.exception("EbayTrendAnalyst.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _analyze_ebay_trends(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze eBay marketplace trends for dropshipping opportunities.

        Expected data:
          - category: str  (optional)
          - sold_listings_data: list[dict]  (optional)
          - active_listings_count: int  (optional)
          - avg_sell_through_rate: float  (optional)
        """
        category = data.get("category", "toutes catégories")
        prompt = (
            f"Analyse les tendances eBay pour: {category}\n\n"
            f"Données disponibles:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "platform": "ebay",\n'
            '  "trending_products": [\n'
            '    {\n'
            '      "name": "...",\n'
            '      "category": "...",\n'
            '      "avg_sold_price_usd": 0.0,\n'
            '      "sell_through_rate_pct": 0.0,\n'
            '      "active_listings": 0,\n'
            '      "sold_last_30_days": 0,\n'
            '      "competition_level": "LOW|MEDIUM|HIGH",\n'
            '      "dropship_opportunity": "EXCELLENT|GOOD|AVERAGE|POOR"\n'
            '    }\n'
            '  ],\n'
            '  "hot_categories": [{"category": "...", "growth_pct": 0.0}],\n'
            '  "arbitrage_opportunities": [{"product": "...", "buy_price_usd": 0.0, "sell_price_usd": 0.0}],\n'
            '  "key_insights": ["..."],\n'
            '  "recommended_products": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="EBAY_TREND_ANALYSIS",
            entity_type="trend_report",
            entity_id=None,
            description=f"Analyse tendances eBay — catégorie: {category}",
            new_data={"category": category, "products_identified": len(result.get("trending_products", []))},
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant qu'analyste tendances eBay, génère un rapport de statut. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "EbayTrendAnalyst",\n'
            '  "platform": "ebay",\n'
            '  "status": "operational",\n'
            '  "last_analysis_summary": "...",\n'
            '  "top_opportunities": ["..."]\n'
            "}"
        )
        response = await self.think(prompt)
        return self._parse_json_response(response)
