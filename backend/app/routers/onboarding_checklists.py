"""API router for project onboarding checklists."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.onboarding_checklist import (
    AssignmentBatchCreate,
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentWithProgress,
    ChecklistCreate,
    ChecklistListResponse,
    ChecklistResponse,
    ChecklistStats,
    ChecklistWithItems,
    ChecklistUpdate,
    ItemCompletionCreate,
    ItemCompletionResponse,
    OnboardingItemCreate,
    OnboardingItemResponse,
    OnboardingItemUpdate,
    ProjectOnboardingStats,
)
from app.services.onboarding_checklist_service import OnboardingChecklistService

router = APIRouter(
    prefix="/projects/{project_id}/onboarding",
    tags=["Project Onboarding Checklists"],
)


# ── Checklist CRUD ──────────────────────────────────────────────────


@router.post(
    "/checklists",
    response_model=ChecklistResponse,
    status_code=201,
    summary="Create an onboarding checklist",
)
def create_checklist(
    project_id: uuid.UUID,
    data: ChecklistCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Create a new onboarding checklist for a project."""
    return OnboardingChecklistService.create_checklist(
        db, project_id, current_user.id, data
    )


@router.get(
    "/checklists",
    response_model=ChecklistListResponse,
    summary="List onboarding checklists",
)
def list_checklists(
    project_id: uuid.UUID,
    include_archived: bool = Query(False),
    db: Session = Depends(get_database),
):
    """List all onboarding checklists for a project."""
    return OnboardingChecklistService.list_checklists(
        db, project_id, include_archived=include_archived
    )


@router.get(
    "/checklists/{checklist_id}",
    response_model=ChecklistWithItems,
    summary="Get a checklist with its items",
)
def get_checklist(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get a checklist with all its items sorted by order."""
    result = OnboardingChecklistService.get_checklist(db, checklist_id)
    if not result:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return result


@router.put(
    "/checklists/{checklist_id}",
    response_model=ChecklistResponse,
    summary="Update a checklist",
)
def update_checklist(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    data: ChecklistUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Update checklist metadata."""
    result = OnboardingChecklistService.update_checklist(db, checklist_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return result


@router.delete(
    "/checklists/{checklist_id}",
    status_code=204,
    summary="Delete a checklist",
)
def delete_checklist(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Delete an onboarding checklist and all its items."""
    if not OnboardingChecklistService.delete_checklist(db, checklist_id):
        raise HTTPException(status_code=404, detail="Checklist not found")


# ── Checklist Items ──────────────────────────────────────────────────


@router.post(
    "/checklists/{checklist_id}/items",
    response_model=OnboardingItemResponse,
    status_code=201,
    summary="Add an item to a checklist",
)
def add_item(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    data: OnboardingItemCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Add a new onboarding step to a checklist."""
    result = OnboardingChecklistService.add_item(db, checklist_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return result


@router.put(
    "/items/{item_id}",
    response_model=OnboardingItemResponse,
    summary="Update a checklist item",
)
def update_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    data: OnboardingItemUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Update an onboarding checklist item."""
    result = OnboardingChecklistService.update_item(db, item_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.delete(
    "/items/{item_id}",
    status_code=204,
    summary="Delete a checklist item",
)
def delete_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Remove an item from a checklist."""
    if not OnboardingChecklistService.delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Item not found")


# ── Assignments ──────────────────────────────────────────────────────


@router.post(
    "/checklists/{checklist_id}/assign",
    response_model=AssignmentResponse,
    status_code=201,
    summary="Assign checklist to a user",
)
def assign_checklist(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    data: AssignmentCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Assign an onboarding checklist to a project member."""
    result = OnboardingChecklistService.assign_checklist(
        db, checklist_id, current_user.id, data
    )
    if not result:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return result


@router.post(
    "/checklists/{checklist_id}/assign-batch",
    response_model=List[AssignmentResponse],
    status_code=201,
    summary="Batch assign checklist to multiple users",
)
def batch_assign_checklist(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    data: AssignmentBatchCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Assign an onboarding checklist to multiple project members at once."""
    results = OnboardingChecklistService.batch_assign(
        db, checklist_id, current_user.id, data.user_ids
    )
    if not results:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return results


@router.get(
    "/checklists/{checklist_id}/assignments",
    response_model=AssignmentListResponse,
    summary="List assignments for a checklist",
)
def list_assignments(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    completed_only: Optional[bool] = Query(None),
    db: Session = Depends(get_database),
):
    """List all users assigned to a checklist, optionally filtered by completion status."""
    return OnboardingChecklistService.list_assignments(
        db, checklist_id, completed_only=completed_only
    )


@router.get(
    "/assignments/{assignment_id}/progress",
    response_model=AssignmentWithProgress,
    summary="Get assignment progress",
)
def get_assignment_progress(
    project_id: uuid.UUID,
    assignment_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get detailed progress for a user's checklist assignment."""
    result = OnboardingChecklistService.get_assignment_progress(db, assignment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return result


@router.post(
    "/assignments/{assignment_id}/items/{item_id}/complete",
    response_model=ItemCompletionResponse,
    status_code=201,
    summary="Mark an item as complete",
)
def complete_item(
    project_id: uuid.UUID,
    assignment_id: uuid.UUID,
    item_id: uuid.UUID,
    data: Optional[ItemCompletionCreate] = None,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Mark a specific onboarding item as completed for a user."""
    result = OnboardingChecklistService.complete_item(
        db, assignment_id, item_id, current_user.id, data
    )
    if not result:
        raise HTTPException(
            status_code=404, detail="Assignment or item not found"
        )
    return result


# ── Statistics ───────────────────────────────────────────────────────


@router.get(
    "/checklists/{checklist_id}/stats",
    response_model=ChecklistStats,
    summary="Get checklist statistics",
)
def get_checklist_stats(
    project_id: uuid.UUID,
    checklist_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get statistics for a specific onboarding checklist."""
    result = OnboardingChecklistService.get_checklist_stats(db, checklist_id)
    if not result:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return result


@router.get(
    "/stats",
    response_model=ProjectOnboardingStats,
    summary="Get project onboarding stats",
)
def get_project_stats(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get aggregate onboarding statistics for a project."""
    return OnboardingChecklistService.get_project_onboarding_stats(db, project_id)
