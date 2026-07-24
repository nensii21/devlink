from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RepositoryProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class Repository(Base):
    """
    Connected source code repository.
    """

    __tablename__ = "repositories"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    connected_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Repository
    # ==========================================================

    provider: Mapped[RepositoryProvider] = mapped_column(
        SqlEnum(RepositoryProvider),
        nullable=False,
    )

    repository_id: Mapped[str | None] = mapped_column(
        String(100),
    )

    owner: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    default_branch: Mapped[str] = mapped_column(
        String(50),
        default="main",
    )

    clone_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    html_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    homepage: Mapped[str | None] = mapped_column(
        String(500),
    )

    language: Mapped[str | None] = mapped_column(
        String(100),
    )

    # ==========================================================
    # Statistics
    # ==========================================================

    stars: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    forks: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    watchers: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    open_issues: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    contributors: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # ==========================================================
    # Status
    # ==========================================================

    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    synced: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    project = relationship(
        "Project",
        backref="repositories",
    )

    user = relationship(
        "User",
        backref="repositories",
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

    def __repr__(self):
        return (
            f"<Repository(provider='{self.provider.value}', repo='{self.full_name}')>"
        )
