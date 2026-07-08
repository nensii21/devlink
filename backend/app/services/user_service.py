from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """
    Business logic for User operations.
    """

    @staticmethod
    def get_user(
        db: Session,
        user_id: uuid.UUID,
    ) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    def get_user_including_deleted(
        db: Session,
        user_id: uuid.UUID,
    ) -> User | None:
        """Retrieve a user regardless of soft-delete status (admin use)."""
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        stmt = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        stmt = select(User).where(
            User.username == username,
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        stmt = (
            select(User)
            .where(User.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
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

        return db_user

    @staticmethod
    def soft_delete_user(
        db: Session,
        db_user: User,
        deleted_by_id: uuid.UUID,
    ) -> None:
        """Mark a user as deleted without removing the row."""
        db_user.deleted_at = func.now()
        db_user.deleted_by_id = deleted_by_id
        db.commit()

    @staticmethod
    def restore_user(
        db: Session,
        db_user: User,
    ) -> User:
        """Restore a soft-deleted user."""
        db_user.deleted_at = None
        db_user.deleted_by_id = None
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def hard_delete_user(
        db: Session,
        db_user: User,
    ) -> None:
        """Permanently remove a user from the database (admin only)."""
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
