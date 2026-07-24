from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenService:
    """
    Business logic for refresh tokens.
    """

    @staticmethod
    def create_token(
        db: Session,
        token: RefreshToken,
    ) -> RefreshToken:

        db.add(token)
        db.flush()
        db.refresh(token)

        return token

    @staticmethod
    def get_token(
        db: Session,
        token: str,
    ) -> RefreshToken | None:

        stmt = select(RefreshToken).where(RefreshToken.token == token)

        return db.scalar(stmt)

    @staticmethod
    def list_user_tokens(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[RefreshToken]:

        stmt = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def revoke_token(
        db: Session,
        db_token: RefreshToken,
    ) -> RefreshToken:

        db_token.is_revoked = True
        db_token.revoked_at = datetime.utcnow()

        db.flush()
        db.refresh(db_token)

        return db_token

    @staticmethod
    def revoke_all_tokens(
        db: Session,
        user_id: uuid.UUID,
    ) -> None:

        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)

        tokens = list(db.scalars(stmt))

        for token in tokens:
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()

        db.flush()

    @staticmethod
    def delete_expired_token(
        db: Session,
        db_token: RefreshToken,
    ) -> None:

        db.delete(db_token)
        db.flush()
