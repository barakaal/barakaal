from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    tags: List[str] = []
    source_platform: str
    source_url: Optional[str] = None
    images: List[str] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source_platform: Optional[str] = None
    source_url: Optional[str] = None
    images: Optional[List[str]] = None
    status: Optional[str] = None
    score: Optional[float] = None
    score_details: Optional[Dict[str, Any]] = None
    selling_price_usd: Optional[float] = None
    cost_price_usd: Optional[float] = None
    gross_margin_pct: Optional[float] = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    tags: List[str]
    source_platform: str
    source_url: Optional[str] = None
    images: List[str]
    status: str
    score: Optional[float] = None
    score_details: Optional[Dict[str, Any]] = None
    selling_price_usd: Optional[float] = None
    cost_price_usd: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductTrendOut(BaseModel):
    id: int
    product_id: int
    platform: str
    keyword: str
    trend_score: float
    search_volume: Optional[int] = None
    growth_rate_pct: Optional[float] = None
    competition_level: Optional[str] = None
    avg_market_price_usd: Optional[float] = None
    data_date: date
    raw_data: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductScoreDetails(BaseModel):
    popularite: float
    croissance_demande: float
    prix_fournisseur_score: float
    marge_brute_score: float
    frais_livraison_score: float
    delai_livraison_score: float
    concurrence_score: float
    retour_probable_score: float
    risque_legal_score: float
    risque_qualite_score: float
    saisonnalite_score: float
    potentiel_pub_score: float
    score_final: float


class SupplierOfferOut(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    supplier_name: str
    sku: Optional[str] = None
    unit_price_usd: float
    shipping_cost_usd: float
    shipping_days_min: int
    shipping_days_max: int
    moq: int
    currency: str
    is_available: bool
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
