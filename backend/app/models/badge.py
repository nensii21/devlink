import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class Badge(Base):
    __tablename__ = "badges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default="achievement")
    points = Column(Integer, nullable=False, default=10)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user_badges = relationship(
        "UserBadge", back_populates="badge", cascade="all, delete-orphan"
    )


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    badge_id = Column(
        String(36),
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    awarded_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    badge = relationship("Badge", back_populates="user_badges")

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)
