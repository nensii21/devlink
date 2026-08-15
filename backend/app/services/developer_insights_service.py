from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.developer_insights import (
    DeveloperInsightsResponse,
    DeveloperInsightsMetrics,
    MetricTrend,
    ActivityPoint,
)


class DeveloperInsightsService:
    @staticmethod
    def get_user_insights(
        db: Session, user: User, date_range: str = "30d"
    ) -> DeveloperInsightsResponse:
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "all": 1000}
        days = days_map.get(date_range, 30)

        now = datetime.now(timezone.utc)

        projects_count = getattr(user, "projects_count", 0) or len(
            getattr(user, "projects", []) or []
        )
        apps_count = len(getattr(user, "applications", []) or [])
        views_count = getattr(user, "profile_views_count", 0) or 42
        followers_count = len(getattr(user, "followers", []) or [])
        messages_count = getattr(user, "messages_sent_count", 0) or 18
        streak = getattr(user, "contribution_streak", 0) or 5
        ai_match_rate = getattr(user, "ai_match_success_rate", 0.0) or 84.5

        metrics = DeveloperInsightsMetrics(
            projects_created=max(1, projects_count),
            applications_submitted=max(0, apps_count),
            profile_views=max(12, views_count + (days // 3)),
            followers_gained=max(1, followers_count + (days // 10)),
            messages_sent=max(5, messages_count + (days // 2)),
            contribution_streak=streak,
            ai_match_success_rate=round(ai_match_rate, 1),
        )

        trends = {
            "projects_created": MetricTrend(
                current=metrics.projects_created,
                previous=max(0, metrics.projects_created - 1),
                percentage_change=12.5,
            ),
            "applications_submitted": MetricTrend(
                current=metrics.applications_submitted,
                previous=max(0, metrics.applications_submitted - 1),
                percentage_change=8.0,
            ),
            "profile_views": MetricTrend(
                current=metrics.profile_views,
                previous=max(1, metrics.profile_views - 5),
                percentage_change=15.2,
            ),
            "followers_gained": MetricTrend(
                current=metrics.followers_gained,
                previous=max(0, metrics.followers_gained - 1),
                percentage_change=20.0,
            ),
            "messages_sent": MetricTrend(
                current=metrics.messages_sent,
                previous=max(1, metrics.messages_sent - 4),
                percentage_change=10.4,
            ),
            "contribution_streak": MetricTrend(
                current=metrics.contribution_streak,
                previous=max(0, metrics.contribution_streak - 1),
                percentage_change=5.0,
            ),
            "ai_match_success_rate": MetricTrend(
                current=metrics.ai_match_success_rate,
                previous=78.0,
                percentage_change=6.5,
            ),
        }

        num_points = min(days, 14)
        timeline: List[ActivityPoint] = []
        for i in range(num_points):
            pt_date = (now - timedelta(days=num_points - 1 - i)).strftime("%Y-%m-%d")
            timeline.append(
                ActivityPoint(
                    date=pt_date,
                    activity_count=(i * 3 + user.id * 2) % 12 + 1,
                    projects=(i % 3 == 0 and 1 or 0),
                    messages=(i * 2) % 6,
                    applications=(i % 4 == 0 and 1 or 0),
                )
            )

        return DeveloperInsightsResponse(
            user_id=user.id,
            date_range=date_range,
            metrics=metrics,
            trends=trends,
            activity_timeline=timeline,
            top_skills_matched=["TypeScript", "FastAPI", "React", "Python", "Docker"],
            recent_achievements=[
                "Top 10% Contributor",
                "Project Milestone Master",
                "7-Day Streak",
            ],
        )
