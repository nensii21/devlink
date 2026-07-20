from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.follower import Follower
from app.models.project import Project
from app.models.user import User
from app.schemas.user import UserCreate, UserStats, UserUpdate


class UserService:
    """
    Business logic for User operations.
    """

    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return db.scalar(stmt)

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return db.scalar(stmt)

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        stmt = select(User).offset(skip).limit(limit)
        return list(db.scalars(stmt))

    @staticmethod
    def create_user(
        db: Session,
        user: UserCreate,
        password_hash: str,
    ) -> User:

        db_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            password_hash=password_hash,
        )

        db.add(db_user)
        db.flush()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def update_user(
        db: Session,
        db_user: User,
        user: UserUpdate,
    ) -> User:

        data = user.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_user, key, value)

        db.flush()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def delete_user(
        db: Session,
        db_user: User,
    ) -> None:

        db.delete(db_user)
        db.flush()

    @staticmethod
    def activate_user(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_active = True

        db.flush()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def deactivate_user(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_active = False

        db.flush()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def get_user_stats(
        db: Session,
        user_id: uuid.UUID,
    ) -> UserStats:
        projects = (
            db.scalar(
                select(func.count())
                .select_from(Project)
                .where(Project.owner_id == user_id)
            )
            or 0
        )

        followers = (
            db.scalar(
                select(func.count())
                .select_from(Follower)
                .where(Follower.following_id == user_id)
            )
            or 0
        )

        following = (
            db.scalar(
                select(func.count())
                .select_from(Follower)
                .where(Follower.follower_id == user_id)
            )
            or 0
        )

        applications = (
            db.scalar(
                select(func.count())
                .select_from(Application)
                .where(Application.applicant_id == user_id)
            )
            or 0
        )

        accepted = (
            db.scalar(
                select(func.count())
                .select_from(Application)
                .where(
                    Application.applicant_id == user_id,
                    Application.status == ApplicationStatus.ACCEPTED,
                )
            )
            or 0
        )

        stats = UserStats(
            projects=projects,
            followers=followers,
            following=following,
            applications=applications,
            accepted=accepted,
        )

        user = db.get(User, user_id)
        if user:
            UserService.update_user_badges(db, user, stats)

        return stats

    @staticmethod
    def update_user_badges(
        db: Session,
        user: User,
        stats: UserStats,
    ) -> None:
        new_badges = []
        if stats.accepted >= 5:
            new_badges.append("Top Contributor")
        elif stats.accepted >= 1:
            new_badges.append("Active Developer")

        if stats.projects >= 1:
            new_badges.append("Project Owner")

        if stats.followers >= 10:
            new_badges.append("Social Butterfly")

        if set(user.badges) != set(new_badges):
            user.badges = new_badges
            db.add(user)
            db.commit()

    @staticmethod
    def verify_email(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_verified = True

        db.flush()
        db.refresh(db_user)

        return db_user
