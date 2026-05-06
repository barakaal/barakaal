from .base import BaseConnector
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)


class TikTokConnector(BaseConnector):
    """
    Connecteur TikTok for Business.

    En production, utilise TikTok for Business API (Creative Center, Ads API).
    Documentation: https://business-api.tiktok.com/portal/docs

    Les credentials sont obtenus via TikTok for Business Developer Platform.
    En mode mock (IS_MOCK=True), retourne des données de démonstration.
    """

    PLATFORM_NAME = "TIKTOK"
    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"
    CREATIVE_CENTER_URL = "https://ads.tiktok.com/creative_radar_api/v1"

    def __init__(self, config: dict):
        super().__init__(config)
        self.access_token = config.get("access_token", self.api_key)
        self.advertiser_id = config.get("advertiser_id", "")
        self.IS_MOCK = not bool(self.access_token)

    async def _test_connection_impl(self) -> dict:
        if self.IS_MOCK:
            return {
                "success": True,
                "message": "Mock mode - no real TikTok API credentials configured",
                "latency_ms": 0,
                "is_mock": True,
            }
        start = datetime.now()
        try:
            # Production: vérifier le token via TikTok Business API
            headers = {
                "Access-Token": self.access_token,
                "Content-Type": "application/json",
            }
            response = await self._http_client.get(
                f"{self.BASE_URL}/advertiser/info/",
                headers=headers,
                params={"advertiser_ids": f'["{self.advertiser_id}"]'},
            )
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connected to TikTok Business API",
                    "latency_ms": elapsed,
                }
            return {
                "success": False,
                "message": f"TikTok API returned {response.status_code}",
                "latency_ms": elapsed,
            }
        except Exception as e:
            return {"success": False, "message": str(e), "latency_ms": 0}

    async def get_trending_products(self, category: str = None, limit: int = 20) -> list[dict]:
        if self.IS_MOCK:
            logger.info("TikTokConnector: using mock data (no real API credentials configured)")
            products = self._mock_trending_products(limit)
            for p in products:
                p["source_platform"] = "TIKTOK"
                p["viral_score"] = round(random.uniform(50, 100), 1)
                p["hashtags"] = [
                    f"#{p['category'].lower().replace(' ', '')}",
                    "#tiktokmademebuyit",
                    "#viral",
                    f"#trending{random.randint(1, 999)}",
                ]
                p["engagement_rate"] = round(random.uniform(2.0, 15.0), 2)
                p["view_count"] = random.randint(100000, 50000000)
                p["like_count"] = random.randint(5000, 2000000)
                p["share_count"] = random.randint(500, 200000)
                p["comment_count"] = random.randint(100, 50000)
                p["creator_count"] = random.randint(10, 10000)
                p["avg_video_duration_sec"] = random.randint(15, 60)
            return products
        # Production: TikTok Creative Center Trending Products API
        raise NotImplementedError("Configure TikTok Business API credentials to use real data")

    async def get_product_details(self, product_id: str) -> dict:
        if self.IS_MOCK:
            return {
                "id": product_id,
                "name": f"TikTok Viral Product {product_id}",
                "source_platform": "TIKTOK",
                "viral_score": round(random.uniform(50, 100), 1),
                "hashtags": ["#tiktokmademebuyit", "#viral"],
                "engagement_rate": round(random.uniform(2.0, 15.0), 2),
                "view_count": random.randint(100000, 50000000),
                "is_mock_data": True,
            }
        raise NotImplementedError("Configure TikTok Business API credentials")

    async def get_trending_hashtags(
        self, category: str = None, limit: int = 20
    ) -> list[dict]:
        """
        Récupère les hashtags tendances sur TikTok.
        Utilise TikTok Creative Center Trend Discovery API.
        """
        if self.IS_MOCK:
            base_hashtags = [
                "tiktokmademebuyit",
                "musthave",
                "viral",
                "trending",
                "amazonfinds",
                "productreview",
                "unboxing",
                "lifehack",
                "gadgets",
                "homedecor",
            ]
            return [
                {
                    "hashtag": f"#{tag}",
                    "post_count": random.randint(10000, 10000000),
                    "view_count": random.randint(1000000, 1000000000),
                    "growth_rate_pct": round(random.uniform(5, 200), 1),
                    "category": category or "General",
                    "is_mock_data": True,
                }
                for tag in base_hashtags[:limit]
            ]
        raise NotImplementedError("Configure TikTok Business API credentials")

    async def get_video_analytics(self, video_id: str) -> dict:
        """Récupère les analytics d'une vidéo TikTok spécifique."""
        if self.IS_MOCK:
            return {
                "video_id": video_id,
                "view_count": random.randint(10000, 10000000),
                "like_count": random.randint(500, 500000),
                "share_count": random.randint(50, 50000),
                "comment_count": random.randint(10, 10000),
                "engagement_rate": round(random.uniform(1.0, 20.0), 2),
                "avg_watch_time_sec": round(random.uniform(5, 45), 1),
                "is_mock_data": True,
            }
        raise NotImplementedError("Configure TikTok Business API credentials")
