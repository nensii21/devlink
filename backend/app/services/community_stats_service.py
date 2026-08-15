from __future__ import annotations

import calendar
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.builder_flare import BuilderFlare, FlareStatus
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.skill import Skill
from app.models.user import User
from app.models.user_skill import UserSkill
from app.schemas.community_stats import (
    CommunityStatsResponse,
    SkillStat,
    TechnologyStat,
)


class CommunityStatsService:
    """
    Computes platform-wide community statistics for the Community Statistics
    Dashboard: developer counts, project activity, team formation, open
    opportunities, monthly contributions and registrations, plus the most
    popular skills and trending technologies.
    """

    @staticmethod
    def _month_bounds(now: datetime) -> tuple[datetime, datetime]:
        """Return the start of the current calendar month and the next month."""
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        _, last_day = calendar.monthrange(now.year, now.month)
        month_end = now.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )
        return month_start, month_end

    @staticmethod
    def get_community_stats(db: Session, days: int = 30) -> CommunityStatsResponse:
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)
        month_start, _ = CommunityStatsService._month_bounds(now)

        # ------------------------------------------------------------------
        # 1. Total Developers
        # ------------------------------------------------------------------
        total_developers = (
            db.scalar(
                select(func.count(User.id)).where(
                    User.is_active.is_(True),
                    User.deleted_at.is_(None),
                )
            )
            or 0
        )

        # ------------------------------------------------------------------
        # 2. Active Projects (published, not archived, not deleted)
        # ------------------------------------------------------------------
        active_projects = (
            db.scalar(
                select(func.count(Project.id)).where(
                    Project.is_published.is_(True),
                    Project.is_archived.is_(False),
                    Project.deleted_at.is_(None),
                )
            )
            or 0
        )

        # ------------------------------------------------------------------
        # 3. Teams Formed (distinct projects with at least one active member)
        # ------------------------------------------------------------------
        teams_formed = (
            db.scalar(
                select(func.count(distinct(ProjectMember.project_id))).where(
                    ProjectMember.is_active.is_(True)
                )
            )
            or 0
        )

        # ------------------------------------------------------------------
        # 4. Open Opportunities (open builder flares)
        # ------------------------------------------------------------------
        open_opportunities = (
            db.scalar(
                select(func.count(BuilderFlare.id)).where(
                    BuilderFlare.status == FlareStatus.OPEN
                )
            )
            or 0
        )

        # ------------------------------------------------------------------
        # 5. Contributions This Month (accepted applications this calendar month)
        # ------------------------------------------------------------------
        contributions_this_month = (
            db.scalar(
                select(func.count(Application.id)).where(
                    Application.status == ApplicationStatus.ACCEPTED,
                    Application.updated_at >= month_start,
                )
            )
            or 0
        )

        # ------------------------------------------------------------------
        # 6. New Users This Month
        # ------------------------------------------------------------------
        new_users_this_month = (
            db.scalar(
                select(func.count(User.id)).where(
                    User.created_at >= month_start,
                    User.deleted_at.is_(None),
                )
            )
            or 0
        )

        # ------------------------------------------------------------------
        # 7. Most Popular Skills (top 10 by number of holders)
        # ------------------------------------------------------------------
        skill_rows = db.execute(
            select(Skill.name, func.count(distinct(UserSkill.user_id)).label("cnt"))
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(
                UserSkill.user_id.in_(select(User.id).where(User.deleted_at.is_(None)))
            )
            .group_by(Skill.id, Skill.name)
            .order_by(func.count(distinct(UserSkill.user_id)).desc())
            .limit(10)
        ).all()
        most_popular_skills: List[SkillStat] = [
            SkillStat(name=name, count=cnt) for name, cnt in skill_rows
        ]

        # ------------------------------------------------------------------
        # 8. Trending Technologies (languages + tags across active projects)
        # ------------------------------------------------------------------
        tech_counter: Dict[str, int] = Counter()
        projects = db.scalars(
            select(Project).where(
                Project.is_published.is_(True),
                Project.is_archived.is_(False),
                Project.deleted_at.is_(None),
                Project.created_at >= start_date,
            )
        ).all()
        for proj in projects:
            if proj.language:
                tech_counter[proj.language.strip()] += 1
            if proj.tags:
                if isinstance(proj.tags, list):
                    tags = proj.tags
                else:
                    tags = [proj.tags]
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        tech_counter[tag.strip()] += 1

        trending_technologies: List[TechnologyStat] = [
            TechnologyStat(name=name, count=cnt)
            for name, cnt in tech_counter.most_common(10)
        ]

        return CommunityStatsResponse(
            generated_at=now,
            timeframe_days=days,
            total_developers=total_developers,
            active_projects=active_projects,
            teams_formed=teams_formed,
            open_opportunities=open_opportunities,
            contributions_this_month=contributions_this_month,
            new_users_this_month=new_users_this_month,
            most_popular_skills=most_popular_skills,
            trending_technologies=trending_technologies,
        )
