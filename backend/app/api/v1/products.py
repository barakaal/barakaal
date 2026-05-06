import csv
import io
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.product import Product, ProductStatus, ProductTrend
from app.models.supplier import SupplierOffer
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.product import ProductCreate, ProductOut, ProductTrendOut, ProductUpdate
from app.schemas.supplier import SupplierOfferOut

router = APIRouter()


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedResponse[ProductOut], summary="List products with filters")
async def list_products(
    product_status: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PaginatedResponse[ProductOut]:
    base_query = select(Product)
    if product_status:
        base_query = base_query.where(Product.status == product_status)
    if category:
        base_query = base_query.where(Product.category == category)
    if min_score is not None:
        base_query = base_query.where(Product.score >= min_score)

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.order_by(Product.score.desc().nullslast(), Product.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    products = result.scalars().all()

    return PaginatedResponse(
        items=[ProductOut.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED, summary="Create product")
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ProductOut:
    product = Product(**product_in.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return ProductOut.model_validate(product)


@router.post("/import-csv", summary="Import products from CSV file")
async def import_products_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> dict[str, Any]:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    errors: list[str] = []

    REQUIRED_FIELDS = {"name", "sku"}

    for row_num, row in enumerate(reader, start=2):  # row 1 = header
        missing = REQUIRED_FIELDS - set(row.keys())
        if missing:
            errors.append(f"Row {row_num}: missing fields {missing}")
            continue
        try:
            product = Product(
                name=row.get("name", "").strip(),
                sku=row.get("sku", "").strip(),
                description=row.get("description", "").strip(),
                category=row.get("category", "").strip() or None,
                cost_price=float(row["cost_price"]) if row.get("cost_price") else None,
                selling_price=float(row["selling_price"]) if row.get("selling_price") else None,
                status=row.get("status", ProductStatus.ACTIVE.value),
            )
            db.add(product)
            imported += 1
        except Exception as exc:
            errors.append(f"Row {row_num}: {exc}")

    if imported > 0:
        await db.flush()

    return {"imported": imported, "errors": errors}


# ---------------------------------------------------------------------------
# Item routes
# ---------------------------------------------------------------------------

@router.get("/{product_id}", response_model=ProductOut, summary="Get product by ID")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ProductOut:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductOut.model_validate(product)


@router.put("/{product_id}", response_model=ProductOut, summary="Update product")
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ProductOut:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return ProductOut.model_validate(product)


@router.delete("/{product_id}", summary="Delete product")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> dict:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await db.delete(product)
    return {"message": f"Product {product_id} deleted successfully"}


@router.get("/{product_id}/trends", response_model=list[ProductTrendOut], summary="Get product trends")
async def get_product_trends(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[ProductTrendOut]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    trends_result = await db.execute(
        select(ProductTrend)
        .where(ProductTrend.product_id == product_id)
        .order_by(ProductTrend.recorded_at.desc())
        .limit(90)
    )
    return [ProductTrendOut.model_validate(t) for t in trends_result.scalars().all()]


@router.get("/{product_id}/suppliers", response_model=list[SupplierOfferOut], summary="Get supplier offers for product")
async def get_product_suppliers(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[SupplierOfferOut]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    offers_result = await db.execute(
        select(SupplierOffer)
        .where(SupplierOffer.product_id == product_id)
        .order_by(SupplierOffer.unit_price)
    )
    return [SupplierOfferOut.model_validate(o) for o in offers_result.scalars().all()]


@router.post("/{product_id}/score", response_model=ProductOut, summary="Recalculate product score")
async def recalculate_product_score(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ProductOut:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Scoring heuristic: combine margin, demand, and competition data
    score_details: dict[str, Any] = {}
    score = 0.0

    if product.selling_price and product.cost_price and product.cost_price > 0:
        margin = (product.selling_price - product.cost_price) / product.cost_price * 100
        margin_score = min(margin / 2, 40)  # up to 40 points
        score += margin_score
        score_details["margin_pct"] = round(margin, 2)
        score_details["margin_score"] = round(margin_score, 2)

    # Count recent trends as a proxy for demand
    trends_result = await db.execute(
        select(func.count(ProductTrend.id)).where(ProductTrend.product_id == product_id)
    )
    trend_count = trends_result.scalar_one()
    demand_score = min(trend_count * 2, 30)  # up to 30 points
    score += demand_score
    score_details["trend_count"] = trend_count
    score_details["demand_score"] = round(demand_score, 2)

    # Supplier availability score
    offers_result = await db.execute(
        select(func.count(SupplierOffer.id)).where(SupplierOffer.product_id == product_id)
    )
    offer_count = offers_result.scalar_one()
    supply_score = min(offer_count * 5, 30)  # up to 30 points
    score += supply_score
    score_details["offer_count"] = offer_count
    score_details["supply_score"] = round(supply_score, 2)

    product.score = round(score, 2)
    score_details["total_score"] = product.score

    await db.flush()
    await db.refresh(product)

    out = ProductOut.model_validate(product)
    # Attach score_details as extra field if schema supports it; return as-is otherwise
    return out
