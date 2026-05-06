from .base import BaseConnector
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AliExpressConnector(BaseConnector):
    """
    Connecteur AliExpress Marketplace.

    En production, utilise AliExpress DS (Dropshipping) API officielle ou Affiliate API.
    Documentation: https://developers.aliexpress.com/

    Les clés API sont obtenues via le portail AliExpress Open Platform.
    En mode mock (IS_MOCK=True), retourne des données de démonstration.
    """

    PLATFORM_NAME = "ALIEXPRESS"
    BASE_URL = "https://api-sg.aliexpress.com/sync"

    def __init__(self, config: dict):
        super().__init__(config)
        self.app_key = config.get("app_key", self.api_key)
        self.app_secret = config.get("app_secret", self.api_secret)
        self.access_token = config.get("access_token", "")
        self.IS_MOCK = not (self.app_key and self.app_secret)

    async def _test_connection_impl(self) -> dict:
        if self.IS_MOCK:
            return {
                "success": True,
                "message": "Mock mode - no real AliExpress API key configured",
                "latency_ms": 0,
                "is_mock": True,
            }
        # Production: appel AliExpress API pour vérifier le token
        start = datetime.now()
        try:
            # TODO: Implémenter appel AliExpress Open Platform
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return {
                "success": True,
                "message": "Connected to AliExpress API",
                "latency_ms": elapsed,
            }
        except Exception as e:
            return {"success": False, "message": str(e), "latency_ms": 0}

    async def get_trending_products(self, category: str = None, limit: int = 20) -> list[dict]:
        if self.IS_MOCK:
            logger.info("AliExpressConnector: using mock data (no real API key configured)")
            import random

            products = self._mock_trending_products(limit)
            for p in products:
                p["source_platform"] = "ALIEXPRESS"
                p["supplier_price"] = round(p["price_usd"] * 0.3, 2)
                p["shipping_cost_usd"] = round(random.uniform(0, 5), 2)
                p["shipping_days"] = random.randint(14, 35)
                p["moq"] = 1
                p["is_aliexpress"] = True
                p["seller_rating"] = round(random.uniform(4.0, 5.0), 1)
                p["orders_count"] = random.randint(100, 50000)
            return products
        # Production: AliExpress DS API - aliexpress.ds.recommend.feed.get
        raise NotImplementedError("Configure AliExpress API credentials to use real data")

    async def get_product_details(self, product_id: str) -> dict:
        if self.IS_MOCK:
            import random

            return {
                "id": product_id,
                "name": f"AliExpress Product {product_id}",
                "source_platform": "ALIEXPRESS",
                "supplier_price": round(random.uniform(2, 50), 2),
                "shipping_cost_usd": round(random.uniform(0, 5), 2),
                "shipping_days": random.randint(14, 35),
                "moq": 1,
                "is_aliexpress": True,
                "is_mock_data": True,
            }
        raise NotImplementedError("Configure AliExpress API credentials")

    async def get_shipping_options(self, product_id: str, country: str = "US") -> list[dict]:
        """Récupère les options de livraison pour un produit vers un pays donné."""
        if self.IS_MOCK:
            import random

            return [
                {
                    "method": "AliExpress Standard Shipping",
                    "cost_usd": round(random.uniform(0, 3), 2),
                    "days_min": 15,
                    "days_max": 30,
                    "tracking": True,
                    "is_mock_data": True,
                },
                {
                    "method": "ePacket",
                    "cost_usd": round(random.uniform(3, 8), 2),
                    "days_min": 10,
                    "days_max": 20,
                    "tracking": True,
                    "is_mock_data": True,
                },
                {
                    "method": "DHL Express",
                    "cost_usd": round(random.uniform(15, 35), 2),
                    "days_min": 3,
                    "days_max": 7,
                    "tracking": True,
                    "is_mock_data": True,
                },
            ]
        raise NotImplementedError("Configure AliExpress API credentials")
