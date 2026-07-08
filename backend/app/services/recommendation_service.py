from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bookmark import Bookmark
from app.models.follower import Follower
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_skill import ProjectSkill
from app.models.user_skill import UserSkill


class RecommendationService:
    """
    Business logic for generating personalized project recommendations.

    Scoring factors and default weights:
      - Skill Match     (40%): overlap between user's skills and project's skills
      - Contribution    (25%): user is/was a member of the project
      - Bookmark        (20%): user has bookmarked the project
      - Organization    (15%): user follows the project owner or owns an
                               organization associated with the project owner
    """

    # ----------------------------------------------------------
    # Scoring Weights
    # ----------------------------------------------------------

    SKILL_WEIGHT: float = 0.40
    CONTRIBUTION_WEIGHT: float = 0.25
    BOOKMARK_WEIGHT: float = 0.20
    ORG_WEIGHT: float = 0.15

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    @staticmethod
    def get_recommended_projects(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Return (paginated_scored_results, total_count).

        Each result dict contains:
          - project            : Project ORM instance
          - score              : float (0-100)
          - skill_match_count  : int
          - total_skills       : int
          - is_previous_contribution : bool
          - is_bookmarked            : bool
          - is_org_related           : bool
        """

        # ---- 1. Load user's reference data into sets for O(1) lookup ----

        user_skill_ids: set[uuid.UUID] = set(
            db.scalars(
                select(UserSkill.skill_id).where(UserSkill.user_id == user_id)
            ).all()
        )

        contributed_project_ids: set[uuid.UUID] = set(
            db.scalars(
                select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
            ).all()
        )

        bookmarked_project_ids: set[uuid.UUID] = set(
            db.scalars(
                select(Bookmark.project_id).where(Bookmark.user_id == user_id)
            ).all()
        )

        followed_user_ids: set[uuid.UUID] = set(
            db.scalars(
                select(Follower.following_id).where(Follower.follower_id == user_id)
            ).all()
        )

        # Organisations where the current user is the owner
        user_org_owner_ids: set[uuid.UUID] = set(
            db.scalars(
                select(Organization.owner_id).where(Organization.owner_id == user_id)
            ).all()
        )

        # ---- 2. Load candidate projects (non-archived, not owned by user) ----

        all_projects: list[Project] = list(
            db.scalars(
                select(Project)
                .where(
                    Project.is_archived == False,  # noqa: E712
                    Project.owner_id != user_id,
                )
                .order_by(Project.created_at.desc())
            ).all()
        )

        total_count = len(all_projects)
        if total_count == 0:
            return [], 0

        # ---- 3. Batch-load project skills in a single query ----

        project_ids = [p.id for p in all_projects]

        project_skills_rows = db.execute(
            select(ProjectSkill.project_id, ProjectSkill.skill_id).where(
                ProjectSkill.project_id.in_(project_ids)
            )
        ).all()

        project_skills_map: dict[uuid.UUID, set[uuid.UUID]] = {}
        for proj_id, skill_id in project_skills_rows:
            project_skills_map.setdefault(proj_id, set()).add(skill_id)

        # ---- 4. Score every candidate project ----

        scored: list[dict] = []
        for project in all_projects:
            proj_skill_ids = project_skills_map.get(project.id, set())
            total_skills = len(proj_skill_ids)
            matching_skills = (
                len(proj_skill_ids & user_skill_ids) if user_skill_ids else 0
            )

            skill_ratio = matching_skills / max(total_skills, 1)

            is_contributor = project.id in contributed_project_ids
            is_bookmarked = project.id in bookmarked_project_ids
            is_org_related = (
                project.owner_id in followed_user_ids
                or project.owner_id in user_org_owner_ids
            )

            score = (
                skill_ratio * RecommendationService.SKILL_WEIGHT
                + float(is_contributor) * RecommendationService.CONTRIBUTION_WEIGHT
                + float(is_bookmarked) * RecommendationService.BOOKMARK_WEIGHT
                + float(is_org_related) * RecommendationService.ORG_WEIGHT
            ) * 100  # normalise to 0-100

            scored.append(
                {
                    "project": project,
                    "score": round(score, 2),
                    "skill_match_count": matching_skills,
                    "total_skills": total_skills,
                    "is_previous_contribution": is_contributor,
                    "is_bookmarked": is_bookmarked,
                    "is_org_related": is_org_related,
                }
            )

        # ---- 5. Rank: highest score first, then newest ----

        scored.sort(key=lambda x: (-x["score"], _project_sort_key(x["project"])))

        # ---- 6. Paginate ----

        paginated = scored[offset : offset + limit]

        return paginated, total_count


# -------------------------------------------------------------------
# Helper
# -------------------------------------------------------------------


def _project_sort_key(project: Project) -> float:
    """
    Return a sortable numeric value derived from created_at.
    Posix timestamp is used so that newer projects sort higher
    (the outer sort uses descending order).
    """
    return project.created_at.timestamp() if project.created_at else 0.0
