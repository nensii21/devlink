from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "devlink",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.celery_app.tasks.email_tasks",
        "app.celery_app.tasks.notification_tasks",
        "app.celery_app.tasks.image_tasks",
        "app.celery_app.tasks.digest_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    "send-daily-digest": {
        "task": "app.celery_app.tasks.digest_tasks.send_daily_digest",
        "schedule": crontab(hour=0, minute=0),  # Midnight UTC
        "args": (),
    },
}
