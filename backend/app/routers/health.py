import time

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
import redis as redis_lib

from app.core.config import settings
from app.database.database import engine

router = APIRouter(prefix="/health", tags=["Health"])


def _check_database() -> dict:
    try:
        start = time.monotonic()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "latency_ms": round((time.monotonic() - start) * 1000, 2),
        }
    except Exception:
        return {"status": "unhealthy", "error": "Database connection failed"}


def _check_redis() -> dict:
    try:
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        try:
            start = time.monotonic()
            r.ping()
            return {
                "status": "healthy",
                "latency_ms": round((time.monotonic() - start) * 1000, 2),
            }
        finally:
            r.close()
    except Exception:
        return {"status": "unhealthy", "error": "Redis connection failed"}


def _check_celery() -> dict:
    try:
        from app.core.celery_app import celery_app
    except ImportError:
        return {"status": "disabled"}

    try:
        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active()
        if active is None:
            return {"status": "no_workers"}
        return {"status": "healthy", "workers": len(active)}
    except Exception:
        return {"status": "unhealthy", "error": "Celery unable to connect to workers"}


@router.get("/ready", summary="Readiness health check")
async def health_ready():
    db = _check_database()
    redis = _check_redis()
    celery = _check_celery()

    all_healthy = db["status"] == "healthy" and redis["status"] == "healthy"
    http_status = (
        status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=http_status,
        content={
            "status": "healthy" if all_healthy else "degraded",
            "environment": settings.ENVIRONMENT,
            "services": {
                "database": db,
                "redis": redis,
                "celery": celery,
            },
        },
    )
