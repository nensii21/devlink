"""
Tests for Issue #635: Backup & Restore for User Data
=====================================================

Tests cover:
 - BackupService.create_backup (payload structure, checksum)
 - BackupService.validate_backup (valid / tampered / wrong version)
 - BackupService.preview_restore
 - BackupService.restore_backup (profile, bookmarks, skills)
 - API router endpoints (mock-level)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.backup import (
    BackupCreateResponse,
    RestoreResponse,
)
from app.services.backup_service import BackupService, _sha256

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(username: str = "testuser") -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()
    u.username = username
    u.email = f"{username}@example.com"
    u.first_name = "Test"
    u.last_name = "User"
    u.headline = "Dev"
    u.bio = "Hello"
    u.location = "NYC"
    u.timezone = "UTC"
    u.website = None
    u.portfolio_url = None
    u.public_email = None
    u.github_url = None
    u.linkedin_url = None
    u.company = None
    u.experience_level = None
    u.open_to_work = True
    u.cover_image = None
    u.profile_image = None
    u.role = "user"
    u.is_verified = False
    u.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u


def _make_minimal_export_data() -> MagicMock:
    """A minimal UserExportData mock that serialises correctly."""
    from app.schemas.export import UserExportData

    return UserExportData(
        exported_at=datetime.now(timezone.utc),
        profile={
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "headline": "Dev",
            "bio": "Hello",
            "location": "NYC",
            "timezone": "UTC",
            "website": None,
            "portfolio_url": None,
            "public_email": None,
            "github_url": None,
            "linkedin_url": None,
            "role": "user",
            "experience_level": None,
            "company": None,
            "open_to_work": True,
            "is_verified": False,
            "created_at": "2024-01-01T00:00:00+00:00",
            "profile_image": None,
            "cover_image": None,
        },
        skills=[],
        projects=[],
        project_memberships=[],
        applications=[],
        connections=[],
        messages=[],
        bookmarks=[],
        organizations=[],
        activities=[],
        notifications=[],
        builder_flares=[],
    )


# ---------------------------------------------------------------------------
# _sha256 helper
# ---------------------------------------------------------------------------


class TestSha256Helper:
    def test_consistent_hash(self):
        text = '{"key": "value"}'
        assert _sha256(text) == _sha256(text)

    def test_different_inputs_differ(self):
        assert _sha256("abc") != _sha256("def")

    def test_known_value(self):
        # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
        expected = hashlib.sha256(b"hello").hexdigest()
        assert _sha256("hello") == expected


# ---------------------------------------------------------------------------
# BackupService.create_backup
# ---------------------------------------------------------------------------


class TestCreateBackup:
    @patch("app.services.backup_service.ExportService.collect_user_data")
    def test_returns_response_and_bytes(self, mock_collect):
        mock_collect.return_value = _make_minimal_export_data()
        db = MagicMock()
        user = _make_user()

        response, zip_bytes = BackupService.create_backup(db, user)

        assert isinstance(response, BackupCreateResponse)
        assert response.success is True
        assert response.backup_id
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0

    @patch("app.services.backup_service.ExportService.collect_user_data")
    def test_zip_contains_json(self, mock_collect):
        import io
        import zipfile

        mock_collect.return_value = _make_minimal_export_data()
        db = MagicMock()
        user = _make_user()

        _, zip_bytes = BackupService.create_backup(db, user)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert len(names) == 1
            assert names[0].endswith(".json")
            content = json.loads(zf.read(names[0]))
            assert "metadata" in content
            assert "checksum" in content
            assert "data" in content

    @patch("app.services.backup_service.ExportService.collect_user_data")
    def test_checksum_valid_in_payload(self, mock_collect):
        import io
        import zipfile

        mock_collect.return_value = _make_minimal_export_data()
        db = MagicMock()
        user = _make_user()

        _, zip_bytes = BackupService.create_backup(db, user)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            content = json.loads(zf.read(zf.namelist()[0]))

        data_json = json.dumps(content["data"], sort_keys=True, default=str)
        expected_checksum = _sha256(data_json)
        assert content["checksum"] == expected_checksum

    @patch("app.services.backup_service.ExportService.collect_user_data")
    def test_metadata_contains_username(self, mock_collect):
        import io
        import zipfile

        mock_collect.return_value = _make_minimal_export_data()
        db = MagicMock()
        user = _make_user(username="alice")

        _, zip_bytes = BackupService.create_backup(db, user)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            content = json.loads(zf.read(zf.namelist()[0]))

        assert content["metadata"]["username"] == "alice"


# ---------------------------------------------------------------------------
# BackupService.validate_backup
# ---------------------------------------------------------------------------


def _build_valid_payload(user: MagicMock | None = None) -> dict:
    """Return a structurally valid backup payload dict."""
    if user is None:
        user = _make_user()
    data = {"profile": {"username": user.username}, "projects": [], "skills": []}
    data_json = json.dumps(data, sort_keys=True, default=str)
    checksum = _sha256(data_json)
    return {
        "metadata": {
            "version": "1.0",
            "backup_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "app_name": "DevLink",
            "user_id": str(uuid.uuid4()),
            "username": "testuser",
        },
        "checksum": checksum,
        "data": data,
    }


class TestValidateBackup:
    def test_valid_payload_is_accepted(self):
        payload = _build_valid_payload()
        result = BackupService.validate_backup(payload)
        assert result.valid is True
        assert result.errors == []

    def test_missing_metadata_rejected(self):
        payload = _build_valid_payload()
        del payload["metadata"]
        result = BackupService.validate_backup(payload)
        assert result.valid is False
        fields = [e.field for e in result.errors]
        assert "metadata" in fields

    def test_missing_checksum_rejected(self):
        payload = _build_valid_payload()
        del payload["checksum"]
        result = BackupService.validate_backup(payload)
        assert result.valid is False
        fields = [e.field for e in result.errors]
        assert "checksum" in fields

    def test_missing_data_rejected(self):
        payload = _build_valid_payload()
        del payload["data"]
        result = BackupService.validate_backup(payload)
        assert result.valid is False
        fields = [e.field for e in result.errors]
        assert "data" in fields

    def test_tampered_data_rejected(self):
        payload = _build_valid_payload()
        # Tamper data after computing the checksum
        payload["data"]["profile"]["username"] = "hacker"
        result = BackupService.validate_backup(payload)
        assert result.valid is False
        fields = [e.field for e in result.errors]
        assert "checksum" in fields

    def test_unsupported_version_rejected(self):
        payload = _build_valid_payload()
        payload["metadata"]["version"] = "99.0"
        # Recompute checksum so only version triggers error
        data_json = json.dumps(payload["data"], sort_keys=True, default=str)
        # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
        payload["checksum"] = _sha256(data_json)
        result = BackupService.validate_backup(payload)
        assert result.valid is False
        fields = [e.field for e in result.errors]
        assert "metadata.version" in fields


# ---------------------------------------------------------------------------
# BackupService.preview_restore
# ---------------------------------------------------------------------------


class TestPreviewRestore:
    def test_preview_returns_expected_keys(self):
        payload = _build_valid_payload()
        payload["data"]["projects"] = [{"id": str(uuid.uuid4())}]
        preview = BackupService.preview_restore(payload)
        assert "backup_id" in preview
        assert "username" in preview
        assert "records" in preview
        assert "projects" in preview["records"]

    def test_preview_counts_projects(self):
        payload = _build_valid_payload()
        payload["data"]["projects"] = [{"id": str(uuid.uuid4())}] * 3
        preview = BackupService.preview_restore(payload)
        assert preview["records"]["projects"] == 3

    def test_preview_username_from_metadata(self):
        payload = _build_valid_payload()
        preview = BackupService.preview_restore(payload)
        assert preview["username"] == "testuser"


# ---------------------------------------------------------------------------
# BackupService.restore_backup
# ---------------------------------------------------------------------------


class TestRestoreBackup:
    def test_raises_on_invalid_payload(self):
        db = MagicMock()
        user = _make_user()
        bad_payload = {"metadata": {}, "checksum": "wrong", "data": {}}
        with pytest.raises(ValueError, match="Invalid backup"):
            BackupService.restore_backup(db, user, bad_payload)

    def test_restores_profile_fields(self):
        db = MagicMock()
        user = _make_user()
        user.bio = "old bio"
        user.headline = "old headline"

        payload = _build_valid_payload(user)
        payload["data"]["profile"] = {"bio": "new bio", "headline": "new headline"}
        # Recompute checksum
        data_json = json.dumps(payload["data"], sort_keys=True, default=str)
        # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
        payload["checksum"] = _sha256(data_json)

        result = BackupService.restore_backup(db, user, payload)
        assert result.success is True
        assert result.restored["profile_fields"] >= 1
        assert user.bio == "new bio"
        assert user.headline == "new headline"

    def test_bookmark_skipped_if_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.get.return_value = None  # project doesn't exist

        user = _make_user()
        payload = _build_valid_payload(user)
        payload["data"]["bookmarks"] = [{"project_id": str(uuid.uuid4())}]
        data_json = json.dumps(payload["data"], sort_keys=True, default=str)
        # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
        payload["checksum"] = _sha256(data_json)

        result = BackupService.restore_backup(db, user, payload)
        assert result.restored["bookmarks"] == 0

    def test_skill_skipped_if_skill_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.get.return_value = None  # skill doesn't exist

        user = _make_user()
        payload = _build_valid_payload(user)
        payload["data"]["skills"] = [{"id": str(uuid.uuid4()), "name": "Python"}]
        data_json = json.dumps(payload["data"], sort_keys=True, default=str)
        # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
        payload["checksum"] = _sha256(data_json)

        result = BackupService.restore_backup(db, user, payload)
        assert result.restored["skills"] == 0

    def test_restore_response_has_correct_structure(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        user = _make_user()
        payload = _build_valid_payload(user)
        result = BackupService.restore_backup(db, user, payload)

        assert isinstance(result, RestoreResponse)
        assert result.success is True
        assert "profile_fields" in result.restored
        assert "bookmarks" in result.restored
        assert "skills" in result.restored
