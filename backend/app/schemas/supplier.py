from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    name: str
    platform: str
    country: str
    rating: Optional[float] = None
    response_time_hours: Optional[int] = None
    min_order_qty: int = 1
    payment_terms: Optional[str] = None
    contact_info: Dict[str, Any] = {}


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[float] = None
    response_time_hours: Optional[int] = None
    min_order_qty: Optional[int] = None
    payment_terms: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class SupplierOut(BaseModel):
    id: int
    name: str
    platform: str
    country: str
    rating: Optional[float] = None
    response_time_hours: Optional[int] = None
    min_order_qty: int
    payment_terms: Optional[str] = None
    contact_info: Dict[str, Any]
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SupplierOfferCreate(BaseModel):
    product_id: int
    supplier_id: int
    sku: Optional[str] = None
    unit_price_usd: float
    shipping_cost_usd: float
    shipping_days_min: int
    shipping_days_max: int
    moq: int = 1
    currency: str = "USD"


class SupplierOfferOut(BaseModel):
    id: int
    product_id: int
    supplier_id: int
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
