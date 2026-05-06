from .base import BaseConnector
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GoogleTrendsConnector(BaseConnector):
    """
    Connecteur Google Trends.

    Utilise pytrends (bibliothèque Python non officielle mais permise pour usage légal)
    ou l'API Google Trends pour récupérer les tendances de recherche.

    Note: Google Trends n'a pas d'API officielle payante.
    pytrends est utilisé de manière responsable avec délais entre requêtes.
    """

    PLATFORM_NAME = "GOOGLE_TRENDS"
    IS_MOCK = True  # Toujours mock au MVP, activer avec pytrends en prod

    def __init__(self, config: dict):
        super().__init__(config)
        self.geo = config.get("geo", "US")
        self.timeframe = config.get("timeframe", "today 3-m")

    async def _test_connection_impl(self) -> dict:
        return {
            "success": True,
            "message": "Google Trends connector ready (mock mode)",
            "latency_ms": 0,
        }

    async def get_trending_products(self, category: str = None, limit: int = 20) -> list[dict]:
        """Retourne les keywords trending sur Google"""
        products = self._mock_trending_products(limit)
        for p in products:
            p["source_platform"] = "GOOGLE_TRENDS"
            p["search_volume_monthly"] = random.randint(1000, 500000)
            p["trend_direction"] = random.choice(["rising", "stable", "declining"])
            p["related_keywords"] = [f"keyword_{i}" for i in range(5)]
        return products

    async def get_product_details(self, product_id: str) -> dict:
        return {
            "keyword": product_id,
            "source_platform": "GOOGLE_TRENDS",
            "is_mock_data": True,
        }

    async def get_keyword_trends(
        self, keywords: list[str], timeframe: str = "today 3-m", geo: str = "US"
    ) -> dict:
        """Retourne les tendances pour une liste de keywords"""
        if not self.IS_MOCK:
            # Production: utiliser pytrends avec rate limiting respectueux
            # from pytrends.request import TrendReq
            # pytrends = TrendReq(hl='en-US', tz=360)
            # pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
            # interest_df = pytrends.interest_over_time()
            pass

        result = {}
        for kw in keywords:
            result[kw] = {
                "interest_over_time": [
                    {
                        "date": (datetime.now() - timedelta(weeks=i)).strftime("%Y-%m-%d"),
                        "value": random.randint(20, 100),
                    }
                    for i in range(12, 0, -1)
                ],
                "current_score": random.randint(40, 100),
                "growth_rate_pct": random.uniform(-20, 150),
                "is_mock_data": True,
            }
        return result

    async def get_rising_queries(self, keyword: str, geo: str = "US") -> list[dict]:
        """Retourne les requêtes en hausse associées à un keyword"""
        return [
            {
                "query": f"{keyword} {suffix}",
                "value": random.randint(100, 5000),
                "is_mock_data": True,
            }
            for suffix in ["buy online", "best price", "review", "cheap", "discount"]
        ]

    async def get_trending_searches(self, geo: str = "US") -> list[dict]:
        """Retourne les recherches tendances du jour sur Google."""
        topics = [
            "wireless earbuds",
            "LED strip lights",
            "portable blender",
            "phone stand",
            "posture corrector",
            "reusable water bottle",
            "car phone holder",
            "desk lamp",
            "yoga mat",
            "resistance bands",
        ]
        return [
            {
                "keyword": topic,
                "trend_score": random.randint(60, 100),
                "search_volume_estimate": random.randint(10000, 1000000),
                "geo": geo,
                "is_mock_data": True,
            }
            for topic in topics[:10]
        ]
