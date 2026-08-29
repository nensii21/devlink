"""
Backup & Restore Service (Issue #635)
======================================

Provides secure, versioned backup/restore of a user's DevLink data.

Backup format
─────────────
A JSON object written to an in-memory BytesIO buffer, optionally compressed
as a .zip archive for download.

  {
    "metadata": { version, backup_id, created_at, app_name, user_id, username },
    "checksum": "<sha256 of JSON-serialised data section>",
    "data": { … UserExportData … }
  }

Security
────────
* The checksum prevents tampering: if the data section is modified after
  export, the restore endpoint rejects the file.
* No sensitive credentials (passwords, MFA secrets) are included in the
  backup payload.
* Restored items are *merged*, not destructive – existing records are
  never deleted.

Restore scope
─────────────
Currently restored:
  - Profile fields (bio, headline, location, website, etc.)
  - Bookmarks (re-created if the project still exists)
  - Skills (user-skill association re-created)

Items NOT restored (by design):
  - Messages (privacy / conversation ownership)
  - Notifications (ephemeral)
  - Connections / followers (social graph is live data)
  - Organizations (require separate owner transfer flow)
"""

from __future__ import annotations

import hashlib
import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.bookmark import Bookmark
from app.models.project import Project
from app.models.skill import Skill
from app.models.user import User
from app.models.user_skill import UserSkill
from app.schemas.backup import (
    BackupCreateResponse,
    BackupMetadata,
    BackupPayload,
    RestoreResponse,
    RestoreValidationError,
    RestoreValidationResponse,
)
from app.services.export_service import ExportService

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sha256(text: str) -> str:
    # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
    return hashlib.sha256(text.encode()).hexdigest()


def _serialize_export_data(data: Any) -> dict:
    """Convert a UserExportData pydantic model to a JSON-serialisable dict."""
    return json.loads(data.model_dump_json())


# ---------------------------------------------------------------------------
# BackupService
# ---------------------------------------------------------------------------


