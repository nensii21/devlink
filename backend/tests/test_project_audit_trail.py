"""
Unit & Integration Tests for Project Audit Trail (#585)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_member import MemberRole, ProjectMember
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.project_member_service import ProjectMemberService


def _make_mock_user(username: str = "audituser") -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.username = username
    u.first_name = "Audit"
    u.last_name = "User"
    u.is_superuser = False
    return u


def _make_mock_project(owner_id: uuid.UUID) -> MagicMock:
    p = MagicMock(spec=Project)
    p.id = uuid.uuid4()
    p.owner_id = owner_id
    p.title = "Original Project Title"
    p.slug = "original-project-title"
    p.description = "Original description for project audit trail testing."
    p.stage = ProjectStage.IDEA
    p.visibility = ProjectVisibility.PUBLIC
    p.created_at = datetime.now(timezone.utc)
    return p


# ---------------------------------------------------------------------------
# 1. Project Audit Action Enum & Service Tests
# ---------------------------------------------------------------------------


class TestProjectAuditTrailActions:
    def test_audit_action_enum_values(self):
        assert AuditAction.PROJECT_CREATED.value == "project_created"
        assert AuditAction.PROJECT_TITLE_UPDATED.value == "project_title_updated"
        assert (
            AuditAction.PROJECT_DESCRIPTION_UPDATED.value
            == "project_description_updated"
        )
        assert AuditAction.PROJECT_STATUS_CHANGED.value == "project_status_changed"
        assert AuditAction.PROJECT_MEMBER_ADDED.value == "project_member_added"
        assert AuditAction.PROJECT_MEMBER_REMOVED.value == "project_member_removed"
        assert (
            AuditAction.PROJECT_MEMBER_ROLE_UPDATED.value
            == "project_member_role_updated"
        )
        assert (
            AuditAction.PROJECT_OWNERSHIP_TRANSFERRED.value
            == "project_ownership_transferred"
        )
        assert AuditAction.PROJECT_ARCHIVED.value == "project_archived"

    def test_search_project_audit_logs(self):
        db = MagicMock(spec=Session)
        project_id = uuid.uuid4()
        actor_id = uuid.uuid4()

        mock_log = MagicMock(spec=AuditLog)
        mock_log.id = uuid.uuid4()
        mock_log.project_id = project_id
        mock_log.actor_id = actor_id
        mock_log.action = AuditAction.PROJECT_TITLE_UPDATED
        mock_log.entity_type = "project"
        mock_log.entity_id = str(project_id)
        mock_log.old_values = {"title": "Old"}
        mock_log.new_values = {"title": "New"}
        mock_log.created_at = datetime.now(timezone.utc)

        db.scalar.return_value = 1
        db.scalars.return_value = [mock_log]

        result = AuditLogService.search_project_audit_logs(
            db, project_id=project_id, page=1, limit=20
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].action == AuditAction.PROJECT_TITLE_UPDATED


# ---------------------------------------------------------------------------
# 2. Member & Ownership Audit Logging Tests
# ---------------------------------------------------------------------------


class TestProjectMemberAuditLogging:
    def test_update_member_role_logs_audit_event(self):
        db = MagicMock(spec=Session)
        owner = _make_mock_user("owner")
        target_user = _make_mock_user("target")
        project = _make_mock_project(owner_id=owner.id)

        pm = MagicMock(spec=ProjectMember)
        pm.id = uuid.uuid4()
        pm.project_id = project.id
        pm.user_id = target_user.id
        pm.role = MemberRole.CONTRIBUTOR

        db.get.side_effect = lambda model, obj_id: (
            project if model == Project else target_user
        )
        db.scalar.return_value = pm

        with patch.object(AuditLogService, "create_log") as mock_create_log:
            res = ProjectMemberService.update_member_role(
                db=db,
                project_id=project.id,
                target_user_id=target_user.id,
                new_role=MemberRole.MAINTAINER,
                actor_user=owner,
            )

            assert res.role == MemberRole.MAINTAINER
            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["action"] == AuditAction.PROJECT_MEMBER_ROLE_UPDATED
            assert call_kwargs["project_id"] == project.id
            assert call_kwargs["target_user_id"] == target_user.id

    def test_transfer_ownership_logs_audit_event(self):
        db = MagicMock(spec=Session)
        current_owner = _make_mock_user("owner1")
        new_owner = _make_mock_user("owner2")
        project = _make_mock_project(owner_id=current_owner.id)

        db.get.side_effect = lambda model, obj_id: (
            project if model == Project else new_owner
        )
        db.scalar.return_value = None

        with patch.object(AuditLogService, "create_log") as mock_create_log:
            updated_proj = ProjectMemberService.transfer_ownership(
                db=db,
                project_id=project.id,
                new_owner_id=new_owner.id,
                current_owner=current_owner,
            )

            assert updated_proj.owner_id == new_owner.id
            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["action"] == AuditAction.PROJECT_OWNERSHIP_TRANSFERRED
            assert call_kwargs["target_user_id"] == new_owner.id

    def test_remove_member_logs_audit_event(self):
        db = MagicMock(spec=Session)
        owner = _make_mock_user("owner")
        target_user = _make_mock_user("target")
        project = _make_mock_project(owner_id=owner.id)
        pm = MagicMock(spec=ProjectMember)

        db.get.return_value = project
        db.scalar.return_value = pm

        with patch.object(AuditLogService, "create_log") as mock_create_log:
            ProjectMemberService.remove_member(
                db=db,
                project_id=project.id,
                target_user_id=target_user.id,
                actor_user=owner,
            )

            mock_create_log.assert_called_once()
            call_kwargs = mock_create_log.call_args.kwargs
            assert call_kwargs["action"] == AuditAction.PROJECT_MEMBER_REMOVED
            assert call_kwargs["target_user_id"] == target_user.id
