"""
Reputation System Service (#597)
"""

from __future__ import annotations

import uuid
from typing import Optional, List, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.models.reputation import ReputationLog
from app.models.user import User
from app.schemas.reputation import (
    MAX_POINTS_PER_AWARD,
    LeaderboardEntry,
    LeaderboardResponse,
    ReputationAction,
    ReputationLogResponse,
    ReputationSummaryResponse,
)

# Points awarded per action source.
#
# Keyed by the wire values of :class:`ReputationAction`. Every member must
# appear here -- ``_assert_action_table_is_complete`` below enforces that at
# import time, so adding an enum member without a point value is a startup
# error rather than a silent fallback to ten points.
ACTION_POINTS: dict[str, int] = {
    ReputationAction.MERGED_PULL_REQUEST.value: 50,
    ReputationAction.COMPLETED_PROJECT.value: 100,
    ReputationAction.COMMUNITY_CONTRIBUTION.value: 25,
    ReputationAction.HELPFUL_DISCUSSION.value: 15,
    ReputationAction.PROFILE_COMPLETION.value: 10,
    ReputationAction.MENTOR_RECOGNITION.value: 30,
    ReputationAction.SUCCESSFUL_COLLABORATION.value: 30,
    ReputationAction.COMMUNITY_FEEDBACK.value: 20,
    ReputationAction.ENDORSEMENT.value: 15,
    ReputationAction.ACCOUNT_VERIFICATION.value: 40,
    ReputationAction.MANUAL_ADJUSTMENT.value: 0,
}


def _assert_action_table_is_complete() -> None:
    missing = {a.value for a in ReputationAction} - set(ACTION_POINTS)
    if missing:
        raise RuntimeError(
            f"ACTION_POINTS is missing point values for: {sorted(missing)}"
        )


_assert_action_table_is_complete()

# Rank Tier thresholds
RANK_TIERS: list[tuple[int, str]] = [
    (1000, "Legend 👑"),
    (500, "Mentor 💎"),
    (200, "Builder 🥇"),
    (50, "Contributor 🥈"),
    (0, "Novice 🥉"),
]


def calculate_rank_tier(score: int) -> str:
    """Calculate the user's community rank tier based on reputation score."""
    for threshold, tier in RANK_TIERS:
        if score >= threshold:
            return tier
    return "Novice 🥉"


