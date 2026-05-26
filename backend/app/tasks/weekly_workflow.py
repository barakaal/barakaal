from app.tasks.celery_app import celery_app
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.weekly_workflow.run_weekly_workflow",
    max_retries=3,
)
def run_weekly_workflow(self):
    """Tâche Celery qui lance le workflow de recherche hebdomadaire."""
    logger.info(f"Starting weekly workflow at {datetime.utcnow()}")
    try:
        result = asyncio.run(_run_workflow_async())
        return {"status": "completed", "timestamp": datetime.utcnow().isoformat(), **result}
    except Exception as exc:
        logger.error(f"Weekly workflow failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


async def _run_workflow_async():
    """Version async du workflow."""
    from app.workflows.weekly_research import WeeklyResearchWorkflow
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        workflow = WeeklyResearchWorkflow(db)
        return await workflow.run()
