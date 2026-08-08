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
    LeaderboardEntry,
    LeaderboardResponse,
    ReputationLogResponse,
    ReputationSummaryResponse,
)

# Points awarded per action source
ACTION_POINTS: dict[str, int] = {
    "merged_pull_request": 50,
    "completed_project": 100,
    "community_contribution": 25,
    "helpful_discussion": 15,
    "profile_completion": 10,
    "mentor_recognition": 30,
}

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
    def award_reputation(
        db: Session,
        user_id: uuid.UUID,
        action: str,
        points_override: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Tuple[User, ReputationLog]:
        """
        Awards (or deducts) reputation points to a user and logs the transaction.
        """
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )

        # Determine points to award
        if points_override is not None:
            pts = points_override
        else:
            pts = ACTION_POINTS.get(action.lower(), 10)

        # Update user's aggregate reputation score
        user.reputation_score = (user.reputation_score or 0) + pts
        if user.reputation_score < 0:
            user.reputation_score = 0

        # Create log entry
        log_entry = ReputationLog(
            user_id=user.id,
            action=action.lower(),
            points=pts,
            description=description or f"Earned {pts} pts for {action.replace('_', ' ')}",
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

        logs_stmt = (
            select(ReputationLog)
            .where(ReputationLog.user_id == user_id)
            .order_by(desc(ReputationLog.created_at))
            .limit(recent_logs_limit)
        )
        logs = list(db.scalars(logs_stmt).all())

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
        total_stmt = select(func.count(User.id))
        total = db.scalar(total_stmt) or 0

        users_stmt = (
            select(User)
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
                    full_name=getattr(u, "full_name", None) or getattr(u, "name", u.username),
                    avatar_url=getattr(u, "avatar_url", None) or getattr(u, "avatar", None),
                    reputation_score=score,
                    rank_tier=calculate_rank_tier(score),
                )
            )

        return LeaderboardResponse(entries=entries, total=total)
