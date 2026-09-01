import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class LearningResource(Base):
    """A curated learning resource linked to a project."""

    __tablename__ = "learning_resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(
        String(50), nullable=False, default="tutorial", index=True
    )  # tutorial | documentation | video | guide | tool | article
    language = Column(String(50), nullable=True, index=True)
    difficulty = Column(
        String(20), nullable=False, default="intermediate", index=True
    )  # beginner | intermediate | advanced
    is_external = Column(Boolean, default=True, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)
    view_count = Column(Integer, default=0, nullable=False)
    vote_score = Column(Integer, default=0, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    author = relationship("User", backref="learning_resources")
    votes = relationship(
        "ResourceVote", back_populates="resource", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "url", name="uq_project_resource_url"),
    )


class ResourceVote(Base):
    """Tracks a user's upvote/downvote on a learning resource."""

    __tablename__ = "resource_votes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(
        String(36),
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value = Column(Integer, nullable=False, default=1)  # +1 upvote, -1 downvote
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    resource = relationship("LearningResource", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("resource_id", "user_id", name="uq_resource_user_vote"),
    )
