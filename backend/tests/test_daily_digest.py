from datetime import date
from unittest.mock import patch, MagicMock
from app.models.digest import UserNotificationPreference, DailyDigestLog
from app.services.digest_service import DailyDigestService
from app.tasks.digest_tasks import process_user_daily_digest


def test_digest_disabled_by_preferences():
    mock_session = MagicMock()
    disabled_pref = UserNotificationPreference(
        user_id="user_1", daily_digest_enabled=False
    )
    mock_session.get.return_value = disabled_pref

    result = DailyDigestService.aggregate_digest(
        mock_session, "user_1", date(2026, 8, 14)
    )
    assert result is None


def test_digest_deduplication_detection():
    mock_session = MagicMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = DailyDigestLog(
        user_id="user_1", digest_date=date(2026, 8, 14)
    )

    is_sent = DailyDigestService.has_digest_been_sent(
        mock_session, "user_1", date(2026, 8, 14)
    )
    assert is_sent is True


def test_task_skips_when_already_sent():
    with patch("app.tasks.digest_tasks.SessionLocal") as mock_db, patch(
        "app.services.digest_service.DailyDigestService.has_digest_been_sent",
        return_value=True,
    ):

        result = process_user_daily_digest.apply(args=["user_101", "2026-08-14"]).get()
        assert result["status"] == "SKIPPED"
        assert result["reason"] == "ALREADY_SENT"


def test_task_executes_and_delivers_successfully():
    mock_session = MagicMock()
    digest_payload = {
        "user_id": "user_101",
        "has_activity": True,
        "new_messages_count": 2,
    }

    with patch("app.tasks.digest_tasks.SessionLocal", return_value=mock_session), patch(
        "app.services.digest_service.DailyDigestService.has_digest_been_sent",
        return_value=False,
    ), patch(
        "app.services.digest_service.DailyDigestService.aggregate_digest",
        return_value=digest_payload,
    ), patch(
        "app.services.digest_service.DailyDigestService.record_digest_sent"
    ) as mock_record:

        result = process_user_daily_digest.apply(args=["user_101", "2026-08-14"]).get()
        assert result["status"] == "DELIVERED"
        assert result["user_id"] == "user_101"
        mock_record.assert_called_once()
