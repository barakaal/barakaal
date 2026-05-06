from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    shipping_address: Dict[str, Any] = {}


class CustomerOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    shipping_address: Dict[str, Any]
    total_orders: int
    total_spent_usd: float
    is_blocked: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_id: int
    items: List[Dict[str, Any]]
    shipping_address: Dict[str, Any]


class OrderOut(BaseModel):
    id: int
    order_number: str
    customer_id: int
    status: str
    items: List[Dict[str, Any]]
    subtotal_usd: float
    shipping_usd: float
    total_usd: float
    currency: str
    shipping_address: Dict[str, Any]
    supplier_order_id: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    notes: Optional[str] = None
    fraud_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
