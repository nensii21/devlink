from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TeamMemberRole(str, Enum):
    LEADER = "leader"
    MEMBER = "member"


class HackathonTeam(Base):
    """
    A team participating in a hackathon.
    """

    __tablename__ = "hackathon_teams"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Foreign Keys
    # ==========================================================

    hackathon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hackathons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Details
    # ==========================================================

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    # ==========================================================
    # Metadata
    # ==========================================================

    member_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    hackathon = relationship(
        "Hackathon",
        backref="teams",
    )

    creator = relationship(
        "User",
        backref="created_hackathon_teams",
    )

    members = relationship(
        "HackathonTeamMember",
        backref="team",
        cascade="all, delete-orphan",
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
        return f"<HackathonTeam(name='{self.name}', hackathon_id={self.hackathon_id})>"


class HackathonTeamMember(Base):
    """
    Member of a hackathon team.
    """

    __tablename__ = "hackathon_team_members"

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_hackathon_team_member",
        ),
    )

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Foreign Keys
    # ==========================================================

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hackathon_teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Membership
    # ==========================================================

    role: Mapped[TeamMemberRole] = mapped_column(
        SqlEnum(TeamMemberRole),
        default=TeamMemberRole.MEMBER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    user = relationship(
        "User",
        backref="hackathon_team_memberships",
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
        return (
            f"<HackathonTeamMember("
            f"team_id={self.team_id}, "
            f"user_id={self.user_id}, "
            f"role='{self.role.value}'"
            f")>"
        )
