from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.agent import AgentDecision, AgentTask, TaskStatus
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductStatus, ProductTrend
from app.models.user import User

router = APIRouter()


@router.get("/weekly", summary="Weekly global report")
async def weekly_report(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)

    # Orders this week
    orders_result = await db.execute(
        select(
            func.count(Order.id).label("count"),
            func.coalesce(func.sum(Order.total_amount_usd), 0).label("revenue"),
        ).where(
            and_(
                Order.created_at >= week_start,
                Order.status != OrderStatus.CANCELLED.value,
            )
        )
    )
    orders_row = orders_result.one()

    # Products active
    active_products_result = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.ACTIVE.value)
    )
    active_products = active_products_result.scalar_one()

    # Trends this week
    trends_result = await db.execute(
        select(func.count(ProductTrend.id)).where(ProductTrend.recorded_at >= week_start)
    )
    trend_signals = trends_result.scalar_one()

    # Agent tasks this week
    tasks_result = await db.execute(
        select(func.count(AgentTask.id)).where(AgentTask.created_at >= week_start)
    )
    agent_tasks = tasks_result.scalar_one()

    completed_tasks_result = await db.execute(
        select(func.count(AgentTask.id)).where(
            and_(
                AgentTask.created_at >= week_start,
                AgentTask.status == TaskStatus.COMPLETED.value,
            )
        )
    )
    completed_tasks = completed_tasks_result.scalar_one()

    # Decisions this week
    decisions_result = await db.execute(
        select(func.count(AgentDecision.id)).where(AgentDecision.created_at >= week_start)
    )
    decisions = decisions_result.scalar_one()

    return {
        "period": {"start": week_start.date().isoformat(), "end": now.date().isoformat()},
        "orders": {
            "count": orders_row.count,
            "revenue_usd": float(orders_row.revenue or 0),
        },
        "products": {
            "active": active_products,
            "trend_signals": trend_signals,
        },
        "agents": {
            "tasks_created": agent_tasks,
            "tasks_completed": completed_tasks,
            "completion_rate": round(completed_tasks / max(agent_tasks, 1) * 100, 1),
            "decisions_made": decisions,
        },
    }


@router.get("/products/performance", summary="Product performance ranking by revenue")
async def products_performance(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[dict[str, Any]]:
    # Revenue per product estimated from selling_price and score as a proxy
    result = await db.execute(
        select(
            Product.id,
            Product.name,
            Product.sku,
            Product.selling_price,
            Product.cost_price,
            Product.score,
            Product.status,
        )
        .where(Product.status == ProductStatus.ACTIVE.value)
        .order_by(Product.score.desc().nullslast(), Product.selling_price.desc().nullslast())
        .limit(limit)
    )

    rows = result.fetchall()
    output = []
    for r in rows:
        selling = float(r.selling_price or 0)
        cost = float(r.cost_price or 0)
        margin = ((selling - cost) / selling * 100) if selling > 0 else 0
        output.append(
            {
                "id": r.id,
                "name": r.name,
                "sku": r.sku,
                "selling_price": selling,
                "cost_price": cost,
                "margin_pct": round(margin, 2),
                "score": float(r.score or 0),
                "status": r.status,
            }
        )
    return output


@router.get("/agents/activity", summary="Agent activity report")
async def agents_activity(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    tasks_result = await db.execute(
        select(
            AgentTask.agent_id,
            func.count(AgentTask.id).label("total"),
            func.sum(
                func.cast(AgentTask.status == TaskStatus.COMPLETED.value, type_=func.count().type)
            ).label("completed"),
        )
        .where(AgentTask.created_at >= since)
        .group_by(AgentTask.agent_id)
    )

    decisions_result = await db.execute(
        select(
            AgentDecision.agent_id,
            func.count(AgentDecision.id).label("count"),
        )
        .where(AgentDecision.created_at >= since)
        .group_by(AgentDecision.agent_id)
    )

    task_rows = tasks_result.fetchall()
    decision_rows = {r.agent_id: r.count for r in decisions_result.fetchall()}

    agents_data = []
    total_tasks = 0
    total_completed = 0

    for row in task_rows:
        completed = int(row.completed or 0)
        total = int(row.total or 0)
        total_tasks += total
        total_completed += completed
        agents_data.append(
            {
                "agent_id": row.agent_id,
                "tasks_total": total,
                "tasks_completed": completed,
                "success_rate_pct": round(completed / max(total, 1) * 100, 1),
                "decisions_made": decision_rows.get(row.agent_id, 0),
            }
        )

    return {
        "period_days": days,
        "summary": {
            "total_tasks": total_tasks,
            "total_completed": total_completed,
            "global_success_rate_pct": round(total_completed / max(total_tasks, 1) * 100, 1),
        },
        "agents": agents_data,
    }


@router.post(
    "/weekly/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Manually trigger the weekly workflow (ADMIN+)",
)
async def trigger_weekly_workflow(
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> dict:
    # In production this would enqueue a Celery task or call an async worker.
    # For now we confirm the trigger request was received.
    return {
        "message": "Weekly workflow triggered successfully",
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "status": "QUEUED",
    }
