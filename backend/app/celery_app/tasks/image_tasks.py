import logging
from app.celery_app.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=120)
def process_image_upload(self, image_url: str, sizes: list[str]):
    """
    Task to download, resize, and re-upload images asynchronously.
    """
    try:
        logger.info(f"Starting image processing for {image_url}")
        # Placeholder for image processing logic (e.g. Pillow thumbnail generation)
        # ...
        logger.info(f"Image processing completed for {image_url}")
    except Exception as exc:
        logger.error(f"Failed to process image {image_url}: {exc}")
        # Use exponential backoff for heavier tasks
        raise self.retry(exc=exc, countdown=2**self.request.retries * 60)
