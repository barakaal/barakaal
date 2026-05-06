from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.agent import Agent, AgentDecision, AgentTask, TaskStatus
from app.models.audit import Approval
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.dashboard import CEODashboardStats

router = APIRouter()


@router.get("/ceo", response_model=CEODashboardStats, summary="CEO dashboard aggregated stats")
async def ceo_dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> CEODashboardStats:
    now = datetime.now(timezone.utc)
    today = now.date()
    seven_days_ago = now - timedelta(days=7)

    # ---- Revenue today ----
    revenue_today_result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount_usd), 0)).where(
            and_(
                func.date(Order.created_at) == today,
                Order.status != OrderStatus.CANCELLED.value,
            )
        )
    )
    revenue_today = float(revenue_today_result.scalar_one() or 0)

    # ---- Orders today ----
    orders_today_result = await db.execute(
        select(func.count(Order.id)).where(
            and_(
                func.date(Order.created_at) == today,
                Order.status != OrderStatus.CANCELLED.value,
            )
        )
    )
    orders_today = orders_today_result.scalar_one()

    # ---- Active products ----
    active_products_result = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.ACTIVE.value)
    )
    active_products = active_products_result.scalar_one()

    # ---- Active agents ----
    active_agents_result = await db.execute(
        select(func.count(Agent.id)).where(Agent.is_active == True)  # noqa: E712
    )
    active_agents = active_agents_result.scalar_one()

    # ---- Pending approvals ----
    pending_approvals_result = await db.execute(
        select(func.count(Approval.id)).where(Approval.status == "PENDING")
    )
    pending_approvals = pending_approvals_result.scalar_one()

    # ---- Top 5 products (by score) ----
    top_products_result = await db.execute(
        select(Product.id, Product.name, Product.score, Product.selling_price)
        .where(Product.status == ProductStatus.ACTIVE.value)
        .order_by(Product.score.desc().nullslast())
        .limit(5)
    )
    top_products = [
        {
            "id": r.id,
            "name": r.name,
            "score": float(r.score or 0),
            "selling_price": float(r.selling_price or 0),
        }
        for r in top_products_result
    ]

    # ---- 7-day revenue chart ----
    revenue_7d_result = await db.execute(
        select(
            func.date(Order.created_at).label("day"),
            func.coalesce(func.sum(Order.total_amount_usd), 0).label("revenue"),
            func.count(Order.id).label("order_count"),
        )
        .where(
            and_(
                Order.created_at >= seven_days_ago,
                Order.status != OrderStatus.CANCELLED.value,
            )
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    revenue_chart = [
        {"date": str(r.day), "revenue": float(r.revenue or 0), "orders": r.order_count}
        for r in revenue_7d_result
    ]

    # ---- Agent tasks today ----
    tasks_today_result = await db.execute(
        select(func.count(AgentTask.id)).where(
            func.date(AgentTask.created_at) == today
        )
    )
    tasks_today = tasks_today_result.scalar_one()

    # ---- Completed tasks today ----
    completed_today_result = await db.execute(
        select(func.count(AgentTask.id)).where(
            and_(
                func.date(AgentTask.created_at) == today,
                AgentTask.status == TaskStatus.COMPLETED.value,
            )
        )
    )
    completed_today = completed_today_result.scalar_one()

    # ---- Decisions pending approval ----
    decisions_pending_result = await db.execute(
        select(func.count(AgentDecision.id)).where(
            AgentDecision.status == "PENDING_APPROVAL"
        )
    )
    decisions_pending = decisions_pending_result.scalar_one()

    alerts: list[dict] = []
    if pending_approvals > 0:
        alerts.append({"type": "WARNING", "message": f"{pending_approvals} approval(s) awaiting review"})
    if decisions_pending > 0:
        alerts.append({"type": "INFO", "message": f"{decisions_pending} agent decision(s) pending approval"})

    return CEODashboardStats(
        revenue_today=revenue_today,
        orders_today=orders_today,
        active_products=active_products,
        active_agents=active_agents,
        pending_approvals=pending_approvals,
        top_products=top_products,
        revenue_chart_7d=revenue_chart,
        agent_tasks_today=tasks_today,
        agent_tasks_completed_today=completed_today,
        decisions_pending_approval=decisions_pending,
        alerts=alerts,
    )
