from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RefreshToken(Base):
    """
    Stores refresh tokens for authenticated users.

    Enables:
    - Multiple devices
    - Logout
    - Logout from all devices
    - Token rotation
    - Revocation
    """

    __tablename__ = "refresh_tokens"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # User
    # ==========================================================

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Token
    # ==========================================================

    token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        unique=True,
        index=True,
    )

    # ==========================================================
    # Device Information
    # ==========================================================

    device_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    device_type: Mapped[str | None] = mapped_column(
        String(100),
    )

    browser: Mapped[str | None] = mapped_column(
        String(100),
    )

    operating_system: Mapped[str | None] = mapped_column(
        String(100),
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(64),
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
    )

    # ==========================================================
    # Token Status
    # ==========================================================

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    # ==========================================================
    # Relationship
    # ==========================================================

    user = relationship(
        "User",
        backref="refresh_tokens",
    )

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<RefreshToken(user={self.user_id}, revoked={self.is_revoked})>"
