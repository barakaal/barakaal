import enum
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProductStatus(str, enum.Enum):
    CANDIDATE = "CANDIDATE"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REJECTED = "REJECTED"
    DISCONTINUED = "DISCONTINUED"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    source_platform: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    images: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default=ProductStatus.CANDIDATE.value, nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    score_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    selling_price_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cost_price_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    gross_margin_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    trends: Mapped[list["ProductTrend"]] = relationship("ProductTrend", back_populates="product")
    supplier_offers: Mapped[list["SupplierOffer"]] = relationship("SupplierOffer", back_populates="product")


class Platform(str, enum.Enum):
    AMAZON = "AMAZON"
    ALIEXPRESS = "ALIEXPRESS"
    EBAY = "EBAY"
    TIKTOK = "TIKTOK"
    GOOGLE_TRENDS = "GOOGLE_TRENDS"
    ETSY = "ETSY"
    WALMART = "WALMART"
    CSV_IMPORT = "CSV_IMPORT"


class ProductTrend(Base):
    __tablename__ = "product_trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    trend_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    growth_rate_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    competition_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    avg_market_price_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="trends")


from app.models.supplier import SupplierOffer  # noqa: E402
