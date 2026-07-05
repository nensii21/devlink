from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import ActivityType
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.activity_service import ActivityService


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
        db.commit()
        db.refresh(db_user)

        ActivityService.record_activity(
            db=db,
            actor_id=db_user.id,
            activity_type=ActivityType.USER_REGISTERED,
            title="Joined DevLink",
            description=f"{db_user.first_name} {db_user.last_name} joined DevLink.",
            icon="user-plus",
            color="success",
        )

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

        db.commit()
        db.refresh(db_user)

        ActivityService.record_activity(
            db=db,
            actor_id=db_user.id,
            activity_type=ActivityType.PROFILE_UPDATED,
            title="Updated profile",
            description=f"{db_user.first_name} {db_user.last_name} updated their profile.",
            icon="user-round-pen",
            color="info",
        )

        return db_user

    @staticmethod
    def delete_user(
        db: Session,
        db_user: User,
    ) -> None:

        db.delete(db_user)
        db.commit()

    @staticmethod
    def activate_user(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_active = True

        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def deactivate_user(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_active = False

        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def verify_email(
        db: Session,
        db_user: User,
    ) -> User:

        db_user.is_verified = True

        db.commit()
        db.refresh(db_user)

        return db_user
