"""Pydantic schemas for the Project Competitor Tracker."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.competitor import ComparisonVerdict, ThreatLevel


# ── Competitor Project ────────────────────────────────────────────────


class CompetitorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    website_url: Optional[str] = None
    repository_url: Optional[str] = None
    description: Optional[str] = None
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CompetitorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    website_url: Optional[str] = None
    repository_url: Optional[str] = None
    description: Optional[str] = None
    threat_level: Optional[ThreatLevel] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class CompetitorResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    tracked_by_id: uuid.UUID
    name: str
    website_url: Optional[str] = None
    repository_url: Optional[str] = None
    description: Optional[str] = None
    threat_level: ThreatLevel
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompetitorListResponse(BaseModel):
    items: List[CompetitorResponse]
    total: int


# ── Feature Comparison ────────────────────────────────────────────────


class FeatureComparisonCreate(BaseModel):
    feature_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    our_notes: Optional[str] = None
    their_notes: Optional[str] = None
    verdict: ComparisonVerdict = ComparisonVerdict.UNKNOWN


class FeatureComparisonUpdate(BaseModel):
    description: Optional[str] = None
    our_notes: Optional[str] = None
    their_notes: Optional[str] = None
    verdict: Optional[ComparisonVerdict] = None


class FeatureComparisonResponse(BaseModel):
    id: uuid.UUID
    competitor_id: uuid.UUID
    created_by_id: uuid.UUID
    feature_name: str
    description: Optional[str] = None
    our_notes: Optional[str] = None
    their_notes: Optional[str] = None
    verdict: ComparisonVerdict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Metric Snapshot ──────────────────────────────────────────────────


class MetricSnapshotCreate(BaseModel):
    stars: Optional[int] = None
    forks: Optional[int] = None
    contributors: Optional[int] = None
    downloads: Optional[int] = None
    open_issues: Optional[int] = None
    monthly_active_users: Optional[int] = None
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    snapshot_date: datetime


class MetricSnapshotResponse(BaseModel):
    id: uuid.UUID
    competitor_id: uuid.UUID
    recorded_by_id: uuid.UUID
    stars: Optional[int] = None
    forks: Optional[int] = None
    contributors: Optional[int] = None
    downloads: Optional[int] = None
    open_issues: Optional[int] = None
    monthly_active_users: Optional[int] = None
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    snapshot_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class MetricSnapshotListResponse(BaseModel):
    items: List[MetricSnapshotResponse]
    total: int


# ── Aggregated Comparison Report ─────────────────────────────────────


class CompetitorInsightReport(BaseModel):
    competitor: CompetitorResponse
    feature_comparisons: List[FeatureComparisonResponse]
    latest_snapshot: Optional[MetricSnapshotResponse] = None
    snapshot_count: int
    verdict_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of each verdict: superior, competitive, inferior, unknown",
    )
