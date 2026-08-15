"""
Unit & Integration Tests for Secure Account Recovery Flow (#587)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.refresh_token_service import RefreshTokenService


def _make_mock_user(email: str = "recoveryuser@example.com") -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.username = "recoveryuser"
    u.email = email
    u.password_hash = "$2b$12$eImiTXuWVxfM37uY4JANjO5E/0bQn6a9x/p4K3S5s5L3f.fakehash"
    return u


class TestSecureAccountRecovery:
    def test_forgot_password_generates_token_and_logs_audit(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        db.scalar.return_value = user

        auth_service = AuthService(db)

        with (
            patch.object(EmailService, "send_notification_email") as mock_email,
            patch.object(AuditLogService, "create_log") as mock_audit,
        ):
            res = auth_service.forgot_password(
                "recoveryuser@example.com", ip_address="127.0.0.1"
            )

            assert res["success"] is True
            assert "password reset link has been sent" in res["message"]
            db.add.assert_called_once()  # Token record added
            mock_email.assert_called_once()
            mock_audit.assert_called_once()
            assert (
                mock_audit.call_args.kwargs["action"]
                == AuditAction.PASSWORD_RESET_REQUESTED
            )

    def test_forgot_password_prevents_email_enumeration(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None  # User not found

        auth_service = AuthService(db)

        res = auth_service.forgot_password("nonexistent@example.com")

        assert res["success"] is True
        assert "password reset link has been sent" in res["message"]

    def test_verify_recovery_token_status(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        t_rec = MagicMock(spec=PasswordResetToken)
        t_rec.is_used = False
        t_rec.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        db.get.return_value = user
        db.scalar.return_value = t_rec

        auth_service = AuthService(db)

        token = "fake.valid.jwt"
        with patch(
            "app.services.auth_service.decode_token",
            return_value={
                "sub": str(user.id),
                "type": "reset_password",
                "jti": "jti123",
                "hash_frag": user.password_hash[-10:],
            },
        ):
            res = auth_service.verify_recovery_token(token)

            assert res["valid"] is True
            assert res["email"] == user.email

    def test_reset_password_success_flow(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        t_rec = MagicMock(spec=PasswordResetToken)
        t_rec.is_used = False
        t_rec.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        db.get.return_value = user
        db.scalar.return_value = t_rec

        auth_service = AuthService(db)
        auth_service.get_current_user = MagicMock(return_value=user)
        auth_service._is_password_reused = MagicMock(return_value=False)
        auth_service._save_password_history = MagicMock()

        token = "fake.valid.jwt"
        with (
            patch(
                "app.services.auth_service.decode_token",
                return_value={
                    "sub": str(user.id),
                    "type": "reset_password",
                    "jti": "jti123",
                    "hash_frag": user.password_hash[-10:],
                },
            ),
            patch.object(
                RefreshTokenService, "revoke_all_tokens"
            ) as mock_revoke_sessions,
            patch.object(AuditLogService, "create_log") as mock_audit,
        ):
            res = auth_service.reset_password(
                token=token, new_password="NewSecurePassword123!"
            )

            assert res["success"] is True
            assert t_rec.is_used is True
            assert t_rec.used_at is not None
            mock_revoke_sessions.assert_called_once_with(db, user.id)
            mock_audit.assert_called_once()
            assert (
                mock_audit.call_args.kwargs["action"]
                == AuditAction.PASSWORD_RESET_COMPLETED
            )

    def test_reset_password_rejects_reused_single_use_token(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        t_rec = MagicMock(spec=PasswordResetToken)
        t_rec.is_used = True  # Token already used!
        t_rec.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        db.get.return_value = user
        db.scalar.return_value = t_rec

        auth_service = AuthService(db)
        auth_service.get_current_user = MagicMock(return_value=user)

        token = "fake.used.jwt"
        with patch(
            "app.services.auth_service.decode_token",
            return_value={
                "sub": str(user.id),
                "type": "reset_password",
                "jti": "jti123",
                "hash_frag": user.password_hash[-10:],
            },
        ):
            with pytest.raises(HTTPException) as exc:
                auth_service.reset_password(
                    token=token, new_password="NewSecurePassword123!"
                )

            assert exc.value.status_code == 400
            assert "already been used" in exc.value.detail

    def test_reset_password_rejects_expired_token(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        t_rec = MagicMock(spec=PasswordResetToken)
        t_rec.is_used = False
        t_rec.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired!

        db.get.return_value = user
        db.scalar.return_value = t_rec

        auth_service = AuthService(db)
        auth_service.get_current_user = MagicMock(return_value=user)

        token = "fake.expired.jwt"
        with patch(
            "app.services.auth_service.decode_token",
            return_value={
                "sub": str(user.id),
                "type": "reset_password",
                "jti": "jti123",
                "hash_frag": user.password_hash[-10:],
            },
        ):
            with pytest.raises(HTTPException) as exc:
                auth_service.reset_password(
                    token=token, new_password="NewSecurePassword123!"
                )

            assert exc.value.status_code == 400
            assert "expired" in exc.value.detail
