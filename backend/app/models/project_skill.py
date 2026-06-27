from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProjectSkill(Base):
    """
    Skills required by a project.
    """

    __tablename__ = "project_skills"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "skill_id",
            name="uq_project_skill",
        ),
    )

    # ----------------------------------------------------------
    # Primary Key
    # ----------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ----------------------------------------------------------
    # Foreign Keys
    # ----------------------------------------------------------

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ----------------------------------------------------------
    # Skill Requirements
    # ----------------------------------------------------------

    required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    minimum_experience: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ----------------------------------------------------------
    # Relationships
    # ----------------------------------------------------------

    project = relationship(
        "Project",
        backref="project_skills",
    )

    skill = relationship(
        "Skill",
        backref="project_skills",
    )

    # ----------------------------------------------------------
    # Audit
    # ----------------------------------------------------------

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
        return (
            f"<ProjectSkill(project_id={self.project_id}, "
            f"skill_id={self.skill_id})>"
        )