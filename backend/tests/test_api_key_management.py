"""
Unit & Integration Tests for API Key Management for Third-Party Integrations (#605)
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyUpdateRequest
from app.services.api_key_service import ApiKeyService
from app.services.audit_log_service import AuditLogService


def _make_mock_user(username: str = "apikeyuser") -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.username = username
    u.is_superuser = False
    return u


class TestApiKeyManagement:
    def test_create_api_key_hashes_secret_and_returns_raw_once(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        payload = ApiKeyCreateRequest(
            name="CI/CD Integration Key",
            scopes=["read:projects", "write:projects"],
            expires_in_days=30,
        )

        with patch.object(AuditLogService, "create_log") as mock_audit:
            raw_key, api_key = ApiKeyService.create_api_key(
                db=db, actor=user, payload=payload
            )

            assert raw_key.startswith("dlk_live_")
            assert api_key.name == "CI/CD Integration Key"
            assert api_key.prefix.startswith("dlk_live_")
            # Verify SHA-256 hash in DB match raw_key
            # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
            expected_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
            assert api_key.hashed_key == expected_hash
            assert api_key.scopes == ["read:projects", "write:projects"]
            assert api_key.expires_at is not None
            mock_audit.assert_called_once()
            assert mock_audit.call_args.kwargs["action"] == AuditAction.API_KEY_CREATED

    def test_list_api_keys_paginated(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        key1 = MagicMock(spec=ApiKey)
        key1.name = "Key 1"
        key2 = MagicMock(spec=ApiKey)
        key2.name = "Key 2"

        db.scalar.return_value = 2
        db.scalars.return_value = [key1, key2]

        res = ApiKeyService.list_api_keys(db, user_id=user.id, page=1, limit=10)

        assert res["total"] == 2
        assert len(res["items"]) == 2

    def test_update_api_key_scopes_and_name(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        existing_key = MagicMock(spec=ApiKey)
        existing_key.id = uuid.uuid4()
        existing_key.user_id = user.id
        existing_key.name = "Old Name"
        existing_key.scopes = ["read:projects"]
        existing_key.organization_id = None

        db.get.return_value = existing_key

        update_payload = ApiKeyUpdateRequest(
            name="New Updated Name",
            scopes=["read:projects", "read:profile"],
        )

        with patch.object(AuditLogService, "create_log") as mock_audit:
            updated = ApiKeyService.update_api_key(
                db=db, key_id=existing_key.id, payload=update_payload, actor=user
            )

            assert updated.name == "New Updated Name"
            assert updated.scopes == ["read:projects", "read:profile"]
            mock_audit.assert_called_once()
            assert mock_audit.call_args.kwargs["action"] == AuditAction.API_KEY_UPDATED

    def test_regenerate_api_key_returns_new_raw_secret(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        existing_key = MagicMock(spec=ApiKey)
        existing_key.id = uuid.uuid4()
        existing_key.user_id = user.id
        existing_key.name = "Prod Key"
        existing_key.hashed_key = "oldhash"
        existing_key.organization_id = None

        db.get.return_value = existing_key

        with patch.object(AuditLogService, "create_log") as mock_audit:
            new_raw_key, regenerated = ApiKeyService.regenerate_api_key(
                db=db, key_id=existing_key.id, actor=user
            )

            assert new_raw_key.startswith("dlk_live_")
            # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
            assert (
                regenerated.hashed_key
                == hashlib.sha256(new_raw_key.encode("utf-8")).hexdigest()
            )
            assert regenerated.last_used_at is None
            mock_audit.assert_called_once()
            assert (
                mock_audit.call_args.kwargs["action"] == AuditAction.API_KEY_REGENERATED
            )

    def test_revoke_api_key_sets_inactive(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        existing_key = MagicMock(spec=ApiKey)
        existing_key.id = uuid.uuid4()
        existing_key.user_id = user.id
        existing_key.is_active = True
        existing_key.organization_id = None

        db.get.return_value = existing_key

        with patch.object(AuditLogService, "create_log") as mock_audit:
            revoked = ApiKeyService.revoke_api_key(
                db=db, key_id=existing_key.id, actor=user
            )

            assert revoked.is_active is False
            mock_audit.assert_called_once()
            assert mock_audit.call_args.kwargs["action"] == AuditAction.API_KEY_REVOKED

    def test_authenticate_api_key_validates_token_and_updates_last_used_at(self):
        db = MagicMock(spec=Session)
        raw_key = "dlk_live_validsecrettoken12345"
        # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
        hashed = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        key = MagicMock(spec=ApiKey)
        key.hashed_key = hashed
        key.is_active = True
        key.expires_at = datetime.now(timezone.utc) + timedelta(days=5)
        key.scopes = ["read:projects", "write:projects"]

        db.scalar.return_value = key

        authenticated = ApiKeyService.authenticate_api_key(
            db, raw_key=raw_key, required_scope="read:projects"
        )

        assert authenticated == key
        assert authenticated.last_used_at is not None

    def test_authenticate_api_key_raises_401_on_expired_or_invalid_key(self):
        db = MagicMock(spec=Session)

        # Invalid key case
        db.scalar.return_value = None
        with pytest.raises(HTTPException) as exc1:
            ApiKeyService.authenticate_api_key(db, raw_key="dlk_live_invalid")
        assert exc1.value.status_code == 401

        # Expired key case
        expired_key = MagicMock(spec=ApiKey)
        expired_key.is_active = True
        expired_key.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.scalar.return_value = expired_key

        with pytest.raises(HTTPException) as exc2:
            ApiKeyService.authenticate_api_key(db, raw_key="dlk_live_expired")
        assert exc2.value.status_code == 401

    def test_authenticate_api_key_raises_403_on_insufficient_scope(self):
        db = MagicMock(spec=Session)
        key = MagicMock(spec=ApiKey)
        key.is_active = True
        key.expires_at = None
        key.scopes = ["read:profile"]

        db.scalar.return_value = key

        with pytest.raises(HTTPException) as exc:
            ApiKeyService.authenticate_api_key(
                db, raw_key="dlk_live_test", required_scope="write:projects"
            )
        assert exc.value.status_code == 403
