from __future__ import annotations

import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.activity import ActivityType
from app.models.follower import Follower
from app.services.activity_service import ActivityService


class FollowerService:
    """
    Business logic for user follow relationships.
    """

    @staticmethod
    def follow_user(
        db: Session,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> Follower:

        relationship = Follower(
            follower_id=follower_id,
            following_id=following_id,
        )

        db.add(relationship)
        db.commit()
        db.refresh(relationship)

        ActivityService.record_activity(
            db=db,
            actor_id=follower_id,
            activity_type=ActivityType.FOLLOWED_USER,
            title="Followed a builder",
            description=str(following_id),
            icon="user-plus",
            color="success",
        )

        return relationship

    @staticmethod
    def get_relationship(
        db: Session,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> Follower | None:

        stmt = select(Follower).where(
            and_(
                Follower.follower_id == follower_id,
                Follower.following_id == following_id,
            )
        )

        return db.scalar(stmt)

    @staticmethod
    def is_following(
        db: Session,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> bool:

        stmt = select(Follower).where(
            and_(
                Follower.follower_id == follower_id,
                Follower.following_id == following_id,
            )
        )

        return db.scalar(stmt) is not None

    @staticmethod
    def list_followers(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[Follower]:

        stmt = (
            select(Follower)
            .where(Follower.following_id == user_id)
            .order_by(Follower.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_following(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[Follower]:

        stmt = (
            select(Follower)
            .where(Follower.follower_id == user_id)
            .order_by(Follower.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def follower_count(
        db: Session,
        user_id: uuid.UUID,
    ) -> int:

        stmt = select(Follower).where(Follower.following_id == user_id)

        return len(list(db.scalars(stmt)))

    @staticmethod
    def following_count(
        db: Session,
        user_id: uuid.UUID,
    ) -> int:

        stmt = select(Follower).where(Follower.follower_id == user_id)

        return len(list(db.scalars(stmt)))

    @staticmethod
    def mutual_followers(
        db: Session,
        user_a: uuid.UUID,
        user_b: uuid.UUID,
    ) -> list[Follower]:

        user_a_following = {
            relation.following_id
            for relation in db.scalars(
                select(Follower).where(Follower.follower_id == user_a)
            )
        }

        stmt = select(Follower).where(Follower.follower_id == user_b)

        return [
            relation
            for relation in db.scalars(stmt)
            if relation.following_id in user_a_following
        ]

    @staticmethod
    def unfollow_user(
        db: Session,
        relationship: Follower,
    ) -> None:

        db.delete(relationship)
        db.commit()
