from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    pass


class RateLimitError(ConnectorError):
    pass


class AuthError(ConnectorError):
    pass


class BaseConnector(ABC):
    """Interface de base pour tous les connecteurs marketplace.

    Tous les connecteurs DOIVENT utiliser uniquement:
    - APIs officielles avec clés valides
    - Flux partenaires autorisés
    - Données CSV importées
    N'JAMAIS faire de scraping non autorisé.
    """

    PLATFORM_NAME: str = "base"
    IS_MOCK: bool = True  # True en mode dev sans vraie clé API

    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.is_configured = bool(self.api_key)
        self.last_request_at: Optional[datetime] = None
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def test_connection(self) -> dict:
        """Teste la connexion et retourne {success: bool, message: str, latency_ms: int}"""
        if not self.is_configured:
            return {
                "success": False,
                "message": f"No API key configured for {self.PLATFORM_NAME}",
                "latency_ms": 0,
            }
        try:
            return await self._test_connection_impl()
        except Exception as e:
            return {"success": False, "message": str(e), "latency_ms": 0}

    @abstractmethod
    async def _test_connection_impl(self) -> dict:
        pass

    @abstractmethod
    async def get_trending_products(self, category: str = None, limit: int = 20) -> list[dict]:
        """Retourne liste de produits tendances avec: name, category, price, demand_score, url, images, description"""
        pass

    @abstractmethod
    async def get_product_details(self, product_id: str) -> dict:
        """Retourne détails complets d'un produit"""
        pass

    async def close(self):
        await self._http_client.aclose()

    def _mock_trending_products(self, count: int = 10) -> list[dict]:
        """Génère des données mock réalistes pour les tests"""
        import random

        categories = [
            "Electronics",
            "Home & Garden",
            "Toys",
            "Beauty",
            "Sports",
            "Pet Supplies",
            "Kitchen",
        ]
        products = []
        for i in range(count):
            category = random.choice(categories)
            products.append(
                {
                    "id": f"{self.PLATFORM_NAME}_{i+1}",
                    "name": f"Trending {category} Product #{i+1}",
                    "category": category,
                    "price_usd": round(random.uniform(5, 150), 2),
                    "demand_score": round(random.uniform(60, 99), 1),
                    "growth_rate_pct": round(random.uniform(-5, 120), 1),
                    "competition_level": random.choice(["LOW", "MEDIUM", "HIGH"]),
                    "rating": round(random.uniform(3.5, 5.0), 1),
                    "reviews_count": random.randint(50, 5000),
                    "source_platform": self.PLATFORM_NAME,
                    "url": f"https://mock.{self.PLATFORM_NAME.lower()}.com/product/{i+1}",
                    "images": [f"https://picsum.photos/400/400?random={i}"],
                    "description": f"Mock product description for {category} item #{i+1}",
                    "shipping_days_min": random.randint(7, 14),
                    "shipping_days_max": random.randint(20, 35),
                    "is_mock_data": True,
                }
            )
        return products
