from datetime import datetime, timezone, date
import logging
from celery.schedules import crontab

from app.core.celery_app import celery_app
from app.tasks.base import BaseTask
from app.services.digest_service import DailyDigestService
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(base=BaseTask, bind=True, name="tasks.process_user_daily_digest")
def process_user_daily_digest(self, user_id: str, target_date_str: str) -> dict:
    """Processes digest for a single user with deduplication checks."""
    target_date = date.fromisoformat(target_date_str)

    with SessionLocal() as session:
        # 1. Deduplication guard
        if DailyDigestService.has_digest_been_sent(session, user_id, target_date):
            logger.info(
                "Digest already sent to user %s for date %s. Skipping.",
                user_id,
                target_date_str,
            )
            return {"status": "SKIPPED", "reason": "ALREADY_SENT", "user_id": user_id}

        # 2. Preference and activity check
        digest_data = DailyDigestService.aggregate_digest(session, user_id, target_date)
        if not digest_data or not digest_data.get("has_activity"):
            logger.info(
                "No activity or digest disabled for user %s. Skipping.", user_id
            )
            return {
                "status": "SKIPPED",
                "reason": "NO_ACTIVITY_OR_DISABLED",
                "user_id": user_id,
            }

        # 3. Deliver digest (e.g., dispatch transactional email or in-app notification)
        logger.info(
            "Sending daily digest to user %s with %d updates", user_id, len(digest_data)
        )

        # 4. Mark as sent to prevent duplicate runs
        DailyDigestService.record_digest_sent(
            session, user_id, target_date, digest_data
        )

        return {
            "status": "DELIVERED",
            "user_id": user_id,
            "digest_date": target_date_str,
        }


@celery_app.task(base=BaseTask, name="tasks.dispatch_daily_digests")
def dispatch_daily_digests() -> dict:
    """Scheduled task that queries active users and enqueues individual digest tasks."""
    today_utc = datetime.now(timezone.utc).date()
    today_str = today_utc.isoformat()

    # In production, query user IDs in batches / via cursor
    with SessionLocal() as session:
        # Example: active_user_ids = session.scalars(select(User.id).where(User.is_active.is_(True))).all()
        active_user_ids = ["user_101", "user_102", "user_103"]

    for user_id in active_user_ids:
        process_user_daily_digest.delay(user_id=user_id, target_date_str=today_str)

    logger.info("Dispatched daily digest tasks for %d users.", len(active_user_ids))
    return {"dispatched_count": len(active_user_ids), "date": today_str}


# Configure Celery Beat schedule (Runs daily at 08:00 UTC)
celery_app.conf.beat_schedule = {
    "dispatch-daily-digest-every-morning": {
        "task": "tasks.dispatch_daily_digests",
        "schedule": crontab(hour=8, minute=0),
    },
}
