from app.tasks.celery_app import celery_app
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.agent_tasks.check_pending_orders")
def check_pending_orders():
    """Vérifie les commandes en attente et met à jour les statuts."""
    logger.info("Checking pending orders...")
    try:
        asyncio.run(_check_orders_async())
    except Exception as e:
        logger.error(f"Order check failed: {e}")


async def _check_orders_async():
    from app.core.database import AsyncSessionLocal
    from app.models.order import Order, OrderStatus
    from sqlalchemy import select, and_
    from datetime import timedelta

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(
                and_(
                    Order.status == OrderStatus.PROCESSING,
                    Order.created_at < datetime.utcnow() - timedelta(days=1),
                )
            )
        )
        orders = result.scalars().all()
        logger.info(f"Found {len(orders)} orders to check")
        # TODO: Appeler l'API fournisseur pour récupérer les mises à jour de statut
        # et mettre à jour chaque commande en base de données.


@celery_app.task(name="app.tasks.agent_tasks.send_approval_reminders")
def send_approval_reminders():
    """Envoie des rappels pour les approbations en attente depuis plus de 2h."""
    logger.info("Checking pending approvals...")
    asyncio.run(_check_approvals_async())


async def _check_approvals_async():
    from app.core.database import AsyncSessionLocal
    from app.models.audit import Approval
    from sqlalchemy import select, and_
    from datetime import timedelta

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Approval).where(
                and_(
                    Approval.status == "PENDING",
                    Approval.created_at < datetime.utcnow() - timedelta(hours=2),
                )
            )
        )
        pending = result.scalars().all()
        logger.info(f"Found {len(pending)} pending approvals needing attention")
        # TODO: Envoyer des notifications (email, Slack, etc.) pour les approbations en attente
        # Le canal de notification est configurable via les settings.


@celery_app.task(name="app.tasks.agent_tasks.run_product_scoring_batch")
def run_product_scoring_batch():
    """Recalcule les scores de tous les produits CANDIDATE en batch."""
    logger.info("Starting batch product scoring...")
    try:
        asyncio.run(_score_products_async())
    except Exception as e:
        logger.error(f"Batch scoring failed: {e}")


async def _score_products_async():
    from app.core.database import AsyncSessionLocal
    from app.models.product import Product, ProductStatus
    from app.services.product_service import calculate_product_score
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Product.id).where(Product.status == ProductStatus.CANDIDATE.value)
        )
        product_ids = [row[0] for row in result.all()]
        logger.info(f"Scoring {len(product_ids)} candidate products")

        scored = 0
        failed = 0
        for product_id in product_ids:
            try:
                await calculate_product_score(db, product_id)
                scored += 1
            except Exception as e:
                logger.error(f"Failed to score product {product_id}: {e}")
                failed += 1

        logger.info(f"Batch scoring complete: {scored} scored, {failed} failed")
