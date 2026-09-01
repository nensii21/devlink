"""Service layer for the Project Competitor Tracker."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.competitor import (
    ComparisonVerdict,
    CompetitorProject,
    FeatureComparison,
    MetricSnapshot,
    ThreatLevel,
)
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


class CompetitorService:
    """CRUD and analytics for competitor tracking."""

    # ── Competitor Projects ──────────────────────────────────────────

    @staticmethod
    def create_competitor(
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CompetitorCreate,
    ) -> CompetitorResponse:
        competitor = CompetitorProject(
            project_id=project_id,
            tracked_by_id=user_id,
            name=data.name,
            website_url=data.website_url,
            repository_url=data.repository_url,
            description=data.description,
            threat_level=data.threat_level,
            tags=data.tags,
            notes=data.notes,
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
        return CompetitorResponse.model_validate(competitor)

    @staticmethod
    def list_competitors(
        db: Session,
        project_id: uuid.UUID,
        threat_level: Optional[ThreatLevel] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> CompetitorListResponse:
        query = db.query(CompetitorProject).filter(
            CompetitorProject.project_id == project_id,
        )
        if threat_level:
            query = query.filter(CompetitorProject.threat_level == threat_level)

        total = query.count()
        items = (
            query.order_by(desc(CompetitorProject.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return CompetitorListResponse(
            items=[CompetitorResponse.model_validate(i) for i in items],
            total=total,
        )

    @staticmethod
    def get_competitor(
        db: Session,
        competitor_id: uuid.UUID,
    ) -> Optional[CompetitorResponse]:
        competitor = db.query(CompetitorProject).filter(
            CompetitorProject.id == competitor_id,
        ).first()
        if not competitor:
            return None
        return CompetitorResponse.model_validate(competitor)

    @staticmethod
    def update_competitor(
        db: Session,
        competitor_id: uuid.UUID,
        data: CompetitorUpdate,
    ) -> Optional[CompetitorResponse]:
        competitor = db.query(CompetitorProject).filter(
            CompetitorProject.id == competitor_id,
        ).first()
        if not competitor:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(competitor, key, value)

        db.commit()
        db.refresh(competitor)
        return CompetitorResponse.model_validate(competitor)

    @staticmethod
    def delete_competitor(
        db: Session,
        competitor_id: uuid.UUID,
    ) -> bool:
        competitor = db.query(CompetitorProject).filter(
            CompetitorProject.id == competitor_id,
        ).first()
        if not competitor:
            return False
        db.delete(competitor)
        db.commit()
        return True

    # ── Feature Comparisons ──────────────────────────────────────────

    @staticmethod
    def create_comparison(
        db: Session,
        competitor_id: uuid.UUID,
        user_id: uuid.UUID,
        data: FeatureComparisonCreate,
    ) -> Optional[FeatureComparisonResponse]:
        competitor = db.query(CompetitorProject).filter(
            CompetitorProject.id == competitor_id,
        ).first()
        if not competitor:
            return None

        comparison = FeatureComparison(
            competitor_id=competitor_id,
            created_by_id=user_id,
            feature_name=data.feature_name,
            description=data.description,
            our_notes=data.our_notes,
            their_notes=data.their_notes,
            verdict=data.verdict,
        )
        db.add(comparison)
        db.commit()
        db.refresh(comparison)
        return FeatureComparisonResponse.model_validate(comparison)

    @staticmethod
    def list_comparisons(
        db: Session,
        competitor_id: uuid.UUID,
        verdict: Optional[ComparisonVerdict] = None,
    ) -> List[FeatureComparisonResponse]:
        query = db.query(FeatureComparison).filter(
            FeatureComparison.competitor_id == competitor_id,
        )
        if verdict:
            query = query.filter(FeatureComparison.verdict == verdict)

        items = query.order_by(desc(FeatureComparison.created_at)).all()
        return [FeatureComparisonResponse.model_validate(i) for i in items]

    @staticmethod
    def update_comparison(
        db: Session,
        comparison_id: uuid.UUID,
        data: FeatureComparisonUpdate,
    ) -> Optional[FeatureComparisonResponse]:
        comparison = db.query(FeatureComparison).filter(
            FeatureComparison.id == comparison_id,
        ).first()
        if not comparison:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(comparison, key, value)

        db.commit()
        db.refresh(comparison)
        return FeatureComparisonResponse.model_validate(comparison)

    @staticmethod
    def delete_comparison(
        db: Session,
        comparison_id: uuid.UUID,
    ) -> bool:
        comparison = db.query(FeatureComparison).filter(
            FeatureComparison.id == comparison_id,
        ).first()
        if not comparison:
            return False
        db.delete(comparison)
        db.commit()
        return True

    # ── Metric Snapshots ─────────────────────────────────────────────

    @staticmethod
    def create_snapshot(
        db: Session,
        competitor_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MetricSnapshotCreate,
    ) -> Optional[MetricSnapshotResponse]:
        competitor = db.query(CompetitorProject).filter(
            CompetitorProject.id == competitor_id,
        ).first()
        if not competitor:
            return None

        snapshot = MetricSnapshot(
            competitor_id=competitor_id,
            recorded_by_id=user_id,
            stars=data.stars,
            forks=data.forks,
            contributors=data.contributors,
            downloads=data.downloads,
            open_issues=data.open_issues,
            monthly_active_users=data.monthly_active_users,
            custom_metrics=data.custom_metrics,
            notes=data.notes,
            snapshot_date=data.snapshot_date,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return MetricSnapshotResponse.model_validate(snapshot)

    @staticmethod
    def list_snapshots(
        db: Session,
        competitor_id: uuid.UUID,
        limit: int = 20,
    ) -> MetricSnapshotListResponse:
        query = db.query(MetricSnapshot).filter(
            MetricSnapshot.competitor_id == competitor_id,
        )
        total = query.count()
        items = (
            query.order_by(desc(MetricSnapshot.snapshot_date))
            .limit(limit)
            .all()
        )
        return MetricSnapshotListResponse(
            items=[MetricSnapshotResponse.model_validate(i) for i in items],
            total=total,
        )

    @staticmethod
    def get_latest_snapshot(
        db: Session,
        competitor_id: uuid.UUID,
    ) -> Optional[MetricSnapshotResponse]:
        snapshot = (
            db.query(MetricSnapshot)
            .filter(MetricSnapshot.competitor_id == competitor_id)
            .order_by(desc(MetricSnapshot.snapshot_date))
            .first()
        )
        if not snapshot:
            return None
        return MetricSnapshotResponse.model_validate(snapshot)

    @staticmethod
    def delete_snapshot(
        db: Session,
        snapshot_id: uuid.UUID,
    ) -> bool:
        snapshot = db.query(MetricSnapshot).filter(
            MetricSnapshot.id == snapshot_id,
        ).first()
        if not snapshot:
            return False
        db.delete(snapshot)
        db.commit()
        return True

    # ── Insights ─────────────────────────────────────────────────────

    @staticmethod
    def get_insight_report(
        db: Session,
        competitor_id: uuid.UUID,
    ) -> Optional[CompetitorInsightReport]:
        competitor = db.query(CompetitorProject).filter(
            CompetitorProject.id == competitor_id,
        ).first()
        if not competitor:
            return None

        comparisons = (
            db.query(FeatureComparison)
            .filter(FeatureComparison.competitor_id == competitor_id)
            .order_by(desc(FeatureComparison.created_at))
            .all()
        )

        latest_snapshot = (
            db.query(MetricSnapshot)
            .filter(MetricSnapshot.competitor_id == competitor_id)
            .order_by(desc(MetricSnapshot.snapshot_date))
            .first()
        )

        snapshot_count = (
            db.query(func.count(MetricSnapshot.id))
            .filter(MetricSnapshot.competitor_id == competitor_id)
            .scalar()
        )

        verdict_summary: Dict[str, int] = {}
        for c in comparisons:
            v = c.verdict.value
            verdict_summary[v] = verdict_summary.get(v, 0) + 1

        return CompetitorInsightReport(
            competitor=CompetitorResponse.model_validate(competitor),
            feature_comparisons=[
                FeatureComparisonResponse.model_validate(c) for c in comparisons
            ],
            latest_snapshot=(
                MetricSnapshotResponse.model_validate(latest_snapshot)
                if latest_snapshot
                else None
            ),
            snapshot_count=snapshot_count or 0,
            verdict_summary=verdict_summary,
        )

    @staticmethod
    def get_threat_summary(
        db: Session,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """Return count of competitors per threat level for a project."""
        rows = (
            db.query(
                CompetitorProject.threat_level,
                func.count(CompetitorProject.id),
            )
            .filter(CompetitorProject.project_id == project_id)
            .group_by(CompetitorProject.threat_level)
            .all()
        )
        return {row[0].value: row[1] for row in rows}
