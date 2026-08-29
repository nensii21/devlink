"""
Unit & Integration Tests for Project Milestone Management (#618)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.milestone import Milestone
from app.models.project import Project
from app.models.user import User
from app.schemas.milestone import (
    MilestoneCreate,
    MilestoneProgressResponse,
    MilestoneTimelineResponse,
    MilestoneUpdate,
)
from app.services.project_milestone_service import ProjectMilestoneService

# ---------------------------------------------------------------------------
# Test Fixtures / Mock Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(username: str = "testuser", system_role: str = "user") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    user.first_name = "Test"
    user.last_name = "User"
    user.system_role = system_role
    user.role = "user"
    return user


def _make_mock_project(
    owner_id: uuid.UUID | None = None, title: str = "DevLink Project"
) -> MagicMock:
    project = MagicMock(spec=Project)
    project.id = uuid.uuid4()
    project.owner_id = owner_id or uuid.uuid4()
    project.title = title
    return project


def _make_mock_milestone(
    project_id: uuid.UUID,
    title: str = "Beta Release",
    due_date: datetime | None = None,
    is_completed: bool = False,
    is_archived: bool = False,
) -> MagicMock:
    m = MagicMock(spec=Milestone)
    m.id = uuid.uuid4()
    m.project_id = project_id
    m.title = title
    m.description = "Deliver MVP features"
    m.due_date = due_date
    m.is_completed = is_completed
    m.completed_at = datetime.now(timezone.utc) if is_completed else None
    m.is_archived = is_archived
    m.archived_at = datetime.now(timezone.utc) if is_archived else None
    m.created_at = datetime.now(timezone.utc)
    m.updated_at = datetime.now(timezone.utc)
    return m


# ---------------------------------------------------------------------------
# 1. Authorization Tests
# ---------------------------------------------------------------------------


class TestMilestoneAuthorization:
    def test_owner_is_maintainer(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)
        assert (
            ProjectMilestoneService.is_user_project_maintainer(db, project, user.id)
            is True
        )

    def test_admin_system_role_allowed(self):
        db = MagicMock(spec=Session)
        admin_user = _make_mock_user(system_role="admin")
        project = _make_mock_project()
        # Should not raise exception
        ProjectMilestoneService.require_project_maintainer(db, project, admin_user)

    def test_non_member_forbidden(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None  # Not a member

        user = _make_mock_user()
        project = _make_mock_project()

        with pytest.raises(HTTPException) as exc_info:
            ProjectMilestoneService.require_project_maintainer(db, project, user)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# 2. CRUD Operations Tests
# ---------------------------------------------------------------------------


class TestMilestoneCRUD:
    def test_create_milestone_success(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)
        db.get.return_value = project

        m_in = MilestoneCreate(
            title=" Launch Alpha ",
            description="Alpha test rollout",
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
        )

        milestone = ProjectMilestoneService.create_milestone(db, project.id, m_in, user)

        assert milestone.title == "Launch Alpha"
        assert milestone.description == "Alpha test rollout"
        assert milestone.is_completed is False
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_get_milestone_or_404_found(self):
        db = MagicMock(spec=Session)
        project_id = uuid.uuid4()
        m = _make_mock_milestone(project_id)
        db.scalar.return_value = m

        res = ProjectMilestoneService.get_milestone_or_404(db, project_id, m.id)
        assert res == m

    def test_get_milestone_or_404_not_found(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            ProjectMilestoneService.get_milestone_or_404(db, uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404

    def test_update_milestone_complete_and_reopen(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)
        db.get.return_value = project

        milestone = _make_mock_milestone(project.id, is_completed=False)
        db.scalar.return_value = milestone

        # Update to complete
        update_in = MilestoneUpdate(is_completed=True)
        res = ProjectMilestoneService.update_milestone(
            db, project.id, milestone.id, update_in, user
        )
        assert res.is_completed is True
        assert res.completed_at is not None

    def test_archive_and_unarchive_milestone(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)
        db.get.return_value = project

        milestone = _make_mock_milestone(project.id, is_archived=False)
        db.scalar.return_value = milestone

        # Archive
        res = ProjectMilestoneService.archive_milestone(
            db, project.id, milestone.id, user, archive=True
        )
        assert res.is_archived is True
        assert res.archived_at is not None

        # Unarchive
        res_un = ProjectMilestoneService.archive_milestone(
            db, project.id, milestone.id, user, archive=False
        )
        assert res_un.is_archived is False
        assert res_un.archived_at is None

    def test_delete_milestone_success(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        project = _make_mock_project(owner_id=user.id)
        db.get.return_value = project

        milestone = _make_mock_milestone(project.id)
        db.scalar.return_value = milestone

        ProjectMilestoneService.delete_milestone(db, project.id, milestone.id, user)
        db.delete.assert_called_once_with(milestone)
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# 3. Progress & Timeline Calculations Tests
# ---------------------------------------------------------------------------


class TestMilestoneProgressAndTimeline:
    def test_calculate_progress_metrics(self):
        db = MagicMock(spec=Session)
        project_id = uuid.uuid4()
        project = _make_mock_project(owner_id=uuid.uuid4())
        project.id = project_id
        db.get.return_value = project

        now = datetime.now(timezone.utc)

        m1 = _make_mock_milestone(project_id, "Completed 1", is_completed=True)
        m2 = _make_mock_milestone(
            project_id,
            "Upcoming 1",
            is_completed=False,
            due_date=now + timedelta(days=5),
        )
        m3 = _make_mock_milestone(
            project_id,
            "Overdue 1",
            is_completed=False,
            due_date=now - timedelta(days=2),
        )
        m4 = _make_mock_milestone(
            project_id, "Archived 1", is_completed=True, is_archived=True
        )

        db.scalars.return_value.all.return_value = [m1, m2, m3, m4]

        progress = ProjectMilestoneService.calculate_progress(db, project_id)

        assert isinstance(progress, MilestoneProgressResponse)
        assert progress.total_milestones == 4
        assert progress.active_milestones == 3
        assert progress.completed_milestones == 1
        assert progress.archived_milestones == 1
        assert progress.overdue_milestones == 1
        # 1 completed out of 3 active = 33.3%
        assert progress.completion_percentage == 33.3

    def test_get_timeline_view(self):
        db = MagicMock(spec=Session)
        project_id = uuid.uuid4()
        project = _make_mock_project(owner_id=uuid.uuid4(), title="Awesome App")
        project.id = project_id
        db.get.return_value = project

        now = datetime.now(timezone.utc)

        m_overdue = _make_mock_milestone(
            project_id, "Overdue Item", due_date=now - timedelta(days=3)
        )
        m_upcoming = _make_mock_milestone(
            project_id, "Upcoming Item", due_date=now + timedelta(days=10)
        )
        m_completed = _make_mock_milestone(project_id, "Done Item", is_completed=True)

        db.scalars.return_value.all.return_value = [m_overdue, m_upcoming, m_completed]

        timeline_res = ProjectMilestoneService.get_timeline(db, project_id)

        assert isinstance(timeline_res, MilestoneTimelineResponse)
        assert timeline_res.project_title == "Awesome App"
        assert len(timeline_res.timeline) == 3

        statuses = {item.milestone.title: item.status for item in timeline_res.timeline}
        assert statuses["Overdue Item"] == "overdue"
        assert statuses["Upcoming Item"] == "upcoming"
        assert statuses["Done Item"] == "completed"
