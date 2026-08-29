from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "devlink",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.notification_tasks",
        "app.tasks.email_tasks",
        "app.tasks.digest_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    # Reliability & Execution Controls
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
)

import logging

logger = logging.getLogger(__name__)

# Register Celery signals for job monitoring
from celery.signals import (
    before_task_publish,
    task_prerun,
    task_success,
    task_failure,
    task_retry,
)


@before_task_publish.connect
def on_task_publish(sender=None, headers=None, body=None, **kwargs):
    from app.database.session import SessionLocal
    from app.models.background_job import BackgroundJob, JobStatus

    info = headers or {}
    task_id = info.get("id")
    task_name = info.get("task") or sender
    if not task_id:
        return

    args, kwargs_dict, embed = body or ((), {}, {})
    payload = {"args": list(args), "kwargs": kwargs_dict}

    db = SessionLocal()
    try:
        job = db.get(BackgroundJob, task_id)
        if not job:
            job = BackgroundJob(
                id=task_id,
                task_name=task_name,
                status=JobStatus.PENDING,
                payload=payload,
                queue=info.get("queue") or "default",
            )
            db.add(job)
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error on task publish signal: {e}")
    finally:
        db.close()


@task_prerun.connect
def on_task_prerun(task_id, task, args, kwargs, **kwargs_extra):
    from app.database.session import SessionLocal
    from app.models.background_job import BackgroundJob, JobStatus
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        job = db.get(BackgroundJob, task_id)
        payload = {"args": list(args), "kwargs": kwargs}
        if not job:
            job = BackgroundJob(
                id=task_id,
                task_name=task.name,
                payload=payload,
                queue="default",
            )
            db.add(job)
        else:
            job.payload = payload

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.worker = task.request.hostname or "unknown"
        job.retries = task.request.retries or 0
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error on task prerun signal: {e}")
    finally:
        db.close()


@task_success.connect
def on_task_success(sender, result, **kwargs):
    from app.database.session import SessionLocal
    from app.models.background_job import BackgroundJob, JobStatus
    from datetime import datetime, timezone

    task_id = sender.request.id
    if not task_id:
        return

    db = SessionLocal()
    try:
        job = db.get(BackgroundJob, task_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.result = {"result": result}
            if job.started_at:
                started_at = job.started_at
                completed_at = job.completed_at
                if started_at.tzinfo is None and completed_at.tzinfo is not None:
                    completed_at = completed_at.replace(tzinfo=None)
                elif started_at.tzinfo is not None and completed_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=None)
                job.processing_time = (completed_at - started_at).total_seconds()
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error on task success signal: {e}")
    finally:
        db.close()


@task_failure.connect
def on_task_failure(task_id, exception, traceback, sender, **kwargs):
    from app.database.session import SessionLocal
    from app.models.background_job import BackgroundJob, JobStatus
    from datetime import datetime, timezone

    if not task_id:
        return

    db = SessionLocal()
    try:
        job = db.get(BackgroundJob, task_id)
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.error = f"{type(exception).__name__}: {str(exception)}\n\nTraceback:\n{traceback}"
            if job.started_at:
                started_at = job.started_at
                completed_at = job.completed_at
                if started_at.tzinfo is None and completed_at.tzinfo is not None:
                    completed_at = completed_at.replace(tzinfo=None)
                elif started_at.tzinfo is not None and completed_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=None)
                job.processing_time = (completed_at - started_at).total_seconds()
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error on task failure signal: {e}")
    finally:
        db.close()


@task_retry.connect
def on_task_retry(uuid, exception, traceback, sender, **kwargs):
    from app.database.session import SessionLocal
    from app.models.background_job import BackgroundJob, JobStatus

    if not uuid:
        return

    db = SessionLocal()
    try:
        job = db.get(BackgroundJob, uuid)
        if job:
            job.status = JobStatus.RETRY
            job.retries = sender.request.retries or (job.retries + 1)
            job.error = f"Retry: {type(exception).__name__}: {str(exception)}"
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error on task retry signal: {e}")
    finally:
        db.close()
