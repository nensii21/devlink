from unittest.mock import patch, MagicMock
from app.services.email_service import EmailService
from app.services.push_service import PushNotificationService
from app.tasks.notification_tasks import send_notification_task


def test_email_service_fallback(caplog):
    """Test that email service gracefully logs when SMTP is not configured."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.SMTP_HOST = ""
        mock_settings.SMTP_PORT = 0

        result = EmailService.send_email("test@example.com", "Subject", "Body")
        assert result is True
        assert "Mock Email sent to test@example.com" in caplog.text


@patch("app.services.email_service.smtplib.SMTP")
def test_email_service_smtp(mock_smtp):
    """Test that email service attempts SMTP connection when configured."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.EMAIL_FROM = "no-reply@test.com"

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = EmailService.send_email("target@example.com", "Hello", "<html></html>")

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "password")
        mock_server.sendmail.assert_called_once()


@patch("app.services.email_service.smtplib.SMTP")
def test_email_service_failure(mock_smtp, caplog):
    """Test that email service catches SMTP exceptions."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587

        mock_smtp.side_effect = Exception("SMTP Connection Timeout")

        result = EmailService.send_email("target@example.com", "Hello", "<html></html>")

        assert result is False
        assert "Failed to send email" in caplog.text


def test_push_service_mock(caplog):
    """Test that push service mocks request correctly."""
    result = PushNotificationService.send_push(["token123"], "Title", "Body")
    assert result is True
    assert "Mock Push sent to 1 devices" in caplog.text


def test_push_service_empty():
    """Test that push service returns False if no tokens provided."""
    result = PushNotificationService.send_push([], "Title", "Body")
    assert result is False


def test_notify_user_push(caplog):
    """Test that notify_user fetches tokens and delegates."""
    with patch(
        "app.services.push_service.PushNotificationService.send_push"
    ) as mock_send:
        mock_send.return_value = True

        result = PushNotificationService.notify_user(
            "user_123", "Hello", "World", action_url="http://test.com"
        )

        assert result is True
        mock_send.assert_called_once_with(
            ["device_token_for_user_123"], "Hello", "World", {"url": "http://test.com"}
        )


@patch("app.tasks.notification_tasks.UserService.get_user")
@patch("app.tasks.notification_tasks.NotificationService.notify")
@patch("app.tasks.notification_tasks.EmailService.send_notification_email")
@patch("app.tasks.notification_tasks.PushNotificationService.notify_user")
@patch("app.tasks.notification_tasks.SessionLocal")
def test_send_notification_task_success(
    mock_session_local, mock_push, mock_email, mock_notify, mock_get_user
):
    """Test that the celery task triggers DB insert, Email, and Push notifications."""
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Mock DB notification creation
    mock_notification = MagicMock()
    mock_notification.id = "notif_123"
    mock_notify.return_value = mock_notification

    # Mock user retrieval
    mock_user = MagicMock()
    mock_user.id = "user_123"
    mock_user.email = "user@test.com"
    mock_get_user.return_value = mock_user

    payload = {
        "recipient_id": "00000000-0000-0000-0000-000000000001",
        "sender_id": None,
        "type": "application",
        "title": "Welcome",
        "message": "Hello to DevLink",
        "action_url": "http://devlink.app",
    }

    # We must patch _to_uuid which is in the same module
    with patch("app.tasks.notification_tasks._to_uuid", return_value="uuid_obj"):
        result = send_notification_task(payload)

    assert result == "notif_123"
    mock_notify.assert_called_once()
    mock_email.assert_called_once_with(
        to_email="user@test.com",
        title="Welcome",
        message="Hello to DevLink",
        action_url="http://devlink.app",
    )
    mock_push.assert_called_once_with(
        user_id="user_123",
        title="Welcome",
        body="Hello to DevLink",
        action_url="http://devlink.app",
    )
    mock_db.close.assert_called_once()
