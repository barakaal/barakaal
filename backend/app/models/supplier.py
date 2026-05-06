from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    response_time_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_order_qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payment_terms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_info: Mapped[dict] = mapped_column(JSON, default=dict)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    offers: Mapped[list["SupplierOffer"]] = relationship("SupplierOffer", back_populates="supplier")


class SupplierOffer(Base):
    __tablename__ = "supplier_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_cost_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_days_min: Mapped[int] = mapped_column(Integer, nullable=False)
    shipping_days_max: Mapped[int] = mapped_column(Integer, nullable=False)
    moq: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="supplier_offers")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="offers")


from app.models.product import Product  # noqa: E402
