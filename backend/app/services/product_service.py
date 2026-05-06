from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductStatus, ProductTrend
from app.services.product_scoring import scoring_service, ProductScoreInput

logger = logging.getLogger(__name__)


async def get_products(
    db: AsyncSession,
    filters: dict = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Product], int]:
    """
    Retourne une page de produits avec le total.

    Filtres supportés:
      - status: str (ex: "ACTIVE", "CANDIDATE")
      - category: str
      - source_platform: str
      - min_score: float
      - max_score: float
      - search: str (recherche dans name)
    """
    filters = filters or {}
    stmt = select(Product)

    if status := filters.get("status"):
        stmt = stmt.where(Product.status == status)

    if category := filters.get("category"):
        stmt = stmt.where(Product.category.ilike(f"%{category}%"))

    if source_platform := filters.get("source_platform"):
        stmt = stmt.where(Product.source_platform == source_platform)

    if min_score := filters.get("min_score"):
        stmt = stmt.where(Product.score >= float(min_score))

    if max_score := filters.get("max_score"):
        stmt = stmt.where(Product.score <= float(max_score))

    if search := filters.get("search"):
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * size
    stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    products = list(result.scalars().all())

    return products, total


async def get_product(db: AsyncSession, product_id: int) -> Optional[Product]:
    """Retourne un produit par ID, ou None si non trouvé."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: dict) -> Product:
    """
    Crée un nouveau produit en base de données.

    Champs attendus dans data:
      - name (str, requis)
      - category (str, requis)
      - description (str)
      - tags (list[str])
      - source_platform (str)
      - source_url (str)
      - images (list[str])
      - cost_price_usd (float)
      - status (str, défaut: CANDIDATE)
    """
    product = Product(
        name=data["name"],
        description=data.get("description", ""),
        category=data.get("category", ""),
        tags=data.get("tags", []),
        source_platform=data.get("source_platform", ""),
        source_url=data.get("source_url"),
        images=data.get("images", []),
        status=data.get("status", ProductStatus.CANDIDATE.value),
        cost_price_usd=data.get("cost_price_usd"),
        selling_price_usd=data.get("selling_price_usd"),
        gross_margin_pct=data.get("gross_margin_pct"),
        score=data.get("score"),
        score_details=data.get("score_details"),
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    logger.info("Created product id=%d name=%s", product.id, product.name)
    return product


async def update_product(db: AsyncSession, product_id: int, data: dict) -> Optional[Product]:
    """
    Met à jour les champs d'un produit.
    Retourne None si le produit n'existe pas.
    """
    product = await get_product(db, product_id)
    if not product:
        return None

    allowed_fields = {
        "name", "description", "category", "tags", "source_platform",
        "source_url", "images", "status", "cost_price_usd", "selling_price_usd",
        "gross_margin_pct", "score", "score_details",
    }

    for field, value in data.items():
        if field in allowed_fields and value is not None:
            setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    logger.info("Updated product id=%d", product_id)
    return product


async def calculate_product_score(db: AsyncSession, product_id: int) -> Optional[Product]:
    """
    Calcule et met à jour le score d'un produit en base.

    Utilise ProductScoringService avec les données disponibles dans:
      - Le produit lui-même (cost_price_usd)
      - Les offres fournisseurs (via supplier_offers)
      - Les tendances (via trends)

    Retourne le produit mis à jour.
    """
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Product)
        .options(selectinload(Product.supplier_offers))
        .options(selectinload(Product.trends))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        return None

    # Construire l'input de scoring depuis les données disponibles
    supplier_price = float(product.cost_price_usd or 0)
    shipping_cost = 0.0
    shipping_days_max = 30
    market_avg_price = 0.0
    demand_score = 50.0
    growth_rate_pct = 0.0
    competition_level = "MEDIUM"

    # Utiliser la meilleure offre fournisseur si disponible
    if product.supplier_offers:
        best_offer = min(
            product.supplier_offers,
            key=lambda o: float(o.unit_price_usd or 999999),
        )
        supplier_price = float(best_offer.unit_price_usd or supplier_price)
        shipping_cost = float(best_offer.shipping_cost_usd or 0)
        shipping_days_max = best_offer.shipping_days_max or 30

    # Utiliser la dernière tendance si disponible
    if product.trends:
        latest_trend = max(product.trends, key=lambda t: t.created_at)
        demand_score = float(latest_trend.trend_score or 50)
        growth_rate_pct = float(latest_trend.growth_rate_pct or 0)
        market_avg_price = float(latest_trend.avg_market_price_usd or 0)
        competition_level = latest_trend.competition_level or "MEDIUM"

    inp = ProductScoreInput(
        demand_score=demand_score,
        growth_rate_pct=growth_rate_pct,
        supplier_price_usd=supplier_price,
        shipping_cost_usd=shipping_cost,
        market_avg_price_usd=market_avg_price,
        shipping_days_max=shipping_days_max,
        competition_level=competition_level,
    )

    score_result = scoring_service.calculate(inp)
    score_dict = scoring_service.score_to_dict(score_result)

    product.score = score_result.score_final
    product.score_details = score_dict
    product.selling_price_usd = score_result.recommended_selling_price_usd
    product.gross_margin_pct = score_result.gross_margin_pct

    await db.commit()
    await db.refresh(product)
    logger.info(
        "Calculated score for product id=%d: %.1f (%s)",
        product_id,
        score_result.score_final,
        score_result.verdict,
    )
    return product


async def import_products_from_csv(
    db: AsyncSession, products: list[dict]
) -> tuple[int, list[str]]:
    """
    Importe une liste de produits depuis un CSV parsé.

    Retourne (nombre_importés, liste_erreurs).
    Ignore les doublons (même name + source_platform).
    """
    imported = 0
    errors = []

    for idx, product_data in enumerate(products):
        try:
            # Vérifier si le produit existe déjà
            existing = await db.execute(
                select(Product).where(
                    Product.name == product_data.get("name", ""),
                    Product.source_platform == product_data.get("source_platform", "CSV_IMPORT"),
                )
            )
            if existing.scalar_one_or_none():
                logger.debug("Skipping duplicate product: %s", product_data.get("name"))
                continue

            product = Product(
                name=product_data["name"],
                description=product_data.get("description", ""),
                category=product_data.get("category", ""),
                tags=product_data.get("tags", []),
                source_platform=product_data.get("source_platform", "CSV_IMPORT"),
                source_url=product_data.get("source_url"),
                images=product_data.get("images", []),
                status=product_data.get("status", ProductStatus.CANDIDATE.value),
                cost_price_usd=product_data.get("cost_price_usd"),
            )
            db.add(product)
            imported += 1

        except KeyError as e:
            errors.append(f"Product #{idx + 1}: missing required field {e}")
        except Exception as e:
            errors.append(f"Product #{idx + 1}: {str(e)}")

    if imported > 0:
        await db.commit()
        logger.info("Imported %d products from CSV", imported)

    return imported, errors


async def update_product_status(
    db: AsyncSession, product_id: int, new_status: str, reason: str = ""
) -> Optional[Product]:
    """
    Met à jour le statut d'un produit avec validation de la transition.

    Transitions autorisées:
      CANDIDATE -> UNDER_REVIEW -> APPROVED -> ACTIVE
      ACTIVE -> PAUSED -> ACTIVE
      ACTIVE | PAUSED -> DISCONTINUED
      CANDIDATE | UNDER_REVIEW -> REJECTED
    """
    valid_statuses = {s.value for s in ProductStatus}
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}")

    product = await get_product(db, product_id)
    if not product:
        return None

    old_status = product.status
    product.status = new_status
    await db.commit()
    await db.refresh(product)

    logger.info(
        "Product id=%d status changed: %s -> %s (reason: %s)",
        product_id,
        old_status,
        new_status,
        reason or "N/A",
    )
    return product