class BackupService:
    """
    High-level service for creating and restoring user data backups.
    """

    BACKUP_VERSION = "1.0"
    SUPPORTED_VERSIONS = {"1.0"}

    # ------------------------------------------------------------------ #
    #  CREATE BACKUP                                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def create_backup(
        cls, db: Session, user: User
    ) -> tuple[BackupCreateResponse, bytes]:
        """
        Collect all user data, build a signed backup payload, and return:
          - a BackupCreateResponse (API response body)
          - raw bytes of the zipped backup file (for streaming download)
        """
        export_data = ExportService.collect_user_data(db, user)
        data_dict = _serialize_export_data(export_data)
        data_json = json.dumps(data_dict, sort_keys=True, default=str)
        checksum = _sha256(data_json)

        now = datetime.now(timezone.utc)
        backup_id = str(uuid.uuid4())

        metadata = BackupMetadata(
            version=cls.BACKUP_VERSION,
            backup_id=backup_id,
            created_at=now,
            user_id=str(user.id),
            username=user.username,
        )

        payload = BackupPayload(
            metadata=metadata,
            checksum=checksum,
            data=data_dict,
        )

        zip_bytes = cls._build_zip(payload, backup_id)

        response = BackupCreateResponse(
            backup_id=backup_id,
            created_at=now,
            message="Backup created successfully. Use GET /me/backup/{backup_id} to download.",
        )

        return response, zip_bytes

    @classmethod
    def _build_zip(cls, payload: BackupPayload, backup_id: str) -> bytes:
        """Serialise the payload to JSON and wrap it in a ZIP archive."""
        payload_json = payload.model_dump_json(indent=2)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"devlink_backup_{backup_id}.json", payload_json)
        buffer.seek(0)
        return buffer.read()

    # ------------------------------------------------------------------ #
    #  VALIDATE BACKUP                                                     #
    # ------------------------------------------------------------------ #

    @classmethod
    def validate_backup(cls, payload: dict) -> RestoreValidationResponse:
        """
        Validate the structure and integrity of an uploaded backup payload.
        Returns a RestoreValidationResponse with any errors found.
        """
        errors: list[RestoreValidationError] = []

        # Check top-level keys
        for key in ("metadata", "checksum", "data"):
            if key not in payload:
                errors.append(
                    RestoreValidationError(
                        field=key,
                        message=f"Required field '{key}' is missing from backup.",
                    )
                )

        if errors:
            return RestoreValidationResponse(valid=False, errors=errors)

        # Version check
        version = payload["metadata"].get("version")
        if version not in cls.SUPPORTED_VERSIONS:
            errors.append(
                RestoreValidationError(
                    field="metadata.version",
                    message=f"Unsupported backup version '{version}'. Supported: {cls.SUPPORTED_VERSIONS}",
                )
            )

        # Checksum integrity check
        data_section = payload.get("data", {})
        data_json = json.dumps(data_section, sort_keys=True, default=str)
        expected_checksum = _sha256(data_json)
        actual_checksum = payload.get("checksum", "")

        if expected_checksum != actual_checksum:
            errors.append(
                RestoreValidationError(
                    field="checksum",
                    message="Checksum mismatch. The backup file may have been tampered with.",
                )
            )

        return RestoreValidationResponse(valid=len(errors) == 0, errors=errors)

    # ------------------------------------------------------------------ #
    #  RESTORE BACKUP                                                      #
    # ------------------------------------------------------------------ #

    @classmethod
    def restore_backup(cls, db: Session, user: User, payload: dict) -> RestoreResponse:
        """
        Apply a validated backup payload to the current user's account.

        Restore strategy (non-destructive merge):
          1. Profile fields – update mutable profile fields if provided.
          2. Bookmarks – re-create any bookmarks whose projects still exist.
          3. Skills – re-create user-skill associations that no longer exist.

        Returns a RestoreResponse with counts of restored items.
        """
        validation = cls.validate_backup(payload)
        if not validation.valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            raise ValueError(f"Invalid backup: {error_msgs}")

        data = payload["data"]
        restored: dict[str, int] = {}

        # 1. Profile
        profile_count = cls._restore_profile(db, user, data.get("profile", {}))
        restored["profile_fields"] = profile_count

        # 2. Bookmarks
        bookmark_count = cls._restore_bookmarks(db, user, data.get("bookmarks", []))
        restored["bookmarks"] = bookmark_count

        # 3. Skills
        skill_count = cls._restore_skills(db, user, data.get("skills", []))
        restored["skills"] = skill_count

        db.commit()

        return RestoreResponse(
            success=True,
            message="Backup restored successfully.",
            restored=restored,
        )

    # ------------------------------------------------------------------ #
    #  Private restore helpers                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _restore_profile(db: Session, user: User, profile: dict) -> int:
        """Update mutable profile fields. Returns number of fields updated."""
        RESTORABLE_FIELDS = [
            "headline",
            "bio",
            "location",
            "timezone",
            "website",
            "portfolio_url",
            "public_email",
            "github_url",
            "linkedin_url",
            "company",
            "experience_level",
            "open_to_work",
        ]
        updated = 0
        for field in RESTORABLE_FIELDS:
            if field in profile and profile[field] is not None:
                current_val = getattr(user, field, None)
                new_val = profile[field]
                if current_val != new_val:
                    setattr(user, field, new_val)
                    updated += 1
        db.add(user)
        return updated

    @staticmethod
    def _restore_bookmarks(db: Session, user: User, bookmarks: list[dict]) -> int:
        """Re-create bookmarks for projects that still exist. Returns count created."""
        if not bookmarks:
            return 0

        # Get existing bookmark project_ids for this user
        existing = {
            str(b.project_id)
            for b in db.query(Bookmark).filter(Bookmark.user_id == user.id).all()
        }

        created = 0
        for bk in bookmarks:
            project_id_str = bk.get("project_id")
            if not project_id_str or project_id_str in existing:
                continue
            try:
                project_id = uuid.UUID(project_id_str)
            except (ValueError, AttributeError):
                continue

            # Only restore if project still exists in DB
            project = db.get(Project, project_id)
            if project is None:
                continue

            new_bookmark = Bookmark(
                id=uuid.uuid4(),
                user_id=user.id,
                project_id=project_id,
            )
            db.add(new_bookmark)
            existing.add(project_id_str)
            created += 1

        return created

    @staticmethod
    def _restore_skills(db: Session, user: User, skills: list[dict]) -> int:
        """Re-create user-skill associations that no longer exist. Returns count created."""
        if not skills:
            return 0

        # Get existing skill ids for this user
        existing_skill_ids = {
            str(us.skill_id)
            for us in db.query(UserSkill).filter(UserSkill.user_id == user.id).all()
        }

        created = 0
        for sk in skills:
            skill_id_str = str(sk.get("id", ""))
            if not skill_id_str or skill_id_str in existing_skill_ids:
                continue
            try:
                skill_id = uuid.UUID(skill_id_str)
            except (ValueError, AttributeError):
                continue

            # Only restore if skill still exists in DB
            skill = db.get(Skill, skill_id)
            if skill is None:
                continue

            new_us = UserSkill(
                id=uuid.uuid4(),
                user_id=user.id,
                skill_id=skill_id,
            )
            db.add(new_us)
            existing_skill_ids.add(skill_id_str)
            created += 1

        return created

    # ------------------------------------------------------------------ #
    #  PREVIEW RESTORE                                                     #
    # ------------------------------------------------------------------ #

    @classmethod
    def preview_restore(cls, payload: dict) -> dict[str, Any]:
        """
        Return a preview of what would be restored without making DB changes.
        """
        data = payload.get("data", {})
        meta = payload.get("metadata", {})
        return {
            "backup_id": meta.get("backup_id", "unknown"),
            "created_at": meta.get("created_at"),
            "username": meta.get("username"),
            "records": {
                "profile_fields": len(data.get("profile", {})),
                "projects": len(data.get("projects", [])),
                "skills": len(data.get("skills", [])),
                "bookmarks": len(data.get("bookmarks", [])),
                "messages": len(data.get("messages", [])),
                "connections": len(data.get("connections", [])),
                "organizations": len(data.get("organizations", [])),
                "applications": len(data.get("applications", [])),
                "activities": len(data.get("activities", [])),
                "notifications": len(data.get("notifications", [])),
                "builder_flares": len(data.get("builder_flares", [])),
            },
        }
