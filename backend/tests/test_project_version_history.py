"""
Unit & Integration Tests for Project Version History (#606)
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.project_version_service import ProjectVersionService


def _make_mock_user(username: str = "versionowner") -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.username = username
    u.is_superuser = False
    return u


def _make_mock_project(owner_id: uuid.UUID) -> MagicMock:
    p = MagicMock(spec=Project)
    p.id = uuid.uuid4()
    p.owner_id = owner_id
    p.title = "Original Project Title"
    p.tagline = "Original Tagline"
    p.description = "Original project description text."
    p.tech_stack = "React, FastAPI"
    p.requirements = "Requirement 1: Python 3.13"
    p.language = "Python"
    p.experience = "Intermediate"
    p.stage = ProjectStage.IDEA
    p.visibility = ProjectVisibility.PUBLIC
    return p


class TestProjectVersionHistory:
    def test_create_version_snapshots_project_details(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)

        db.scalar.return_value = 0  # No existing versions -> max version is 0
        db.scalars.return_value = []

        with patch.object(AuditLogService, "create_log") as mock_audit:
            ver = ProjectVersionService.create_version(
                db=db,
                project=project,
                actor_id=user.id,
                change_summary="Initial version snapshot",
            )

            assert ver.version_number == 1
            assert ver.title == "Original Project Title"
            assert ver.tech_stack == "React, FastAPI"
            assert ver.requirements == "Requirement 1: Python 3.13"
            db.add.assert_called_once()
            mock_audit.assert_called_once()
            assert (
                mock_audit.call_args.kwargs["action"]
                == AuditAction.PROJECT_VERSION_CREATED
            )

    def test_list_versions_paginated(self):
        db = MagicMock(spec=Session)
        project_id = uuid.uuid4()
        project = MagicMock(spec=Project)
        db.get.return_value = project

        v1 = MagicMock(spec=ProjectVersion)
        v1.version_number = 2
        v2 = MagicMock(spec=ProjectVersion)
        v2.version_number = 1

        db.scalar.return_value = 2
        db.scalars.return_value = [v1, v2]

        res = ProjectVersionService.list_versions(
            db, project_id=project_id, page=1, limit=10
        )

        assert res["total"] == 2
        assert len(res["items"]) == 2
        assert res["items"][0].version_number == 2

    def test_compare_versions_computes_field_diff(self):
        db = MagicMock(spec=Session)
        project_id = uuid.uuid4()
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)
        db.get.return_value = project

        v1 = MagicMock(spec=ProjectVersion)
        v1.version_number = 1
        v1.title = "Old Title"
        v1.tagline = "Original Tagline"
        v1.description = "Old description"
        v1.tech_stack = "React"
        v1.requirements = "Old Req"
        v1.language = "Python"
        v1.experience = "Intermediate"
        v1.stage = "idea"
        v1.visibility = "public"
        v1.team_roles = []

        db.scalar.return_value = v1
        db.scalars.return_value = []

        res = ProjectVersionService.compare_versions(
            db, project_id=project_id, v1_identifier="1", v2_identifier="current"
        )

        assert res["v1_version_number"] == 1
        assert res["v2_version_number"] == "current"
        diff = res["diff"]
        assert "title" in diff
        assert diff["title"]["old"] == "Old Title"
        assert diff["title"]["new"] == "Original Project Title"

    def test_restore_version_reverts_project_state_and_logs_audit(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)
        db.get.return_value = project

        v1 = MagicMock(spec=ProjectVersion)
        v1.version_number = 1
        v1.title = "Restored Title"
        v1.tagline = "Restored Tagline"
        v1.description = "Restored Description"
        v1.tech_stack = "Vue, Django"
        v1.requirements = "Restored Requirements"
        v1.language = "Python"
        v1.experience = "Senior"
        v1.stage = "mvp"
        v1.visibility = "public"

        db.scalar.side_effect = lambda *args, **kwargs: 1 if "max" in str(args) else v1
        db.scalars.return_value = []

        with patch.object(AuditLogService, "create_log") as mock_audit:
            restored = ProjectVersionService.restore_version(
                db=db,
                project_id=project.id,
                version_identifier="1",
                actor_user=user,
            )

            assert restored.title == "Restored Title"
            assert restored.description == "Restored Description"
            assert restored.tech_stack == "Vue, Django"
            assert restored.requirements == "Restored Requirements"
            mock_audit.assert_called()
            # Verify AuditAction.PROJECT_VERSION_RESTORED was logged
            audit_actions = [
                call.kwargs["action"] for call in mock_audit.call_args_list
            ]
            assert AuditAction.PROJECT_VERSION_RESTORED in audit_actions
