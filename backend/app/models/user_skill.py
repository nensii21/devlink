from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UserSkill(Base):
    """
    Associates users with their skills.
    """

    __tablename__ = "user_skills"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "skill_id",
            name="uq_user_skill",
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

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
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
    # Skill Information
    # ----------------------------------------------------------

    level: Mapped[SkillLevel] = mapped_column(
        SqlEnum(SkillLevel),
        default=SkillLevel.BEGINNER,
        nullable=False,
    )

    years_of_experience: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ----------------------------------------------------------
    # Relationships
    # ----------------------------------------------------------

    user = relationship(
        "User",
        backref="user_skills",
    )

    skill = relationship(
        "Skill",
        backref="user_skills",
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
            f"<UserSkill(user_id={self.user_id}, "
            f"skill_id={self.skill_id}, "
            f"level={self.level.value})>"
        )