from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.finance import FinancialReport
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schemas
# ---------------------------------------------------------------------------

class FinancialReportCreate(BaseModel):
    period_start: date
    period_end: date
    report_type: str = "MONTHLY"


class FinancialReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: str
    period_start: date
    period_end: date
    total_revenue_usd: float
    total_cost_usd: float
    gross_profit_usd: float
    net_profit_usd: float
    order_count: int
    data: Optional[dict] = None
    generated_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/reports/", response_model=list[FinancialReportOut], summary="List financial reports")
async def list_reports(
    report_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[FinancialReportOut]:
    query = select(FinancialReport).order_by(FinancialReport.period_start.desc())
    if report_type:
        query = query.where(FinancialReport.report_type == report_type)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return [FinancialReportOut.model_validate(r) for r in result.scalars().all()]


@router.get("/reports/{report_id}", response_model=FinancialReportOut, summary="Get financial report by ID")
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> FinancialReportOut:
    result = await db.execute(select(FinancialReport).where(FinancialReport.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return FinancialReportOut.model_validate(report)


@router.post(
    "/reports/generate",
    response_model=FinancialReportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a financial report",
)
async def generate_report(
    report_in: FinancialReportCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> FinancialReportOut:
    if report_in.period_end < report_in.period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_end must be >= period_start",
        )

    # Aggregate orders in the period
    orders_result = await db.execute(
        select(
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_amount_usd), 0).label("revenue"),
            func.coalesce(func.sum(Order.cost_amount_usd), 0).label("cost"),
        ).where(
            and_(
                func.date(Order.created_at) >= report_in.period_start,
                func.date(Order.created_at) <= report_in.period_end,
                Order.status != OrderStatus.CANCELLED.value,
            )
        )
    )
    row = orders_result.one()
    revenue = float(row.revenue or 0)
    cost = float(row.cost or 0)
    gross_profit = revenue - cost
    # Simplified: net = gross * 0.85 (15% overhead)
    net_profit = gross_profit * 0.85

    now = datetime.now(timezone.utc)
    report = FinancialReport(
        report_type=report_in.report_type,
        period_start=report_in.period_start,
        period_end=report_in.period_end,
        total_revenue_usd=revenue,
        total_cost_usd=cost,
        gross_profit_usd=gross_profit,
        net_profit_usd=net_profit,
        order_count=row.order_count,
        data={
            "generated_by": "api",
            "period_start": report_in.period_start.isoformat(),
            "period_end": report_in.period_end.isoformat(),
        },
        generated_at=now,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return FinancialReportOut.model_validate(report)


@router.get("/summary", summary="Current month financial summary")
async def finance_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    month_start = date(now.year, now.month, 1)

    # Revenue & orders MTD
    mtd_result = await db.execute(
        select(
            func.count(Order.id).label("orders_mtd"),
            func.coalesce(func.sum(Order.total_amount_usd), 0).label("revenue_mtd"),
            func.coalesce(func.sum(Order.cost_amount_usd), 0).label("cost_mtd"),
        ).where(
            and_(
                func.date(Order.created_at) >= month_start,
                Order.status != OrderStatus.CANCELLED.value,
            )
        )
    )
    row = mtd_result.one()
    revenue_mtd = float(row.revenue_mtd or 0)
    cost_mtd = float(row.cost_mtd or 0)
    profit_mtd = (revenue_mtd - cost_mtd) * 0.85

    # Top 5 products by revenue (from orders line items — simplified using product price)
    top_products_result = await db.execute(
        select(Product.id, Product.name, Product.selling_price)
        .where(Product.selling_price.isnot(None))
        .order_by(Product.selling_price.desc())
        .limit(5)
    )
    top_products = [
        {"id": r.id, "name": r.name, "selling_price": float(r.selling_price or 0)}
        for r in top_products_result
    ]

    return {
        "revenue_mtd": round(revenue_mtd, 2),
        "profit_mtd": round(profit_mtd, 2),
        "orders_mtd": row.orders_mtd,
        "top_products_by_revenue": top_products,
        "period": {"start": month_start.isoformat(), "end": now.date().isoformat()},
    }
