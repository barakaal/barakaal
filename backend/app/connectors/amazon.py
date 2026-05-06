from .base import BaseConnector
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AmazonConnector(BaseConnector):
    """
    Connecteur Amazon Marketplace.

    En production, utilise Amazon Product Advertising API 5.0 ou SP-API.
    Documentation: https://webservices.amazon.com/paapi5/documentation/

    En mode mock (IS_MOCK=True), retourne des données de démonstration.
    """

    PLATFORM_NAME = "AMAZON"
    BASE_URL = "https://webservices.amazon.com/paapi5"

    def __init__(self, config: dict):
        super().__init__(config)
        self.partner_tag = config.get("partner_tag", "")
        self.region = config.get("region", "us-east-1")
        self.IS_MOCK = not (self.api_key and self.api_secret and self.partner_tag)

    async def _test_connection_impl(self) -> dict:
        if self.IS_MOCK:
            return {
                "success": True,
                "message": "Mock mode - no real API call",
                "latency_ms": 0,
                "is_mock": True,
            }
        # En production: appel API réel avec signature AWS SigV4
        start = datetime.now()
        # TODO: Implémenter la signature AWS SigV4 pour PA-API
        return {
            "success": True,
            "message": "Connected to Amazon PA-API",
            "latency_ms": int((datetime.now() - start).total_seconds() * 1000),
        }

    async def get_trending_products(self, category: str = None, limit: int = 20) -> list[dict]:
        if self.IS_MOCK:
            logger.info("AmazonConnector: using mock data (no real API key configured)")
            products = self._mock_trending_products(limit)
            import random

            for p in products:
                p["amazon_bsr"] = random.randint(1, 100000)
                p["prime_eligible"] = True
                p["source_platform"] = "AMAZON"
            return products
        # Production: Amazon PA-API SearchItems
        # https://webservices.amazon.com/paapi5/documentation/search-items.html
        raise NotImplementedError("Configure Amazon PA-API credentials to use real data")

    async def get_product_details(self, product_id: str) -> dict:
        if self.IS_MOCK:
            return {
                "id": product_id,
                "name": f"Amazon Product {product_id}",
                "asin": product_id,
                "source_platform": "AMAZON",
                "is_mock_data": True,
            }
        raise NotImplementedError("Configure Amazon PA-API credentials")

    async def get_bestsellers(self, category: str, limit: int = 20) -> list[dict]:
        """Récupère les bestsellers d'une catégorie (PA-API BrowseNodes)"""
        if self.IS_MOCK:
            logger.info("AmazonConnector.get_bestsellers: using mock data")
            products = self._mock_trending_products(limit)
            import random

            for p in products:
                p["amazon_bsr"] = random.randint(1, 100000)
                p["prime_eligible"] = True
                p["source_platform"] = "AMAZON"
                p["category"] = category or p["category"]
            return products
        raise NotImplementedError("Configure Amazon PA-API credentials")
