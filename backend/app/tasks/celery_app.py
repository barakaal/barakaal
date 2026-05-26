from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_dropship_os",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.weekly_workflow", "app.tasks.agent_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "weekly-product-research": {
            "task": "app.tasks.weekly_workflow.run_weekly_workflow",
            "schedule": 604800.0,  # 7 jours en secondes
            "options": {"expires": 3600},
        },
        "daily-order-check": {
            "task": "app.tasks.agent_tasks.check_pending_orders",
            "schedule": 86400.0,  # 24h
        },
        "hourly-approval-reminder": {
            "task": "app.tasks.agent_tasks.send_approval_reminders",
            "schedule": 3600.0,  # 1h
        },
    },
)
