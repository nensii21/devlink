from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
import sqlalchemy as sa
from typing import Optional

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.background_job import BackgroundJob, JobStatus
from app.core.celery_app import celery_app


def check_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


router = APIRouter(
    prefix="/admin/background-jobs",
    tags=["Admin Background Jobs"],
    dependencies=[Depends(check_admin)],
)


@router.get("/stats")
def get_job_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(BackgroundJob.id))) or 0
    running = (
        db.scalar(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.status == JobStatus.RUNNING
            )
        )
        or 0
    )
    completed = (
        db.scalar(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.status == JobStatus.COMPLETED
            )
        )
        or 0
    )
    failed = (
        db.scalar(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.status == JobStatus.FAILED
            )
        )
        or 0
    )
    pending = (
        db.scalar(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.status.in_([JobStatus.PENDING, JobStatus.RETRY])
            )
        )
        or 0
    )

    # Calculate average processing time
    avg_processing_time = (
        db.scalar(
            select(func.avg(BackgroundJob.processing_time)).where(
                BackgroundJob.status == JobStatus.COMPLETED
            )
        )
        or 0.0
    )

    # Worker health
    try:
        inspect = celery_app.control.inspect(timeout=1.0)
        if inspect is None:
            worker_health = {"status": "no_workers", "workers": {}}
        else:
            active = inspect.active() or {}
            ping = inspect.ping() or {}
            reserved = inspect.reserved() or {}
            stats = inspect.stats() or {}

            workers_info = {}
            for w in active.keys():
                workers_info[w] = {
                    "status": "active" if ping.get(w) else "offline",
                    "active_tasks": len(active.get(w, [])),
                    "queued_tasks": len(reserved.get(w, [])),
                    "total_processed": stats.get(w, {})
                    .get("total", {})
                    .get("notifications.send", 0),
                }

            worker_health = {
                "status": "healthy" if len(workers_info) > 0 else "no_workers",
                "workers": workers_info,
            }
    except Exception as e:
        worker_health = {"status": "unhealthy", "error": str(e), "workers": {}}

    return {
        "total": total,
        "running": running,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "avg_processing_time": round(float(avg_processing_time), 3),
        "worker_health": worker_health,
    }


@router.get("/")
def get_jobs(
    status: Optional[JobStatus] = None,
    task_name: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    stmt = select(BackgroundJob)

    if status:
        stmt = stmt.where(BackgroundJob.status == status)
    if task_name:
        stmt = stmt.where(BackgroundJob.task_name == task_name)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            or_(
                BackgroundJob.id.ilike(search_filter),
                BackgroundJob.task_name.ilike(search_filter),
                BackgroundJob.error.ilike(search_filter),
                func.cast(BackgroundJob.payload, sa.Text).ilike(search_filter),
                func.cast(BackgroundJob.result, sa.Text).ilike(search_filter),
            )
        )

    stmt = stmt.order_by(BackgroundJob.created_at.desc()).offset(skip).limit(limit)
    jobs = list(db.scalars(stmt))

    count_stmt = select(func.count(BackgroundJob.id))
    if status:
        count_stmt = count_stmt.where(BackgroundJob.status == status)
    if task_name:
        count_stmt = count_stmt.where(BackgroundJob.task_name == task_name)
    if search:
        search_filter = f"%{search}%"
        count_stmt = count_stmt.where(
            or_(
                BackgroundJob.id.ilike(search_filter),
                BackgroundJob.task_name.ilike(search_filter),
                BackgroundJob.error.ilike(search_filter),
                func.cast(BackgroundJob.payload, sa.Text).ilike(search_filter),
                func.cast(BackgroundJob.result, sa.Text).ilike(search_filter),
            )
        )
    total_count = db.scalar(count_stmt) or 0

    return {"jobs": jobs, "total": total_count, "skip": skip, "limit": limit}


@router.post("/{job_id}/retry")
def retry_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(BackgroundJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found",
        )

    job.status = JobStatus.PENDING
    job.error = None
    job.result = None
    job.completed_at = None
    job.started_at = None
    db.commit()

    payload = job.payload or {}
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})

    try:
        task = celery_app.tasks.get(job.task_name)
        if task:
            task.apply_async(args=args, kwargs=kwargs, task_id=job.id)
        else:
            celery_app.send_task(
                name=job.task_name,
                args=args,
                kwargs=kwargs,
                task_id=job.id,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry job: {str(e)}",
        )

    return {"status": "retrying", "job_id": job_id}
