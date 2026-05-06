from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.order import Customer, Order, OrderStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.order import (
    CustomerCreate,
    CustomerOut,
    OrderCreate,
    OrderOut,
    OrderStatusUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Customer routes (before /customers/{id} to avoid route conflicts)
# ---------------------------------------------------------------------------

@router.get("/customers/", response_model=PaginatedResponse[CustomerOut], summary="List customers")
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PaginatedResponse[CustomerOut]:
    total_result = await db.execute(select(func.count(Customer.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Customer)
        .order_by(Customer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    customers = result.scalars().all()

    return PaginatedResponse(
        items=[CustomerOut.model_validate(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/customers/", response_model=CustomerOut, status_code=status.HTTP_201_CREATED, summary="Create customer")
async def create_customer(
    customer_in: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> CustomerOut:
    # Check for duplicate email
    if customer_in.email:
        existing = await db.execute(select(Customer).where(Customer.email == customer_in.email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer with this email already exists")

    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    return CustomerOut.model_validate(customer)


@router.get("/customers/{customer_id}", response_model=CustomerOut, summary="Get customer with orders")
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> CustomerOut:
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerOut.model_validate(customer)


# ---------------------------------------------------------------------------
# Order routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedResponse[OrderOut], summary="List orders with filters")
async def list_orders(
    order_status: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PaginatedResponse[OrderOut]:
    base_query = select(Order)
    if order_status:
        base_query = base_query.where(Order.status == order_status)
    if customer_id:
        base_query = base_query.where(Order.customer_id == customer_id)
    if date_from:
        base_query = base_query.where(func.date(Order.created_at) >= date_from)
    if date_to:
        base_query = base_query.where(func.date(Order.created_at) <= date_to)

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    orders = result.scalars().all()

    return PaginatedResponse(
        items=[OrderOut.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED, summary="Create order")
async def create_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> OrderOut:
    # Validate customer exists
    if order_in.customer_id:
        customer_result = await db.execute(select(Customer).where(Customer.id == order_in.customer_id))
        if customer_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    order = Order(**order_in.model_dump(), status=OrderStatus.PENDING.value)
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return OrderOut.model_validate(order)


@router.get("/{order_id}", response_model=OrderOut, summary="Get order by ID")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> OrderOut:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderOut.model_validate(order)


@router.put("/{order_id}/status", response_model=OrderOut, summary="Update order status")
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> OrderOut:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order.status = status_update.status
    if hasattr(status_update, "tracking_number") and status_update.tracking_number:
        order.tracking_number = status_update.tracking_number

    await db.flush()
    await db.refresh(order)
    return OrderOut.model_validate(order)


@router.get("/{order_id}/tracking", summary="Get order tracking info")
async def get_order_tracking(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    tracking_number = getattr(order, "tracking_number", None)
    tracking_url: Optional[str] = None

    if tracking_number:
        # Generic tracking URL — in production this would branch per carrier
        tracking_url = f"https://track.example.com/{tracking_number}"

    return {
        "order_id": order.id,
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "status": order.status,
        "estimated_delivery": getattr(order, "estimated_delivery", None),
    }
