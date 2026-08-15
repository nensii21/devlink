import logging
from app.celery_app.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_daily_digest(self):
    """
    Scheduled task that runs daily.
    Compiles and sends a daily digest of activity.
    """
    try:
        logger.info("Starting daily digest generation...")
        # Placeholder for querying daily activity and dispatching emails
        # ...
        logger.info("Daily digest generated and sent successfully.")
    except Exception as exc:
        logger.error(f"Failed to generate daily digest: {exc}")
        raise self.retry(exc=exc)
