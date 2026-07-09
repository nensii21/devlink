from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "devlink",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.notification_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,
    task_soft_time_limit=45,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
)