from unittest.mock import patch
from app.tasks.email_tasks import send_welcome_email


def test_task_execution_success():
    result = send_welcome_email.apply(args=["user@example.com", "John Doe"]).get()
    assert result["status"] == "SENT"
    assert result["email"] == "user@example.com"


def test_task_retry_and_failure():
    with patch(
        "app.tasks.email_tasks.logger.info",
        side_effect=ConnectionError("Gateway timeout"),
    ):
        task_res = send_welcome_email.apply(args=["user@example.com", "John Doe"])
        # Verify that task entered failure/retry path
        assert task_res.failed()
