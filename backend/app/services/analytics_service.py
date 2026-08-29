from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.hackathon import Hackathon
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.analytics import (
    ActiveUsersOverview,
    ConversionMetric,
    DAUMetric,
    DailyProjectMetric,
    PlatformAnalyticsResponse,
    PlatformSocialProofResponse,
    ProjectGrowthMetric,
    RetentionMetric,
)
from app.schemas.profile_analytics import ProfileAnalyticsResponse


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

    @staticmethod
    def log_profile_click(
        db: Session,
        click_type: str,
        target_user_id: uuid.UUID,
        entity_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> None:
        from app.models.centralized_analytics import CentralizedAnalyticsEvent

        event = CentralizedAnalyticsEvent(
            event_type=f"{click_type}_click",
            user_id=user_id,
            properties={
                "target_user_id": str(target_user_id),
                "entity_id": str(entity_id) if entity_id else None,
            },
        )
        db.add(event)
        db.commit()

    @staticmethod
    def get_profile_analytics(
        db: Session,
        user_id: uuid.UUID,
    ) -> ProfileAnalyticsResponse:
        from datetime import datetime, timedelta, timezone
        from app.models.profile_view import ProfileView
        from app.models.centralized_analytics import CentralizedAnalyticsEvent
        from app.models.follower import Follower
        from app.schemas.profile_analytics import (
            ProfileAnalyticsResponse,
            ProfileAnalyticsSummary,
            ProfileAnalyticSummaryItem,
            ProfileAnalyticTrendItem,
        )

        now = datetime.now(timezone.utc)
        today = now.date()

        # Ranges
        start_current = today - timedelta(days=6)
        start_previous = today - timedelta(days=13)

        start_current_dt = datetime.combine(
            start_current, datetime.min.time(), tzinfo=timezone.utc
        )
        start_previous_dt = datetime.combine(
            start_previous, datetime.min.time(), tzinfo=timezone.utc
        )

        # Database dialect check for JSON querying compatibility (SQLite vs PostgreSQL)
        bind = db.get_bind()
        is_postgres = bind is not None and bind.dialect.name == "postgresql"

        # 1. Profile Views
        views_all = db.scalars(
            select(ProfileView).where(ProfileView.viewed_user_id == user_id)
        ).all()

        # 2. Search Appearances
        if is_postgres:
            search_stmt = select(CentralizedAnalyticsEvent).where(
                CentralizedAnalyticsEvent.event_type == "profile_search_appearance",
                CentralizedAnalyticsEvent.properties["target_user_id"].astext
                == str(user_id),
            )
        else:
            search_stmt = select(CentralizedAnalyticsEvent).where(
                CentralizedAnalyticsEvent.event_type == "profile_search_appearance"
            )
        search_all = db.scalars(search_stmt).all()
        if not is_postgres:
            search_all = [
                r
                for r in search_all
                if r.properties
                and str(r.properties.get("target_user_id")) == str(user_id)
            ]

        # 3. Connection Requests (Follows)
        follows_all = db.scalars(
            select(Follower).where(Follower.following_id == user_id)
        ).all()

        # 4. Repo Clicks
        if is_postgres:
            repo_stmt = select(CentralizedAnalyticsEvent).where(
                CentralizedAnalyticsEvent.event_type == "repository_click",
                CentralizedAnalyticsEvent.properties["target_user_id"].astext
                == str(user_id),
            )
        else:
            repo_stmt = select(CentralizedAnalyticsEvent).where(
                CentralizedAnalyticsEvent.event_type == "repository_click"
            )
        repo_all = db.scalars(repo_stmt).all()
        if not is_postgres:
            repo_all = [
                r
                for r in repo_all
                if r.properties
                and str(r.properties.get("target_user_id")) == str(user_id)
            ]

        # 5. Project Clicks
        if is_postgres:
            project_stmt = select(CentralizedAnalyticsEvent).where(
                CentralizedAnalyticsEvent.event_type == "project_click",
                CentralizedAnalyticsEvent.properties["target_user_id"].astext
                == str(user_id),
            )
        else:
            project_stmt = select(CentralizedAnalyticsEvent).where(
                CentralizedAnalyticsEvent.event_type == "project_click"
            )
        project_all = db.scalars(project_stmt).all()
        if not is_postgres:
            project_all = [
                r
                for r in project_all
                if r.properties
                and str(r.properties.get("target_user_id")) == str(user_id)
            ]

        # Function to aggregate counts
        def get_summary_and_growth(items) -> ProfileAnalyticSummaryItem:
            total = len(items)
            current_count = 0
            previous_count = 0

            for item in items:
                created_at = getattr(item, "created_at", None)
                if created_at:
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    if created_at >= start_current_dt:
                        current_count += 1
                    elif created_at >= start_previous_dt:
                        previous_count += 1

            if previous_count == 0:
                growth_pct = 100.0 if current_count > 0 else 0.0
            else:
                growth_pct = round(
                    ((current_count - previous_count) / previous_count) * 100, 1
                )

            return ProfileAnalyticSummaryItem(total=total, growth_pct=growth_pct)

        # Generate Summaries
        summary = ProfileAnalyticsSummary(
            profile_views=get_summary_and_growth(views_all),
            search_appearances=get_summary_and_growth(search_all),
            connection_requests=get_summary_and_growth(follows_all),
            repository_clicks=get_summary_and_growth(repo_all),
            project_clicks=get_summary_and_growth(project_all),
        )

        # Generate Daily Trends (last 7 days, from start_current to today)
        trends_map = {}
        for i in range(7):
            d = start_current + timedelta(days=i)
            trends_map[d.strftime("%Y-%m-%d")] = {
                "profile_views": 0,
                "search_appearances": 0,
                "connection_requests": 0,
                "repository_clicks": 0,
                "project_clicks": 0,
            }

        for item in views_all:
            created_at = getattr(item, "created_at", None)
            if created_at:
                d_str = created_at.strftime("%Y-%m-%d")
                if d_str in trends_map:
                    trends_map[d_str]["profile_views"] += 1

        for item in search_all:
            created_at = getattr(item, "created_at", None)
            if created_at:
                d_str = created_at.strftime("%Y-%m-%d")
                if d_str in trends_map:
                    trends_map[d_str]["search_appearances"] += 1

        for item in follows_all:
            created_at = getattr(item, "created_at", None)
            if created_at:
                d_str = created_at.strftime("%Y-%m-%d")
                if d_str in trends_map:
                    trends_map[d_str]["connection_requests"] += 1

        for item in repo_all:
            created_at = getattr(item, "created_at", None)
            if created_at:
                d_str = created_at.strftime("%Y-%m-%d")
                if d_str in trends_map:
                    trends_map[d_str]["repository_clicks"] += 1

        for item in project_all:
            created_at = getattr(item, "created_at", None)
            if created_at:
                d_str = created_at.strftime("%Y-%m-%d")
                if d_str in trends_map:
                    trends_map[d_str]["project_clicks"] += 1

        trends = []
        for d_str, counts in sorted(trends_map.items()):
            trends.append(
                ProfileAnalyticTrendItem(
                    date=d_str,
                    profile_views=counts["profile_views"],
                    search_appearances=counts["search_appearances"],
                    connection_requests=counts["connection_requests"],
                    repository_clicks=counts["repository_clicks"],
                    project_clicks=counts["project_clicks"],
                )
            )

        return ProfileAnalyticsResponse(summary=summary, trends=trends)

    @staticmethod
    def get_social_proof(db: Session) -> PlatformSocialProofResponse:
        """
        Compute platform growth and adoption numbers for the landing page social proof section:
        - Developers (registered active users)
        - Projects (total published projects)
        - Teams (teams formed / projects with active members)
        - Organizations (registered organizations)
        - Hackathons (hosted hackathon events)
        """
        total_developers = (
            db.scalar(
                select(func.count(User.id)).where(
                    User.is_active.is_(True),
                    User.deleted_at.is_(None),
                )
            )
            or 0
        )

        total_projects = (
            db.scalar(
                select(func.count(Project.id)).where(
                    Project.deleted_at.is_(None),
                )
            )
            or 0
        )

        teams_formed = (
            db.scalar(
                select(func.count(distinct(ProjectMember.project_id))).where(
                    ProjectMember.is_active.is_(True)
                )
            )
            or 0
        )

        total_organizations = db.scalar(select(func.count(Organization.id))) or 0

        total_hackathons = db.scalar(select(func.count(Hackathon.id))) or 0

        return PlatformSocialProofResponse(
            developers=total_developers,
            projects=total_projects,
            teams=teams_formed,
            organizations=total_organizations,
            hackathons=total_hackathons,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )
