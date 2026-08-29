import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Boolean, Index, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base


class ProfileView(Base):
    """
    Model tracking profile visits while respecting user privacy opt-outs.
    """

    __tablename__ = "profile_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    viewed_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    viewer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_anonymous = Column(Boolean, default=False, nullable=False)
    visit_count = Column(Integer, default=1, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    viewed_user = relationship(
        "User", foreign_keys=[viewed_user_id], backref="profile_views_received"
    )
    viewer = relationship(
        "User", foreign_keys=[viewer_id], backref="profile_views_made"
    )

    __table_args__ = (
        Index("idx_profile_view_target_time", "viewed_user_id", "created_at"),
        Index("idx_profile_view_unique_recent", "viewed_user_id", "viewer_id"),
    )
