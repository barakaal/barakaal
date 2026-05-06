from .amazon import AmazonConnector
from .aliexpress import AliExpressConnector
from .ebay import EbayConnector
from .google_trends import GoogleTrendsConnector
from .tiktok import TikTokConnector
from .csv_import import CSVImportConnector

CONNECTOR_MAP = {
    "AMAZON": AmazonConnector,
    "ALIEXPRESS": AliExpressConnector,
    "EBAY": EbayConnector,
    "GOOGLE_TRENDS": GoogleTrendsConnector,
    "TIKTOK": TikTokConnector,
    "CSV_IMPORT": CSVImportConnector,
}


def get_connector(platform: str, config: dict):
    """Instancie un connecteur par nom de plateforme."""
    cls = CONNECTOR_MAP.get(platform.upper())
    if not cls:
        raise ValueError(f"Unknown platform: {platform}")
    return cls(config)


def get_all_connectors(configs: dict) -> dict:
    """Instancie tous les connecteurs depuis une config {platform: {api_key: ...}}"""
    connectors = {}
    for platform, config in configs.items():
        try:
            connectors[platform] = get_connector(platform, config)
        except Exception:
            pass
    return connectors


def get_default_connectors() -> dict:
    """
    Retourne tous les connecteurs en mode mock (sans clés API).
    Utile pour le développement et les tests.
    """
    return {
        platform: cls({})
        for platform, cls in CONNECTOR_MAP.items()
        if platform != "CSV_IMPORT"
    }
