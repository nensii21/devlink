from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.analytics import (
    ActiveUsersOverview,
    ConversionMetric,
    DAUMetric,
    DailyProjectMetric,
    PlatformAnalyticsResponse,
    ProjectGrowthMetric,
    RetentionMetric,
)


class AnalyticsService:
    """
    Business logic for platform-wide analytics and performance tracking dashboard metrics.
    Computes DAU, WAU, MAU, Retention Rates, Conversion Rates, and Project Growth.
    """

    @staticmethod
    def get_platform_analytics(
        db: Session,
        days: int = 30,
    ) -> PlatformAnalyticsResponse:
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        # ------------------------------------------------------------------
        # 1. DAU / WAU / MAU Calculation
        # ------------------------------------------------------------------
        h24_ago = now - timedelta(hours=24)
        d7_ago = now - timedelta(days=7)
        d30_ago = now - timedelta(days=30)

        # DAU: active in last 24h (last_login or created_at within 24h)
        dau_stmt = select(func.count(User.id)).where(
            User.is_active.is_(True),
            (User.last_login >= h24_ago)
            | ((User.last_login.is_(None)) & (User.created_at >= h24_ago)),
        )
        dau = db.scalar(dau_stmt) or 0

        # WAU: active in last 7 days
        wau_stmt = select(func.count(User.id)).where(
            User.is_active.is_(True),
            (User.last_login >= d7_ago)
            | ((User.last_login.is_(None)) & (User.created_at >= d7_ago)),
        )
        wau = db.scalar(wau_stmt) or 0

        # MAU: active in last 30 days
        mau_stmt = select(func.count(User.id)).where(
            User.is_active.is_(True),
            (User.last_login >= d30_ago)
            | ((User.last_login.is_(None)) & (User.created_at >= d30_ago)),
        )
        mau = db.scalar(mau_stmt) or 0

        # Daily DAU trend calculation over requested days
        users_in_window = db.scalars(select(User).where(User.is_active.is_(True))).all()

        daily_active_map: Dict[str, set] = {}
        for i in range(days - 1, -1, -1):
            day_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_active_map[day_str] = set()

        for u in users_in_window:
            user_dates = set()
            user_dt = u.last_login or u.created_at
            if user_dt:
                if user_dt.tzinfo is None:
                    user_dt = user_dt.replace(tzinfo=timezone.utc)
                d_str = user_dt.strftime("%Y-%m-%d")
                if d_str in daily_active_map:
                    user_dates.add(d_str)
            for d_str in user_dates:
                daily_active_map[d_str].add(u.id)

        daily_dau_metrics: List[DAUMetric] = []
        for day_str, user_set in daily_active_map.items():
            daily_dau_metrics.append(
                DAUMetric(
                    date=day_str,
                    active_users=len(user_set),
                )
            )

        active_overview = ActiveUsersOverview(
            dau=dau,
            wau=wau,
            mau=mau,
            daily_trend=daily_dau_metrics,
        )

        # ------------------------------------------------------------------
        # 2. Retention Metrics Calculation
        # ------------------------------------------------------------------
        # Eligible 7d users: registered >7d ago
        eligible_7d_stmt = select(func.count(User.id)).where(
            User.created_at <= d7_ago,
            User.is_active.is_(True),
        )
        eligible_7d_users = db.scalar(eligible_7d_stmt) or 0

        # Retained 7d users: registered >7d ago AND active in last 7d
        retained_7d_stmt = select(func.count(User.id)).where(
            User.created_at <= d7_ago,
            User.is_active.is_(True),
            (User.last_login >= d7_ago) | (User.updated_at >= d7_ago),
        )
        retained_7d_users = db.scalar(retained_7d_stmt) or 0

        retention_7d_pct = (
            round((retained_7d_users / eligible_7d_users) * 100, 2)
            if eligible_7d_users > 0
            else 0.0
        )

        # Eligible 30d users: registered >30d ago
        eligible_30d_stmt = select(func.count(User.id)).where(
            User.created_at <= d30_ago,
            User.is_active.is_(True),
        )
        eligible_30d_users = db.scalar(eligible_30d_stmt) or 0

        # Retained 30d users: registered >30d ago AND active in last 30d
        retained_30d_stmt = select(func.count(User.id)).where(
            User.created_at <= d30_ago,
            User.is_active.is_(True),
            (User.last_login >= d30_ago) | (User.updated_at >= d30_ago),
        )
        retained_30d_users = db.scalar(retained_30d_stmt) or 0

        retention_30d_pct = (
            round((retained_30d_users / eligible_30d_users) * 100, 2)
            if eligible_30d_users > 0
            else 0.0
        )

        retention_metrics = RetentionMetric(
            retention_7d_pct=retention_7d_pct,
            retention_30d_pct=retention_30d_pct,
            retained_7d_users=retained_7d_users,
            eligible_7d_users=eligible_7d_users,
            retained_30d_users=retained_30d_users,
            eligible_30d_users=eligible_30d_users,
        )

        # ------------------------------------------------------------------
        # 3. Conversion Funnel Metrics
        # ------------------------------------------------------------------
        total_users_stmt = select(func.count(User.id)).where(User.is_active.is_(True))
        total_users = db.scalar(total_users_stmt) or 0

        # Completed profiles count (headline or bio provided)
        completed_profiles_stmt = select(func.count(User.id)).where(
            User.is_active.is_(True),
            (User.headline.is_not(None) & (User.headline != ""))
            | (User.bio.is_not(None) & (User.bio != "")),
        )
        completed_profiles_count = db.scalar(completed_profiles_stmt) or 0

        profile_completion_pct = (
            round((completed_profiles_count / total_users) * 100, 2)
            if total_users > 0
            else 0.0
        )

        # Project Creators count
        creators_stmt = select(func.count(func.distinct(Project.owner_id)))
        project_creators_count = db.scalar(creators_stmt) or 0

        project_creator_pct = (
            round((project_creators_count / total_users) * 100, 2)
            if total_users > 0
            else 0.0
        )

        # Application stats
        total_apps_stmt = select(func.count(Application.id))
        total_applications_count = db.scalar(total_apps_stmt) or 0

        accepted_apps_stmt = select(func.count(Application.id)).where(
            Application.status == ApplicationStatus.ACCEPTED
        )
        accepted_applications_count = db.scalar(accepted_apps_stmt) or 0

        application_acceptance_pct = (
            round((accepted_applications_count / total_applications_count) * 100, 2)
            if total_applications_count > 0
            else 0.0
        )

        applicants_stmt = select(func.count(func.distinct(Application.applicant_id)))
        unique_applicants_count = db.scalar(applicants_stmt) or 0

        user_application_pct = (
            round((unique_applicants_count / total_users) * 100, 2)
            if total_users > 0
            else 0.0
        )

        conversion_metrics = ConversionMetric(
            profile_completion_pct=profile_completion_pct,
            project_creator_pct=project_creator_pct,
            application_acceptance_pct=application_acceptance_pct,
            user_application_pct=user_application_pct,
            completed_profiles_count=completed_profiles_count,
            project_creators_count=project_creators_count,
            total_applications_count=total_applications_count,
            accepted_applications_count=accepted_applications_count,
        )

        # ------------------------------------------------------------------
        # 4. Project Growth Calculation
        # ------------------------------------------------------------------
        total_projects_stmt = select(func.count(Project.id))
        total_projects = db.scalar(total_projects_stmt) or 0

        new_projects_period_stmt = select(func.count(Project.id)).where(
            Project.created_at >= start_date
        )
        new_projects_period = db.scalar(new_projects_period_stmt) or 0

        prior_projects = total_projects - new_projects_period
        if prior_projects > 0:
            growth_rate_pct = round((new_projects_period / prior_projects) * 100, 2)
        else:
            growth_rate_pct = 100.0 if new_projects_period > 0 else 0.0

        # Daily project creation breakdown over requested timeframe
        projects_in_window = db.scalars(
            select(Project).where(Project.created_at >= start_date)
        ).all()

        daily_projects_map: Dict[str, int] = {}
        for i in range(days - 1, -1, -1):
            day_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_projects_map[day_str] = 0

        for p in projects_in_window:
            if p.created_at:
                created_dt = p.created_at
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                d_str = created_dt.strftime("%Y-%m-%d")
                if d_str in daily_projects_map:
                    daily_projects_map[d_str] += 1

        daily_growth_metrics: List[DailyProjectMetric] = []
        running_total = prior_projects
        for day_str, count in daily_projects_map.items():
            running_total += count
            daily_growth_metrics.append(
                DailyProjectMetric(
                    date=day_str,
                    new_projects=count,
                    cumulative_projects=running_total,
                )
            )

        project_growth_metrics = ProjectGrowthMetric(
            total_projects=total_projects,
            new_projects_period=new_projects_period,
            growth_rate_pct=growth_rate_pct,
            daily_growth=daily_growth_metrics,
        )

        return PlatformAnalyticsResponse(
            timeframe_days=days,
            active_users=active_overview,
            retention=retention_metrics,
            conversion=conversion_metrics,
            project_growth=project_growth_metrics,
        )
