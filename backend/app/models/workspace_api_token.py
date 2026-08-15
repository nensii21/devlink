from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Forward reference for type annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class WorkspaceApiToken(Base):
    """
    Workspace API Tokens for automation and integration authentication.
    """

    __tablename__ = "workspace_api_tokens"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Relations / FKs
    # ==========================================================

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Token details
    # ==========================================================

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    hashed_token: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        unique=True,
        index=True,
    )

    prefix: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    scopes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    # ==========================================================
    # Expiration & Usage
    # ==========================================================

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    organization = relationship(
        "Organization",
        backref="api_tokens",
        passive_deletes=True,
    )

    created_by = relationship(
        "User",
        backref="workspace_api_tokens",
    )

    def __repr__(self):
        return f"<WorkspaceApiToken(name='{self.name}', prefix='{self.prefix}')>"
