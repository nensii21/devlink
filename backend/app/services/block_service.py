from __future__ import annotations

import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.follower import Follower
from app.models.user import User
from app.models.user_block import UserBlock


class BlockService:
    @staticmethod
    def block_user(
        db: Session,
        blocker_id: uuid.UUID,
        blocked_id: uuid.UUID,
    ) -> UserBlock:
        if blocker_id == blocked_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot block yourself.",
            )

        target_user = db.scalar(select(User).where(User.id == blocked_id))
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User to block not found.",
            )

        # Check existing block
        existing = db.scalar(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        if existing:
            return existing

        block = UserBlock(
            blocker_id=blocker_id,
            blocked_id=blocked_id,
        )
        db.add(block)

        # Remove active follow relationships between both users
        follow_stmt = select(Follower).where(
            or_(
                (Follower.follower_id == blocker_id)
                & (Follower.following_id == blocked_id),
                (Follower.follower_id == blocked_id)
                & (Follower.following_id == blocker_id),
            )
        )
        active_follows = db.scalars(follow_stmt).all()
        for follow in active_follows:
            db.delete(follow)

        db.commit()
        db.refresh(block)
        return block

    @staticmethod
    def unblock_user(
        db: Session,
        blocker_id: uuid.UUID,
        blocked_id: uuid.UUID,
    ) -> bool:
        block = db.scalar(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not blocked.",
            )

        db.delete(block)
        db.commit()
        return True

    @staticmethod
    def is_blocked(
        db: Session,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
    ) -> bool:
        """
        Check if user A has blocked user B or user B has blocked user A.
        """
        block = db.scalar(
            select(UserBlock).where(
                or_(
                    (UserBlock.blocker_id == user_a_id)
                    & (UserBlock.blocked_id == user_b_id),
                    (UserBlock.blocker_id == user_b_id)
                    & (UserBlock.blocked_id == user_a_id),
                )
            )
        )
        return block is not None

    @staticmethod
    def has_blocked(
        db: Session,
        blocker_id: uuid.UUID,
        blocked_id: uuid.UUID,
    ) -> bool:
        """
        Check if blocker_id explicitly blocked blocked_id.
        """
        block = db.scalar(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        return block is not None

    @staticmethod
    def get_blocked_users(
        db: Session,
        user_id: uuid.UUID,
    ) -> List[User]:
        stmt = (
            select(User)
            .join(UserBlock, User.id == UserBlock.blocked_id)
            .where(UserBlock.blocker_id == user_id)
            .order_by(UserBlock.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_blocked_and_blocking_user_ids(
        db: Session,
        user_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        """
        Get all user IDs that either the current user blocked or that blocked the current user.
        """
        rows = db.execute(
            select(UserBlock.blocker_id, UserBlock.blocked_id).where(
                or_(
                    UserBlock.blocker_id == user_id,
                    UserBlock.blocked_id == user_id,
                )
            )
        ).all()

        blocked_ids = set()
        for blocker_id, blocked_id in rows:
            if blocker_id != user_id:
                blocked_ids.add(blocker_id)
            if blocked_id != user_id:
                blocked_ids.add(blocked_id)
        return blocked_ids
