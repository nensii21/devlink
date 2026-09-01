"""API router for the Project Competitor Tracker."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorInsightReport,
    CompetitorListResponse,
    CompetitorResponse,
    CompetitorUpdate,
    FeatureComparisonCreate,
    FeatureComparisonResponse,
    FeatureComparisonUpdate,
    MetricSnapshotCreate,
    MetricSnapshotListResponse,
    MetricSnapshotResponse,
)
from app.services.competitor_service import CompetitorService
from app.models.competitor import ComparisonVerdict, ThreatLevel

router = APIRouter(
    prefix="/projects/{project_id}/competitors",
    tags=["Project Competitor Tracker"],
)


# ── Competitor CRUD ──────────────────────────────────────────────────


@router.post(
    "/",
    response_model=CompetitorResponse,
    status_code=201,
    summary="Add a competitor to track",
)
def add_competitor(
    project_id: uuid.UUID,
    data: CompetitorCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Register a new competing project for tracking."""
    return CompetitorService.create_competitor(db, project_id, current_user.id, data)


@router.get(
    "/",
    response_model=CompetitorListResponse,
    summary="List tracked competitors",
)
def list_competitors(
    project_id: uuid.UUID,
    threat_level: Optional[ThreatLevel] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_database),
):
    """List all competitors being tracked for a project, optionally filtered by threat level."""
    return CompetitorService.list_competitors(
        db, project_id, threat_level=threat_level, skip=skip, limit=limit,
    )


@router.get(
    "/summary",
    response_model=dict,
    summary="Get threat level summary",
)
def threat_summary(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Return count of competitors per threat level for a project."""
    return CompetitorService.get_threat_summary(db, project_id)


@router.get(
    "/{competitor_id}",
    response_model=CompetitorResponse,
    summary="Get a tracked competitor",
)
def get_competitor(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get details of a specific competitor."""
    result = CompetitorService.get_competitor(db, competitor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return result


@router.put(
    "/{competitor_id}",
    response_model=CompetitorResponse,
    summary="Update a competitor",
)
def update_competitor(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    data: CompetitorUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Update details of a tracked competitor."""
    result = CompetitorService.update_competitor(db, competitor_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return result


@router.delete(
    "/{competitor_id}",
    status_code=204,
    summary="Remove a competitor",
)
def delete_competitor(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Remove a competitor from tracking."""
    deleted = CompetitorService.delete_competitor(db, competitor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Competitor not found")


# ── Feature Comparisons ──────────────────────────────────────────────


@router.post(
    "/{competitor_id}/comparisons",
    response_model=FeatureComparisonResponse,
    status_code=201,
    summary="Add a feature comparison",
)
def add_comparison(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    data: FeatureComparisonCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Add a new feature comparison against a competitor."""
    result = CompetitorService.create_comparison(
        db, competitor_id, current_user.id, data,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return result


@router.get(
    "/{competitor_id}/comparisons",
    response_model=List[FeatureComparisonResponse],
    summary="List feature comparisons",
)
def list_comparisons(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    verdict: Optional[ComparisonVerdict] = Query(None),
    db: Session = Depends(get_database),
):
    """List all feature comparisons for a competitor, optionally filtered by verdict."""
    return CompetitorService.list_comparisons(db, competitor_id, verdict=verdict)


@router.put(
    "/comparisons/{comparison_id}",
    response_model=FeatureComparisonResponse,
    summary="Update a feature comparison",
)
def update_comparison(
    project_id: uuid.UUID,
    comparison_id: uuid.UUID,
    data: FeatureComparisonUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Update a feature comparison."""
    result = CompetitorService.update_comparison(db, comparison_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return result


@router.delete(
    "/comparisons/{comparison_id}",
    status_code=204,
    summary="Delete a feature comparison",
)
def delete_comparison(
    project_id: uuid.UUID,
    comparison_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Delete a feature comparison."""
    deleted = CompetitorService.delete_comparison(db, comparison_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Comparison not found")


# ── Metric Snapshots ─────────────────────────────────────────────────


@router.post(
    "/{competitor_id}/snapshots",
    response_model=MetricSnapshotResponse,
    status_code=201,
    summary="Record a metric snapshot",
)
def add_snapshot(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    data: MetricSnapshotCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Record a periodic metric snapshot for a competitor."""
    result = CompetitorService.create_snapshot(
        db, competitor_id, current_user.id, data,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return result


@router.get(
    "/{competitor_id}/snapshots",
    response_model=MetricSnapshotListResponse,
    summary="List metric snapshots",
)
def list_snapshots(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
):
    """List metric snapshots for a competitor, most recent first."""
    return CompetitorService.list_snapshots(db, competitor_id, limit=limit)


@router.get(
    "/{competitor_id}/snapshots/latest",
    response_model=MetricSnapshotResponse,
    summary="Get latest metric snapshot",
)
def get_latest_snapshot(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get the most recent metric snapshot for a competitor."""
    result = CompetitorService.get_latest_snapshot(db, competitor_id)
    if not result:
        raise HTTPException(status_code=404, detail="No snapshots found")
    return result


@router.delete(
    "/snapshots/{snapshot_id}",
    status_code=204,
    summary="Delete a metric snapshot",
)
def delete_snapshot(
    project_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Delete a metric snapshot."""
    deleted = CompetitorService.delete_snapshot(db, snapshot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Snapshot not found")


# ── Insights ─────────────────────────────────────────────────────────


@router.get(
    "/{competitor_id}/insights",
    response_model=CompetitorInsightReport,
    summary="Get competitor insight report",
)
def get_insights(
    project_id: uuid.UUID,
    competitor_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Get a comprehensive insight report for a competitor including comparisons, latest metrics, and verdict summary."""
    result = CompetitorService.get_insight_report(db, competitor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return result
