"""Project Competitor Tracker models.

Tracks competing projects, compares features over time, and stores
periodic metric snapshots so teams can monitor the competitive landscape.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComparisonVerdict(str, Enum):
    SUPERIOR = "superior"
    COMPETITIVE = "competitive"
    INFERIOR = "inferior"
    UNKNOWN = "unknown"


class CompetitorProject(Base):
    """A competing project being tracked by a team."""

    __tablename__ = "competitor_projects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tracked_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Competitor info
    name = Column(String(200), nullable=False)
    website_url = Column(String(500), nullable=True)
    repository_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    # Categorisation
    threat_level = Column(
        SqlEnum(ThreatLevel),
        default=ThreatLevel.MEDIUM,
        nullable=False,
        index=True,
    )
    tags = Column(JSON, nullable=True, default=list)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    feature_comparisons = relationship(
        "FeatureComparison",
        back_populates="competitor",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    metric_snapshots = relationship(
        "MetricSnapshot",
        back_populates="competitor",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            name="uq_competitor_per_project",
        ),
    )

    def __repr__(self) -> str:
        return f"<CompetitorProject(name='{self.name}')>"


class FeatureComparison(Base):
    """Compares a specific feature dimension between our project and a competitor."""

    __tablename__ = "feature_comparisons"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitor_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    feature_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    our_notes = Column(Text, nullable=True)
    their_notes = Column(Text, nullable=True)

    verdict = Column(
        SqlEnum(ComparisonVerdict),
        default=ComparisonVerdict.UNKNOWN,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    competitor = relationship("CompetitorProject", back_populates="feature_comparisons")

    __table_args__ = (
        UniqueConstraint(
            "competitor_id",
            "feature_name",
            name="uq_feature_per_competitor",
        ),
    )

    def __repr__(self) -> str:
        return f"<FeatureComparison(feature='{self.feature_name}', verdict='{self.verdict}')>"


class MetricSnapshot(Base):
    """Periodic snapshot of public metrics for a competitor."""

    __tablename__ = "metric_snapshots"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitor_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Metrics
    stars = Column(Integer, nullable=True)
    forks = Column(Integer, nullable=True)
    contributors = Column(Integer, nullable=True)
    downloads = Column(Integer, nullable=True)
    open_issues = Column(Integer, nullable=True)
    monthly_active_users = Column(Integer, nullable=True)
    custom_metrics = Column(JSON, nullable=True, default=dict)

    notes = Column(Text, nullable=True)
    snapshot_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    competitor = relationship("CompetitorProject", back_populates="metric_snapshots")

    def __repr__(self) -> str:
        return f"<MetricSnapshot(date='{self.snapshot_date}')>"
