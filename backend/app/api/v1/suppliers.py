from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.supplier import Supplier, SupplierOffer
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.supplier import (
    SupplierCreate,
    SupplierOfferCreate,
    SupplierOfferOut,
    SupplierOut,
    SupplierUpdate,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[SupplierOut], summary="List suppliers")
async def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PaginatedResponse[SupplierOut]:
    total_result = await db.execute(select(func.count(Supplier.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Supplier)
        .order_by(Supplier.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    suppliers = result.scalars().all()

    return PaginatedResponse(
        items=[SupplierOut.model_validate(s) for s in suppliers],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=SupplierOut, status_code=status.HTTP_201_CREATED, summary="Create supplier")
async def create_supplier(
    supplier_in: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> SupplierOut:
    supplier = Supplier(**supplier_in.model_dump())
    db.add(supplier)
    await db.flush()
    await db.refresh(supplier)
    return SupplierOut.model_validate(supplier)


@router.post("/offers/", response_model=SupplierOfferOut, status_code=status.HTTP_201_CREATED, summary="Create supplier offer")
async def create_supplier_offer(
    offer_in: SupplierOfferCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> SupplierOfferOut:
    # Validate supplier exists
    supplier_result = await db.execute(select(Supplier).where(Supplier.id == offer_in.supplier_id))
    if supplier_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    offer = SupplierOffer(**offer_in.model_dump())
    db.add(offer)
    await db.flush()
    await db.refresh(offer)
    return SupplierOfferOut.model_validate(offer)


@router.get("/{supplier_id}", response_model=SupplierOut, summary="Get supplier by ID")
async def get_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> SupplierOut:
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return SupplierOut.model_validate(supplier)


@router.put("/{supplier_id}", response_model=SupplierOut, summary="Update supplier")
async def update_supplier(
    supplier_id: int,
    supplier_in: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> SupplierOut:
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    for field, value in supplier_in.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)

    await db.flush()
    await db.refresh(supplier)
    return SupplierOut.model_validate(supplier)


@router.delete("/{supplier_id}", summary="Delete supplier")
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> dict:
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    await db.delete(supplier)
    return {"message": f"Supplier {supplier_id} deleted successfully"}


@router.get("/{supplier_id}/offers", response_model=list[SupplierOfferOut], summary="Get offers by supplier")
async def get_supplier_offers(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[SupplierOfferOut]:
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    offers_result = await db.execute(
        select(SupplierOffer)
        .where(SupplierOffer.supplier_id == supplier_id)
        .order_by(SupplierOffer.unit_price)
    )
    return [SupplierOfferOut.model_validate(o) for o in offers_result.scalars().all()]
