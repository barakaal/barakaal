"""
ProductWriterAgent: generates optimized product listings and descriptions.

Responsibilities:
  - Write SEO-optimized product titles and descriptions
  - Generate bullet points highlighting key features and benefits
  - Adapt content for different platforms (Amazon, eBay, Shopify, TikTok Shop)
  - Create A/B test variants for listings
  - Translate and localize content for international markets
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.agent import TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class ProductWriterAgent(BaseAgent):
    """Employee agent specializing in product content creation and optimization."""

    SYSTEM_PROMPT = (
        "Tu es un Rédacteur Produits expert de la compagnie de dropshipping AI Dropship Company OS. "
        "Tu crées des fiches produits optimisées pour le SEO et la conversion. "
        "Tu maîtrises la rédaction pour: Amazon (A9 algorithm), eBay, Shopify, TikTok Shop. "
        "Tu utilises des techniques de copywriting éprouvées: bénéfices > caractéristiques, "
        "AIDA (Attention, Intérêt, Désir, Action), social proof, urgency. "
        "Tu optimises les titres, descriptions, bullet points, et mots-clés backend. "
        "Tu adaptes le ton selon la plateforme et le public cible. "
        "Tu respectes les politiques de contenu de chaque plateforme."
    )

    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        action = task_input.get("action", "write_listing")
        data = task_input.get("data", {})

        task = await self.create_task(
            title=f"Product Writer: {action}",
            description=f"Rédaction produit — action: {action}",
            input_data=task_input,
            priority=TaskPriority.MEDIUM.value,
        )
        await self.update_task_status(task, TaskStatus.RUNNING.value)

        try:
            if action == "write_listing":
                result = await self._write_listing(data)
            elif action == "optimize_listing":
                result = await self._optimize_listing(data)
            elif action == "generate_variants":
                result = await self._generate_variants(data)
            elif action == "translate_listing":
                result = await self._translate_listing(data)
            elif action == "write_ad_copy":
                result = await self._write_ad_copy(data)
            else:
                result = {"error": f"Action inconnue: {action}"}

            await self.update_task_status(task, TaskStatus.COMPLETED.value, output_data=result)
            return result

        except Exception as exc:
            logger.exception("ProductWriterAgent.execute failed: %s", exc)
            await self.update_task_status(task, TaskStatus.FAILED.value, error=str(exc))
            raise

    async def _write_listing(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Write a complete product listing from scratch.

        Expected data:
          - product_name: str
          - category: str
          - features: list[str]
          - target_audience: str
          - platform: str  (amazon|ebay|shopify|tiktok_shop|generic)
          - keywords: list[str]  (optional, SEO keywords to include)
          - price_usd: float  (optional)
          - competitor_titles: list[str]  (optional)
        """
        product = data.get("product_name", "produit")
        platform = data.get("platform", "generic")
        prompt = (
            f"Rédige une fiche produit complète et optimisée pour: {product} sur {platform}\n\n"
            f"Données produit:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            f"Platform: {platform}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "platform": "...",\n'
            '  "title": "...",\n'
            '  "subtitle": "...",\n'
            '  "bullet_points": ["...", "...", "...", "...", "..."],\n'
            '  "description": "...",\n'
            '  "backend_keywords": ["..."],\n'
            '  "meta_description": "...",\n'
            '  "seo_score": 0,\n'
            '  "readability_score": 0,\n'
            '  "conversion_score": 0,\n'
            '  "content_notes": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="WRITE_PRODUCT_LISTING",
            entity_type="product_listing",
            entity_id=None,
            description=f"Fiche produit rédigée: {product} pour {platform}",
            new_data={"product": product, "platform": platform, "seo_score": result.get("seo_score")},
        )

        return result

    async def _optimize_listing(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Optimize an existing product listing.

        Expected data:
          - product_name: str
          - platform: str
          - current_listing: dict  (title, description, bullet_points, keywords)
          - performance_data: dict  (optional: ctr, conversion_rate, search_rank)
          - competitor_listings: list[dict]  (optional)
        """
        product = data.get("product_name", "produit")
        platform = data.get("platform", "generic")
        prompt = (
            f"Optimise la fiche produit existante pour: {product} sur {platform}\n\n"
            f"Listing actuel et données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Identifie les problèmes et propose une version améliorée.\n"
            "Format JSON:\n"
            "{\n"
            '  "issues_found": ["..."],\n'
            '  "optimized_title": "...",\n'
            '  "optimized_bullet_points": ["..."],\n'
            '  "optimized_description": "...",\n'
            '  "added_keywords": ["..."],\n'
            '  "removed_elements": ["..."],\n'
            '  "expected_improvements": {"ctr": "+0%", "conversion_rate": "+0%"},\n'
            '  "seo_score_before": 0,\n'
            '  "seo_score_after": 0\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _generate_variants(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate A/B test variants for a product listing.

        Expected data:
          - product_name: str
          - platform: str
          - base_listing: dict  (title, bullet_points)
          - variants_count: int  (default 3)
          - test_element: str  (TITLE|BULLETS|DESCRIPTION|ALL)
        """
        product = data.get("product_name", "produit")
        variants_count = data.get("variants_count", 3)
        test_element = data.get("test_element", "TITLE")
        prompt = (
            f"Génère {variants_count} variantes A/B pour tester: {test_element} — produit: {product}\n\n"
            f"Listing de base:\n{json.dumps(data.get('base_listing', {}), indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "test_element": "...",\n'
            '  "variants": [\n'
            '    {\n'
            '      "variant_id": "A",\n'
            '      "title": "...",\n'
            '      "bullet_points": ["..."],\n'
            '      "hypothesis": "...",\n'
            '      "expected_impact": "HIGH|MEDIUM|LOW"\n'
            '    }\n'
            '  ],\n'
            '  "testing_recommendations": "...",\n'
            '  "metrics_to_track": ["..."]\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _translate_listing(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Translate and localize a product listing for international markets.

        Expected data:
          - product_name: str
          - source_language: str  (default "en")
          - target_languages: list[str]  (e.g. ["fr", "de", "es"])
          - listing: dict  (title, description, bullet_points)
          - cultural_notes: str  (optional)
        """
        product = data.get("product_name", "produit")
        target_langs = data.get("target_languages", ["fr"])
        prompt = (
            f"Traduis et localise la fiche produit: {product} vers: {', '.join(target_langs)}\n\n"
            f"Contenu à traduire:\n{json.dumps(data.get('listing', {}), indent=2, ensure_ascii=False)}\n\n"
            "Adapte culturellement le contenu (pas une traduction mot à mot).\n"
            "Format JSON:\n"
            "{\n"
            '  "translations": {\n'
            '    "language_code": {\n'
            '      "title": "...",\n'
            '      "bullet_points": ["..."],\n'
            '      "description": "...",\n'
            '      "cultural_adaptations": ["..."]\n'
            '    }\n'
            '  }\n'
            "}"
        )

        response = await self.think(prompt)
        return self._parse_json_response(response)

    async def _write_ad_copy(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Write advertising copy for paid campaigns.

        Expected data:
          - product_name: str
          - platform: str  (facebook|tiktok|google|instagram)
          - objective: str  (AWARENESS|TRAFFIC|CONVERSIONS)
          - target_audience: str
          - key_benefit: str  (main selling point)
          - price_usd: float  (optional)
          - promotion: str  (optional, e.g. "20% off today only")
        """
        product = data.get("product_name", "produit")
        platform = data.get("platform", "facebook")
        objective = data.get("objective", "CONVERSIONS")
        prompt = (
            f"Rédige des copies publicitaires pour: {product} sur {platform} — objectif: {objective}\n\n"
            f"Données:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
            "Format JSON:\n"
            "{\n"
            '  "platform": "...",\n'
            '  "objective": "...",\n'
            '  "primary_text": "...",\n'
            '  "headline": "...",\n'
            '  "description": "...",\n'
            '  "cta": "...",\n'
            '  "hook_variants": ["...", "...", "..."],\n'
            '  "video_script_outline": "...",\n'
            '  "hashtags": ["..."],\n'
            '  "emojis_suggestion": "..."\n'
            "}"
        )

        response = await self.think(prompt)
        result = self._parse_json_response(response)

        await self.log_action(
            action="WRITE_AD_COPY",
            entity_type="ad_copy",
            entity_id=None,
            description=f"Copies publicitaires rédigées: {product} pour {platform}",
            new_data={"product": product, "platform": platform, "objective": objective},
        )

        return result

    async def generate_report(self) -> dict[str, Any]:
        prompt = (
            "En tant que Rédacteur Produits, génère un rapport d'activité. "
            "Format JSON:\n"
            "{\n"
            '  "agent_name": "ProductWriter",\n'
            '  "status": "operational",\n'
            '  "listings_written_this_week": 0,\n'
            '  "listings_optimized_this_week": 0,\n'
            '  "avg_seo_score": 0.0,\n'
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
