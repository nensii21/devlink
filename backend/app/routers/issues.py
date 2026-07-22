from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.middleware.rate_limit import limiter
from app.models.issue import Issue
from app.models.user import User
from app.schemas.issue import (
    DifficultyEstimateResponse,
    DifficultyOverride,
    IssueCreate,
    IssueResponse,
    IssueUpdate,
)
from app.services.issue_difficulty_service import IssueDifficultyService

router = APIRouter(
    tags=["Issues"],
)

ISSUE_RATE_LIMIT = "30/minute"


@router.post(
    "/",
    response_model=IssueResponse,
    status_code=201,
)
@limiter.limit(ISSUE_RATE_LIMIT)
def create_issue(
    request: Request,
    body: IssueCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Create a new issue and automatically estimate its difficulty."""
    issue = Issue(
        project_id=body.project_id,
        author_id=current_user.id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        labels=body.labels,
    )

    # Run AI difficulty estimation
    result = IssueDifficultyService.estimate_difficulty(
        title=body.title,
        description=body.description,
        labels=body.labels,
    )
    issue.difficulty = result.difficulty
    issue.difficulty_confidence = result.confidence
    issue.difficulty_manual_override = False

    db.add(issue)
    db.flush()
    db.refresh(issue)

    return issue


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
)
def get_issue(
    issue_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get an issue by ID."""
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.get(
    "/project/{project_id}",
    response_model=list[IssueResponse],
)
def list_project_issues(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """List all issues for a project."""
    stmt = select(Issue).where(Issue.project_id == project_id).order_by(Issue.created_at.desc())
    return list(db.scalars(stmt))


@router.patch(
    "/{issue_id}",
    response_model=IssueResponse,
)
def update_issue(
    issue_id: uuid.UUID,
    body: IssueUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Update an issue's details."""
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(issue, key, value)

    db.flush()
    db.refresh(issue)
    return issue


@router.post(
    "/{issue_id}/estimate",
    response_model=DifficultyEstimateResponse,
)
@limiter.limit(ISSUE_RATE_LIMIT)
def estimate_difficulty(
    request: Request,
    issue_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Re-run AI difficulty estimation on an existing issue."""
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    result = IssueDifficultyService.estimate_difficulty(
        title=issue.title,
        description=issue.description,
        labels=issue.labels,
    )

    # Update the issue with new estimation
    issue.difficulty = result.difficulty
    issue.difficulty_confidence = result.confidence
    issue.difficulty_manual_override = False

    db.flush()
    db.refresh(issue)

    return DifficultyEstimateResponse(
        difficulty=result.difficulty,
        confidence=result.confidence,
        reasoning=result.reasoning,
    )


@router.patch(
    "/{issue_id}/difficulty",
    response_model=IssueResponse,
)
def override_difficulty(
    issue_id: uuid.UUID,
    body: DifficultyOverride,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Manually override the AI-estimated difficulty."""
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue.difficulty = body.difficulty
    issue.difficulty_manual_override = True
    issue.difficulty_confidence = 1.0

    db.flush()
    db.refresh(issue)
    return issue
