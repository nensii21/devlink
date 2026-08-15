"""
Unit & Integration Tests for Notification Preferences Center (#586)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.notification import NotificationPreference
from app.models.user import User
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.services.notification_service import NotificationService


def _make_mock_user() -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.username = "testprefuser"
    return u


def _make_mock_preference(user_id: uuid.UUID) -> MagicMock:
    pref = MagicMock(spec=NotificationPreference)
    pref.id = uuid.uuid4()
    pref.user_id = user_id
    pref.email_enabled = True
    pref.websocket_enabled = True
    pref.database_enabled = True
    pref.messages = True
    pref.team_invitations = True
    pref.project_updates = True
    pref.mentions = True
    pref.system_announcements = True
    pref.email_messages = True
    pref.email_team_invitations = True
    pref.email_project_updates = True
    pref.email_mentions = True
    pref.email_system_announcements = True
    pref.invitations = True
    pref.role_changes = True
    pref.marketing_emails = False
    pref.system_alerts = True
    pref.updated_at = datetime.now(timezone.utc)
    return pref


class TestNotificationPreferencesService:
    def test_get_preferences_existing(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        existing_pref = _make_mock_preference(user.id)
        db.scalar.return_value = existing_pref

        result = NotificationService.get_preferences(db, user.id)

        assert result.user_id == user.id
        assert result.messages is True
        assert result.team_invitations is True
        assert result.project_updates is True
        assert result.mentions is True
        assert result.system_announcements is True

    def test_get_preferences_creates_default_if_none(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        db.scalar.return_value = None

        result = NotificationService.get_preferences(db, user.id)

        assert result.user_id == user.id
        assert result.email_enabled is True
        assert result.messages is True
        assert result.team_invitations is True
        assert result.project_updates is True
        assert result.mentions is True
        assert result.system_announcements is True
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_update_preferences_persists_settings(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        existing_pref = _make_mock_preference(user.id)
        db.scalar.return_value = existing_pref

        update_payload = NotificationPreferenceUpdate(
            email_enabled=False,
            messages=False,
            email_messages=False,
            team_invitations=True,
            project_updates=False,
            mentions=True,
            system_announcements=True,
        )

        result = NotificationService.update_preferences(
            db, user_id=user.id, update_in=update_payload
        )

        assert result.email_enabled is False
        assert result.messages is False
        assert result.email_messages is False
        assert result.project_updates is False
        assert result.mentions is True
        db.commit.assert_called()

    def test_preference_pydantic_schema_validation(self):
        user_id = uuid.uuid4()
        pref_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": pref_id,
            "user_id": user_id,
            "email_enabled": True,
            "websocket_enabled": True,
            "database_enabled": True,
            "messages": False,
            "team_invitations": True,
            "project_updates": True,
            "mentions": False,
            "system_announcements": True,
            "email_messages": False,
            "email_team_invitations": True,
            "email_project_updates": True,
            "email_mentions": False,
            "email_system_announcements": True,
            "invitations": True,
            "role_changes": True,
            "marketing_emails": False,
            "system_alerts": True,
            "updated_at": now,
        }

        resp = NotificationPreferenceResponse.model_validate(data)
        assert resp.id == pref_id
        assert resp.messages is False
        assert resp.mentions is False
        assert resp.team_invitations is True
