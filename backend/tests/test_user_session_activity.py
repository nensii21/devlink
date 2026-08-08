"""
Unit & Integration Tests for User Session Activity (#588)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.refresh_token_service import RefreshTokenService


def _make_mock_user() -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.username = "sessionuser"
    u.email = "sessionuser@example.com"
    return u


def _make_mock_session(user_id: uuid.UUID, device_name: str = "MacBook Pro", is_current: bool = False) -> MagicMock:
    s = MagicMock(spec=RefreshToken)
    s.id = uuid.uuid4()
    s.user_id = user_id
    s.token = f"refreshtoken-{uuid.uuid4()}"
    s.device_name = device_name
    s.device_type = "Laptop"
    s.browser = "Chrome 124"
    s.operating_system = "macOS 14.4"
    s.ip_address = "192.168.1.100"
    s.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    s.is_revoked = False
    s.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    s.last_used_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    s.expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    s.is_current = is_current
    return s


class TestUserSessionActivity:
    def test_get_active_sessions_returns_user_device_metadata(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        sess1 = _make_mock_session(user_id=user.id, device_name="MacBook Pro", is_current=True)
        sess2 = _make_mock_session(user_id=user.id, device_name="iPhone 15", is_current=False)

        db.scalars.return_value = [sess1, sess2]

        sessions = RefreshTokenService.get_active_sessions(db, user_id=user.id)

        assert len(sessions) == 2
        assert sessions[0].device_name == "MacBook Pro"
        assert sessions[1].device_name == "iPhone 15"

    def test_revoke_individual_session_by_id(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        session = _make_mock_session(user_id=user.id, device_name="Old Tablet")

        db.scalar.return_value = session

        success = RefreshTokenService.revoke_session_by_id(db, session_id=session.id, user_id=user.id)

        assert success is True
        assert session.is_revoked is True
        assert session.revoked_at is not None

    def test_revoke_other_sessions_keeps_current(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        current_sess = _make_mock_session(user_id=user.id, device_name="Current Desktop", is_current=True)
        other_sess1 = _make_mock_session(user_id=user.id, device_name="Laptop", is_current=False)
        other_sess2 = _make_mock_session(user_id=user.id, device_name="Phone", is_current=False)

        db.scalars.return_value = [other_sess1, other_sess2]

        count = RefreshTokenService.revoke_other_sessions(
            db=db, user_id=user.id, current_session_id=current_sess.id
        )

        assert count == 2
        assert other_sess1.is_revoked is True
        assert other_sess2.is_revoked is True
        assert current_sess.is_revoked is False

    def test_revoke_all_sessions(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        sess1 = _make_mock_session(user_id=user.id, device_name="Desktop 1")
        sess2 = _make_mock_session(user_id=user.id, device_name="Desktop 2")

        db.scalars.return_value = [sess1, sess2]

        RefreshTokenService.revoke_all_tokens(db, user_id=user.id)

        assert sess1.is_revoked is True
        assert sess2.is_revoked is True
