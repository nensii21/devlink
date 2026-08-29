"""
Reputation System Router (#597)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.rbac import SystemRole
from app.database.session import get_db
from app.dependencies import (
    get_current_user,
    get_optional_current_user,
    require_roles,
)
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.reputation import (
    LeaderboardResponse,
    ReputationAwardRequest,
    ReputationLogResponse,
    ReputationSummaryResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.reputation_service import ReputationService

router = APIRouter(prefix="/reputation", tags=["User Reputation System"])


@router.get(
    "/me",
    response_model=ReputationSummaryResponse,
    summary="Get current user reputation summary & activity log",
)
def get_my_reputation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated user's total reputation score, rank tier, and recent activity logs.
    """
    return ReputationService.get_user_reputation_summary(
        db, current_user.id, viewer=current_user
    )


@router.get(
    "/user/{user_id}",
    response_model=ReputationSummaryResponse,
    summary="Get specific user reputation summary & activity log",
)
def get_user_reputation(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    """
    Returns a specific user's total reputation score, rank tier, and recent activity logs.
    """
    return ReputationService.get_user_reputation_summary(
        db, user_id, viewer=current_user
    )


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get community leaderboard ranked by reputation score",
)
def get_leaderboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns top community members ranked by their reputation score.
    """
    return ReputationService.get_leaderboard(db, skip=skip, limit=limit)


@router.post(
    "/award",
    response_model=ReputationLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adjust a user's reputation (administrators only)",
    description=(
        "Grant or deduct reputation points. Restricted to administrators: "
        "reputation is meant to be a derived signal, and an endpoint that "
        "lets a caller name the target, the action and the number of points "
        "is a write primitive for anybody's score."
    ),
)
def award_reputation(
    payload: ReputationAwardRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(SystemRole.ADMIN)),
):
    """
    Awards reputation points for activities like merged pull requests, completed projects,
    contributions, discussions, profile completions, or mentor recognitions.

    ``payload.user_id`` is required and is never defaulted to the caller. The
    previous behaviour -- "omit the target and it means me" -- is the shape of
    a self-service score, which is not what this endpoint is for.
    """
    _, log_entry = ReputationService.award_reputation(
        db=db,
        user_id=payload.user_id,
        action=payload.action.value,
        points_override=payload.points,
        description=payload.description,
        granted_by_id=actor.id,
    )

    # The log row names the recipient and the actor; the audit trail is where
    # a reviewer goes looking for "what did this administrator do", so the
    # adjustment belongs in both.
    client = getattr(request, "client", None)
    AuditLogService.create_log(
        db=db,
        actor_id=actor.id,
        action=AuditAction.SETTINGS_CHANGED,
        entity_type="reputation_log",
        entity_id=str(log_entry.id),
        target_user_id=payload.user_id,
        description=(
            f"Adjusted reputation by {log_entry.points} "
            f"for action '{log_entry.action}'"
        ),
        new_values={"points": log_entry.points, "action": log_entry.action},
        ip_address=getattr(client, "host", None) if client else None,
        user_agent=request.headers.get("user-agent"),
        request_method=request.method,
        request_path=str(request.url.path),
    )
    db.commit()

    return ReputationLogResponse.model_validate(log_entry)
