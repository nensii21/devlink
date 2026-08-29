import logging
from celery import Task

logger = logging.getLogger("celery.tasks")


class BaseTask(Task):
    """
    Standard base task with exponential backoff retries,
    structured lifecycle logging, and custom failure reporting.
    """

    # Automatic retry configuration
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True  # Exponential backoff (e.g., 2s, 4s, 8s, 16s...)
    retry_backoff_max = 600  # Cap backoff delay at 10 minutes
    retry_jitter = True  # Prevent thundering herds

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when the task has exhausted all retries or failed fatally."""
        logger.error(
            "Task failed fatally | Task: %s | ID: %s | Error: %s",
            self.name,
            task_id,
            exc,
            exc_info=einfo,
        )
        # Optional: Dispatch alert to Sentry, PagerDuty, or push to dead-letter queue
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when a task is scheduled for a retry."""
        logger.warning(
            "Retrying task | Task: %s | ID: %s | Attempt: %s/%s | Reason: %s",
            self.name,
            task_id,
            self.request.retries + 1,
            self.retry_kwargs.get("max_retries", self.max_retries),
            exc,
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Called upon successful task completion."""
        logger.info(
            "Task completed successfully | Task: %s | ID: %s", self.name, task_id
        )
        super().on_success(retval, task_id, args, kwargs)
