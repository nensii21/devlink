import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import redis as redis_lib
from fastapi import APIRouter, Header, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.database.database import engine

router = APIRouter(prefix="/health", tags=["Health"])

START_MONOTONIC = time.monotonic()
START_TIME = datetime.now(timezone.utc)


def _format_uptime(seconds: float) -> str:
    total_seconds = int(seconds)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 or days > 0 or hours > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    return ", ".join(parts)


def _check_uptime() -> dict:
    elapsed_seconds = round(time.monotonic() - START_MONOTONIC, 2)
    return {
        "seconds": elapsed_seconds,
        "human": _format_uptime(elapsed_seconds),
        "started_at": START_TIME.isoformat(),
    }


def _check_database() -> dict:
    try:
        start = time.monotonic()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "latency_ms": round((time.monotonic() - start) * 1000, 2),
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "error": "Database connection failed",
            "detail": str(exc),
        }


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
    except Exception as exc:
        return {
            "status": "unhealthy",
            "error": "Redis connection failed",
            "detail": str(exc),
        }


def _check_ai_service() -> dict:
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return {
            "status": "unconfigured",
            "provider": "OpenAI",
            "configured": False,
            "message": "OPENAI_API_KEY is not set",
        }

    try:
        start = time.monotonic()
        # Verify OpenAI client instantiation
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        latency = round((time.monotonic() - start) * 1000, 2)
        return {
            "status": "healthy",
            "provider": "OpenAI",
            "configured": True,
            "latency_ms": latency,
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "provider": "OpenAI",
            "configured": True,
            "error": "AI service initialization failed",
            "detail": str(exc),
        }


def _check_storage() -> dict:
    upload_dir_str = getattr(settings, "UPLOAD_DIR", "uploads")
    upload_path = Path(upload_dir_str)

    try:
        upload_path.mkdir(parents=True, exist_ok=True)
        test_file = upload_path / ".health_check_tmp"
        test_file.write_text("health_check")
        test_file.unlink(missing_ok=True)
        writable = True
    except Exception:
        writable = False

    try:
        usage = shutil.disk_usage(upload_path.resolve())
        free_mb = round(usage.free / (1024 * 1024), 2)
        total_mb = round(usage.total / (1024 * 1024), 2)
        used_mb = round(usage.used / (1024 * 1024), 2)
    except Exception:
        free_mb = 0.0
        total_mb = 0.0
        used_mb = 0.0

    is_healthy = upload_path.exists() and writable

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "path": str(upload_path),
        "writable": writable,
        "free_space_mb": free_mb,
        "total_space_mb": total_mb,
        "used_space_mb": used_mb,
    }


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


def _render_html_dashboard(data: dict) -> str:
    status_color = "#10B981" if data["status"] == "healthy" else "#EF4444"
    if data["status"] == "degraded":
        status_color = "#F59E0B"

    services_html = ""
    for name, s in data["services"].items():
        srv_status = s.get("status", "unknown")
        badge_bg = (
            "#D1FAE5"
            if srv_status == "healthy"
            else (
                "#FEF3C7"
                if srv_status in ("unconfigured", "disabled", "no_workers")
                else "#FEE2E2"
            )
        )
        badge_text = (
            "#065F46"
            if srv_status == "healthy"
            else (
                "#92400E"
                if srv_status in ("unconfigured", "disabled", "no_workers")
                else "#991B1B"
            )
        )

        details = ""
        for k, v in s.items():
            if k != "status":
                details += f"<div><span style='color: #6B7280;'>{k}:</span> <strong>{v}</strong></div>"

        services_html += f"""
        <div style="background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; text-transform: capitalize; font-size: 1.1rem; color: #1F2937;">{name.replace("_", " ")}</h3>
                <span style="background: {badge_bg}; color: {badge_text}; font-weight: 600; padding: 4px 12px; border-radius: 9999px; font-size: 0.85rem; text-transform: uppercase;">
                    {srv_status}
                </span>
            </div>
            <div style="font-size: 0.9rem; color: #374151; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px;">
                {details}
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevLink System Health Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #F3F4F6; margin: 0; padding: 40px 20px; color: #111827; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ background: white; padding: 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
        .title {{ font-size: 1.5rem; font-weight: 700; margin: 0; }}
        .status-badge {{ background: {status_color}; color: white; padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 1rem; text-transform: uppercase; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .meta-card {{ background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .meta-label {{ font-size: 0.85rem; color: #6B7280; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }}
        .meta-value {{ font-size: 1.1rem; font-weight: 600; color: #111827; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 class="title">DevLink System Health Dashboard</h1>
                <p style="margin: 4px 0 0 0; color: #6B7280; font-size: 0.9rem;">Environment: <strong>{data.get("environment", "development")}</strong></p>
            </div>
            <div class="status-badge">{data["status"]}</div>
        </div>

        <div class="meta-grid">
            <div class="meta-card">
                <div class="meta-label">System Uptime</div>
                <div class="meta-value">{data["uptime"]["human"]}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Uptime Seconds</div>
                <div class="meta-value">{data["uptime"]["seconds"]}s</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Last Checked</div>
                <div class="meta-value">{data["timestamp"]}</div>
            </div>
        </div>

        <h2 style="font-size: 1.25rem; margin-bottom: 16px; color: #374151;">Service Status</h2>
        {services_html}
    </div>
</body>
</html>
"""


@router.get("/dashboard", summary="Backend Health Check Dashboard")
async def health_dashboard(
    format: str | None = Query(None, description="Set to 'html' for UI dashboard view"),
    accept: str | None = Header(None),
):
    """
    Returns full health status across all core services:
    - Database
    - Redis
    - AI Service
    - Storage
    - System Uptime
    """
    db = _check_database()
    redis = _check_redis()
    ai_service = _check_ai_service()
    storage = _check_storage()
    celery = _check_celery()
    uptime = _check_uptime()

    all_healthy = (
        db["status"] == "healthy"
        and redis["status"] == "healthy"
        and storage["status"] == "healthy"
        and ai_service["status"] in ("healthy", "unconfigured")
    )

    system_status = "healthy" if all_healthy else "degraded"
    if db["status"] == "unhealthy" and redis["status"] == "unhealthy":
        system_status = "unhealthy"

    data = {
        "status": system_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "uptime": uptime,
        "services": {
            "database": db,
            "redis": redis,
            "ai_service": ai_service,
            "storage": storage,
            "celery": celery,
        },
    }

    wants_html = format == "html" or (
        accept and "text/html" in accept and "application/json" not in accept
    )
    if wants_html:
        return HTMLResponse(content=_render_html_dashboard(data), status_code=200)

    http_status_code = (
        status.HTTP_200_OK
        if system_status in ("healthy", "degraded")
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=http_status_code, content=data)


@router.get("/ready", summary="Readiness health check")
async def health_ready():
    db = _check_database()
    redis = _check_redis()
    ai_service = _check_ai_service()
    storage = _check_storage()
    celery = _check_celery()
    uptime = _check_uptime()

    all_healthy = db["status"] == "healthy" and redis["status"] == "healthy"
    http_status = (
        status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=http_status,
        content={
            "status": "healthy" if all_healthy else "degraded",
            "environment": settings.ENVIRONMENT,
            "uptime": uptime,
            "services": {
                "database": db,
                "redis": redis,
                "ai_service": ai_service,
                "storage": storage,
                "celery": celery,
            },
        },
    )
