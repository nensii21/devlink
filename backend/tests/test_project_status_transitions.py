"""
Tests for Project Status Transitions (#232)
"""

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.project_service import ProjectService
from app.services.project_status_service import (
    ALLOWED_PROJECT_STATUS_TRANSITIONS,
    ProjectStatusService,
)
from app.schemas.project import ProjectUpdate


def test_allowed_status_transitions_matrix():
    """Test that all documented allowed transitions pass validation."""
    for current_status, allowed_set in ALLOWED_PROJECT_STATUS_TRANSITIONS.items():
        for target_status in allowed_set:
            # Should not raise HTTPException
            ProjectStatusService.validate_status_transition(
                current_status, target_status
            )


def test_self_status_transitions_allowed():
    """Test that self-transitions (e.g. recruiting -> recruiting) are allowed no-ops."""
    for status_enum in ProjectStatus:
        ProjectStatusService.validate_status_transition(status_enum, status_enum)


def test_invalid_status_transitions_rejected():
    """Test that invalid transitions raise HTTP 400 Bad Request."""
    invalid_pairs = [
        (ProjectStatus.ARCHIVED, ProjectStatus.RECRUITING),
        (ProjectStatus.ARCHIVED, ProjectStatus.IN_PROGRESS),
        (ProjectStatus.ARCHIVED, ProjectStatus.COMPLETED),
        (ProjectStatus.ARCHIVED, ProjectStatus.PAUSED),
        (ProjectStatus.DRAFT, ProjectStatus.COMPLETED),
        (ProjectStatus.DRAFT, ProjectStatus.PAUSED),
        (ProjectStatus.RECRUITING, ProjectStatus.DRAFT),
        (ProjectStatus.RECRUITING, ProjectStatus.COMPLETED),
        (ProjectStatus.IN_PROGRESS, ProjectStatus.DRAFT),
        (ProjectStatus.COMPLETED, ProjectStatus.DRAFT),
        (ProjectStatus.COMPLETED, ProjectStatus.RECRUITING),
        (ProjectStatus.COMPLETED, ProjectStatus.PAUSED),
    ]

    for current_status, target_status in invalid_pairs:
        with pytest.raises(HTTPException) as exc_info:
            ProjectStatusService.validate_status_transition(
                current_status, target_status
            )
        assert exc_info.value.status_code == 400
        assert (
            f"Invalid project status transition from '{current_status.value}' to '{target_status.value}'"
            in exc_info.value.detail
        )


def test_invalid_status_string():
    """Test that invalid status strings raise HTTP 400."""
    with pytest.raises(HTTPException) as exc_info:
        ProjectStatusService.validate_status_transition(
            "non_existent_status", "recruiting"
        )
    assert exc_info.value.status_code == 400
    assert "Invalid current project status" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        ProjectStatusService.validate_status_transition("draft", "invalid_target")
    assert exc_info.value.status_code == 400
    assert "Invalid target project status" in exc_info.value.detail


def test_project_service_update_valid_transition(db):
    """Test updating project status using ProjectService with a valid transition."""
    user = User(
        first_name="Test",
        last_name="User",
        email="test_status_user@example.com",
        username="statususer1",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    project = Project(
        title="Test Status Project",
        slug="test-status-project-1",
        description="A test project for status transitions",
        owner_id=user.id,
        status=ProjectStatus.DRAFT,
        is_archived=False,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Valid: DRAFT -> RECRUITING
    update_data = ProjectUpdate(status=ProjectStatus.RECRUITING)
    updated_project = ProjectService.update_project(db, project, update_data)
    assert updated_project.status == ProjectStatus.RECRUITING
    assert updated_project.is_archived is False


def test_project_service_update_invalid_transition_rejected(db):
    """Test updating project status with an invalid transition raises HTTP 400."""
    user = User(
        first_name="Test",
        last_name="User",
        email="test_status_user2@example.com",
        username="statususer2",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    project = Project(
        title="Archived Project",
        slug="archived-project-2",
        description="An archived project",
        owner_id=user.id,
        status=ProjectStatus.ARCHIVED,
        is_archived=True,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Invalid: ARCHIVED -> RECRUITING
    update_data = ProjectUpdate(status=ProjectStatus.RECRUITING)
    with pytest.raises(HTTPException) as exc_info:
        ProjectService.update_project(db, project, update_data)

    assert exc_info.value.status_code == 400
    assert (
        "Invalid project status transition from 'archived' to 'recruiting'"
        in exc_info.value.detail
    )


def test_project_service_archive_and_restore(db):
    """Test archiving a project and restoring it to draft."""
    user = User(
        first_name="Test",
        last_name="User",
        email="test_status_user3@example.com",
        username="statususer3",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    project = Project(
        title="Project To Archive",
        slug="project-to-archive-3",
        description="Project description",
        owner_id=user.id,
        status=ProjectStatus.IN_PROGRESS,
        is_archived=False,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Archive (IN_PROGRESS -> ARCHIVED is valid)
    archived_project = ProjectService.archive_project(db, project)
    assert archived_project.status == ProjectStatus.ARCHIVED
    assert archived_project.is_archived is True

    # Restore (ARCHIVED -> DRAFT is valid)
    restored_project = ProjectService.restore_project(db, archived_project)
    assert restored_project.status == ProjectStatus.DRAFT
    assert restored_project.is_archived is False
