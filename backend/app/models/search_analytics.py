from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SearchQueryLog(Base):
    __tablename__ = "search_query_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    query: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Can be null if searched anonymously
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    results_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    filters: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # JSON dump of filters used

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )


class SearchClickLog(Base):
    __tablename__ = "search_click_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    search_query_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("search_query_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    clicked_entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'project', 'user', 'organization', 'skill'
    clicked_entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    # Can be null if anonymous
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
