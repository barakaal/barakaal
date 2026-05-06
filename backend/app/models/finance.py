from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinancialReport(Base):
    __tablename__ = "financial_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    revenue_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    cogs_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    gross_profit_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    operating_costs_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    net_profit_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    orders_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_order_value_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    report_data: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_by_agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("agents.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