class ReputationService:
    @staticmethod
    def resolve_points(action: str, points_override: Optional[int]) -> int:
        """How many points an award is worth.

        ``ACTION_POINTS.get(action.lower(), 10)`` used to accept any string and
        fall back to ten, so a typo scored. The action is validated against the
        table instead, and an override is bounded on both sides -- the schema
        enforces the same range, and this repeats it because the service is
        also called from places that do not go through the schema.
        """
        if points_override is not None:
            if abs(points_override) > MAX_POINTS_PER_AWARD:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"points must be between -{MAX_POINTS_PER_AWARD} and "
                        f"{MAX_POINTS_PER_AWARD}."
                    ),
                )
            return points_override

        normalised = action.lower()
        if normalised not in ACTION_POINTS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Unknown reputation action '{action}'. "
                    f"Valid actions: {sorted(ACTION_POINTS)}"
                ),
            )
        return ACTION_POINTS[normalised]

    @staticmethod
    def award_reputation(
        db: Session,
        user_id: uuid.UUID,
        action: str,
        points_override: Optional[int] = None,
        description: Optional[str] = None,
        granted_by_id: Optional[uuid.UUID] = None,
    ) -> Tuple[User, ReputationLog]:
        """
        Awards (or deducts) reputation points to a user and logs the transaction.

        ``granted_by_id`` records the administrator behind a manual
        adjustment. It is optional so the platform can award points to itself
        later, without a human actor, but the award endpoint always supplies it
        -- an adjustment nobody is named on is not auditable.
        """
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )

        pts = ReputationService.resolve_points(action, points_override)

        # Update user's aggregate reputation score
        user.reputation_score = (user.reputation_score or 0) + pts
        if user.reputation_score < 0:
            user.reputation_score = 0

        # Create log entry
        log_entry = ReputationLog(
            user_id=user.id,
            action=action.lower(),
            points=pts,
            description=description
            or f"Earned {pts} pts for {action.replace('_', ' ')}",
            granted_by_id=granted_by_id,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(user)
        db.refresh(log_entry)

        return user, log_entry

    @staticmethod
    def get_user_reputation_summary(
        db: Session,
        user_id: uuid.UUID,
        recent_logs_limit: int = 10,
        viewer: User | None = None,
    ) -> ReputationSummaryResponse:
        """
        Retrieves a user's total reputation score, rank tier, and recent activity logs.
        """
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )

        # Check activity visibility settings
        settings = user.get_privacy_settings()
        activity_visibility = settings.get("activity", "public")

        is_visible = False
        if activity_visibility == "public":
            is_visible = True
        elif activity_visibility == "authenticated" and viewer is not None:
            is_visible = True
        elif activity_visibility == "followers" and viewer is not None:
            if viewer.id == user.id or getattr(viewer, "is_superuser", False):
                is_visible = True
            else:
                from app.services.follower_service import FollowerService

                is_visible = FollowerService.is_following(
                    db, follower_id=viewer.id, following_id=user.id
                )
        elif activity_visibility == "private":
            if viewer is not None and (
                viewer.id == user.id or getattr(viewer, "is_superuser", False)
            ):
                is_visible = True

        if is_visible:
            logs_stmt = (
                select(ReputationLog)
                .where(ReputationLog.user_id == user_id)
                .order_by(desc(ReputationLog.created_at))
                .limit(recent_logs_limit)
            )
            logs = list(db.scalars(logs_stmt).all())
        else:
            logs = []

        score = user.reputation_score or 0
        tier = calculate_rank_tier(score)

        return ReputationSummaryResponse(
            user_id=user.id,
            reputation_score=score,
            rank_tier=tier,
            recent_logs=[ReputationLogResponse.model_validate(log) for log in logs],
        )

    @staticmethod
    def get_leaderboard(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> LeaderboardResponse:
        """
        Fetches the community leaderboard sorted by reputation_score descending.
        """
        # Both statements share one predicate so the count and the page are
        # drawn from the same set. Neither used to filter at all, so the
        # leaderboard ranked deactivated and soft-deleted accounts alongside
        # live ones -- publishing their username, name and avatar -- and
        # ``total`` was the count of every row in ``users``, which made the
        # client's page count wrong.
        ranked = (
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )

        total = db.scalar(select(func.count(User.id)).where(*ranked)) or 0

        users_stmt = (
            select(User)
            .where(*ranked)
            .order_by(desc(User.reputation_score), desc(User.created_at))
            .offset(skip)
            .limit(limit)
        )
        users = list(db.scalars(users_stmt).all())

        entries: List[LeaderboardEntry] = []
        for idx, u in enumerate(users, start=skip + 1):
            score = u.reputation_score or 0
            entries.append(
                LeaderboardEntry(
                    rank=idx,
                    user_id=u.id,
                    username=u.username,
                    full_name=getattr(u, "full_name", None)
                    or getattr(u, "name", u.username),
                    avatar_url=getattr(u, "avatar_url", None)
                    or getattr(u, "avatar", None),
                    reputation_score=score,
                    rank_tier=calculate_rank_tier(score),
                )
            )

        return LeaderboardResponse(entries=entries, total=total)

    @staticmethod
    def get_trust_score(db: Session, user_id: uuid.UUID) -> TrustScoreResponse:
        """
        Calculates user trust score breakdown (0-100 normalized) based on:
        1. Successful collaborations
        2. Merged pull requests
        3. Project completion
        4. Community feedback
        5. Endorsements
        6. Account verification
        """
        from app.schemas.reputation import TrustScoreBreakdown, TrustScoreResponse

        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )

        logs = list(
            db.scalars(
                select(ReputationLog).where(ReputationLog.user_id == user_id)
            ).all()
        )

        collab_pts = sum(l.points for l in logs if l.action == ReputationAction.SUCCESSFUL_COLLABORATION.value)
        pr_pts = sum(l.points for l in logs if l.action == ReputationAction.MERGED_PULL_REQUEST.value)
        project_pts = sum(l.points for l in logs if l.action == ReputationAction.COMPLETED_PROJECT.value)
        feedback_pts = sum(l.points for l in logs if l.action in [ReputationAction.COMMUNITY_FEEDBACK.value, ReputationAction.HELPFUL_DISCUSSION.value, ReputationAction.COMMUNITY_CONTRIBUTION.value])
        endorsement_pts = sum(l.points for l in logs if l.action in [ReputationAction.ENDORSEMENT.value, ReputationAction.MENTOR_RECOGNITION.value])
        
        is_verified = bool(getattr(user, "is_verified", False) or getattr(user, "verified", False))
        verification_pts = 40 if is_verified else sum(l.points for l in logs if l.action == ReputationAction.ACCOUNT_VERIFICATION.value)

        total_score = user.reputation_score or 0
        normalized_trust = min(100, max(10 if is_verified else 0, round((total_score / 500) * 100)))

        if normalized_trust >= 85:
            trust_level = "Highly Trusted Member ⭐"
        elif normalized_trust >= 60:
            trust_level = "Verified Contributor 🛡️"
        elif normalized_trust >= 30:
            trust_level = "Active Community Member 🚀"
        else:
            trust_level = "Rising Developer 🌱"

        return TrustScoreResponse(
            user_id=user.id,
            reputation_score=total_score,
            trust_score=normalized_trust,
            trust_level=trust_level,
            rank_tier=calculate_rank_tier(total_score),
            is_verified=is_verified,
            breakdown=TrustScoreBreakdown(
                collaborations_points=collab_pts,
                pull_requests_points=pr_pts,
                completed_projects_points=project_pts,
                feedback_points=feedback_pts,
                endorsements_points=endorsement_pts,
                verification_points=verification_pts,
            ),
        )

    @staticmethod
    def endorse_user(
        db: Session,
        endorser_id: uuid.UUID,
        target_user_id: uuid.UUID,
        skill_or_reason: str,
        note: Optional[str] = None,
    ) -> Tuple[User, ReputationLog]:
        """
        Allows a builder to endorse a peer, awarding +15 reputation points.
        """
        if endorser_id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot endorse yourself.",
            )

        description = f"Endorsed by peer for '{skill_or_reason}'"
        if note:
            description += f": {note}"

        return ReputationService.award_reputation(
            db=db,
            user_id=target_user_id,
            action=ReputationAction.ENDORSEMENT.value,
            points_override=15,
            description=description,
            granted_by_id=endorser_id,
        )

