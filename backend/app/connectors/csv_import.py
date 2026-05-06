import csv
import io
from typing import Optional
import logging
from .base import BaseConnector

logger = logging.getLogger(__name__)


class CSVImportConnector(BaseConnector):
    """
    Connecteur d'import CSV pour produits, fournisseurs et tendances.

    Format CSV attendu pour produits:
    name, description, category, price_usd, source_platform, source_url, tags

    Format CSV pour fournisseurs:
    supplier_name, platform, country, price_usd, shipping_cost, shipping_days_min, shipping_days_max, moq
    """

    PLATFORM_NAME = "CSV_IMPORT"
    IS_MOCK = False  # Toujours réel

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.is_configured = True

    async def _test_connection_impl(self) -> dict:
        return {
            "success": True,
            "message": "CSV Import connector always available",
            "latency_ms": 0,
        }

    async def get_trending_products(self, category: str = None, limit: int = 20) -> list[dict]:
        return []  # CSV import doesn't generate trends

    async def get_product_details(self, product_id: str) -> dict:
        return {}

    async def parse_products_csv(self, content: bytes) -> tuple[list[dict], list[str]]:
        """Parse CSV produits. Retourne (products, errors)"""
        products = []
        errors = []

        try:
            text = content.decode("utf-8-sig")  # Handle BOM
            reader = csv.DictReader(io.StringIO(text))

            required_fields = ["name", "category", "price_usd"]

            for row_num, row in enumerate(reader, start=2):
                row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

                missing = [f for f in required_fields if not row.get(f)]
                if missing:
                    errors.append(f"Row {row_num}: missing fields {missing}")
                    continue

                try:
                    price = float(row["price_usd"])
                except ValueError:
                    errors.append(
                        f"Row {row_num}: invalid price_usd '{row['price_usd']}'"
                    )
                    continue

                products.append(
                    {
                        "name": row["name"],
                        "description": row.get("description", ""),
                        "category": row["category"],
                        "tags": [
                            t.strip()
                            for t in row.get("tags", "").split(",")
                            if t.strip()
                        ],
                        "source_platform": row.get("source_platform", "CSV_IMPORT"),
                        "source_url": row.get("source_url", ""),
                        "cost_price_usd": price,
                        "images": [],
                        "status": "CANDIDATE",
                    }
                )

        except Exception as e:
            errors.append(f"CSV parse error: {str(e)}")

        return products, errors

    async def parse_suppliers_csv(self, content: bytes) -> tuple[list[dict], list[str]]:
        """Parse CSV fournisseurs"""
        suppliers = []
        errors = []

        try:
            text = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))

            for row_num, row in enumerate(reader, start=2):
                row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

                if not row.get("supplier_name"):
                    errors.append(f"Row {row_num}: missing supplier_name")
                    continue

                try:
                    suppliers.append(
                        {
                            "name": row["supplier_name"],
                            "platform": row.get("platform", "OTHER"),
                            "country": row.get("country", "CN"),
                            "unit_price_usd": float(row.get("price_usd", 0)),
                            "shipping_cost_usd": float(row.get("shipping_cost", 0)),
                            "shipping_days_min": int(row.get("shipping_days_min", 14)),
                            "shipping_days_max": int(row.get("shipping_days_max", 30)),
                            "moq": int(row.get("moq", 1)),
                        }
                    )
                except ValueError as e:
                    errors.append(
                        f"Row {row_num}: invalid numeric value - {e}"
                    )

        except Exception as e:
            errors.append(f"CSV parse error: {str(e)}")

        return suppliers, errors

    async def parse_trends_csv(self, content: bytes) -> tuple[list[dict], list[str]]:
        """
        Parse CSV de données de tendances.

        Format CSV attendu:
        keyword, platform, trend_score, search_volume, growth_rate_pct, competition_level, avg_market_price_usd
        """
        trends = []
        errors = []

        try:
            text = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))

            required_fields = ["keyword", "trend_score"]

            for row_num, row in enumerate(reader, start=2):
                row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

                missing = [f for f in required_fields if not row.get(f)]
                if missing:
                    errors.append(f"Row {row_num}: missing fields {missing}")
                    continue

                try:
                    trend_score = float(row["trend_score"])
                    if not (0 <= trend_score <= 100):
                        errors.append(
                            f"Row {row_num}: trend_score must be between 0 and 100"
                        )
                        continue

                    trends.append(
                        {
                            "keyword": row["keyword"],
                            "platform": row.get("platform", "CSV_IMPORT").upper(),
                            "trend_score": trend_score,
                            "search_volume": int(row["search_volume"])
                            if row.get("search_volume")
                            else None,
                            "growth_rate_pct": float(row["growth_rate_pct"])
                            if row.get("growth_rate_pct")
                            else None,
                            "competition_level": row.get(
                                "competition_level", "MEDIUM"
                            ).upper(),
                            "avg_market_price_usd": float(
                                row["avg_market_price_usd"]
                            )
                            if row.get("avg_market_price_usd")
                            else None,
                        }
                    )
                except (ValueError, TypeError) as e:
                    errors.append(f"Row {row_num}: invalid value - {e}")

        except Exception as e:
            errors.append(f"CSV parse error: {str(e)}")

        return trends, errors
