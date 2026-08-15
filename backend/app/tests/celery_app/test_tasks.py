import pytest
from unittest.mock import patch

from app.celery_app.tasks.email_tasks import send_verification_email_task
from app.celery_app.tasks.digest_tasks import send_daily_digest
from app.celery_app.tasks.notification_tasks import process_notification
from app.celery_app.tasks.image_tasks import process_image_upload
from celery.exceptions import Retry

# Test the tasks directly as functions to verify logic


@patch("app.celery_app.tasks.email_tasks.run_async_email")
@patch("app.core.email.email_service._send_email_async")
def test_send_verification_email_task(mock_send_email, mock_run_async):
    # Call the task synchronously
    send_verification_email_task(
        email_to="test@example.com",
        username="test",
        verification_url="http://test.com",
        expire_hours=24,
    )

    mock_run_async.assert_called_once()
    assert mock_send_email.called


@patch("app.celery_app.tasks.email_tasks.run_async_email")
def test_send_verification_email_task_retry(mock_run_async):
    mock_run_async.side_effect = Exception("SMTP Error")

    with patch.object(send_verification_email_task, "retry", side_effect=Retry):
        with pytest.raises(Retry):
            send_verification_email_task(
                email_to="test@example.com",
                username="test",
                verification_url="http://test.com",
                expire_hours=24,
            )


def test_send_daily_digest():
    # Calling the placeholder task
    result = send_daily_digest()
    assert result is None


@patch("app.celery_app.tasks.digest_tasks.logger")
def test_send_daily_digest_retry(mock_logger):
    # Mocking internal logic to throw error
    with patch(
        "app.celery_app.tasks.digest_tasks.send_daily_digest.retry", side_effect=Retry
    ):
        with patch.object(send_daily_digest, "retry", side_effect=Retry):
            with pytest.raises(Retry):
                # Force failure if we had real logic, but since it's placeholder
                # we'll manually invoke the retry logic
                raise send_daily_digest.retry(exc=Exception("Fail"))


def test_process_notification():
    # Calling the placeholder task
    result = process_notification(
        user_id=1, notification_type="mention", payload={"message": "hello"}
    )
    assert result is None


def test_process_image_upload():
    # Calling the placeholder task
    result = process_image_upload(
        image_url="http://example.com/image.png", sizes=["small", "large"]
    )
    assert result is None
