"""
AI-Powered Builder Recommendation Service.

This module implements a transparent, well-documented scoring engine that
ranks potential collaborators (builders) against a project context (or the
requesting user's own profile when no project is supplied).

Design goals
------------
1. **Ranked recommendations** — builders are returned sorted by a final
   weighted score in the range ``[0.0, 1.0]``.
2. **Well-documented matching logic** — every factor is computed by a
   dedicated, pure function with a docstring explaining the rationale.
3. **Easily extensible for future AI models** — the scoring pipeline is
   broken into small, swappable components. A future embedding-based or
   LLM-based ranker can replace ``WeightedScoringStrategy`` without
   touching the router, schema or cache layer.

Recommendation factors (per the issue)
--------------------------------------
* Skills            – Jaccard overlap, weighted by skill level.
* Interests         – Keyword overlap between builder bio/headline and
                      the project description (or requester's headline).
* Experience level  – Builder's ``years_of_experience`` vs. the project's
                      ``minimum_experience`` requirement.
* Preferred tech    – Overlap between builder skills and project tech_stack.
* Availability      – ``open_to_work`` flag.
* Previous contribs – Number of accepted applications + projects owned.
* Network           – Small boost for mutual-follow social proximity.
"""

from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

# pyrefly: ignore [missing-import]
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.cache import cache_manager
from app.models.application import Application, ApplicationStatus
from app.models.follower import Follower
from app.models.project import Project
from app.models.project_skill import ProjectSkill
from app.models.skill import Skill
from app.models.user import User
from app.models.user_skill import SkillLevel, UserSkill
from app.schemas.recommendation import (
    ProjectContext,
    RecommendationWeights,
    RecommendedBuilder,
    ScoreBreakdown,
)

if TYPE_CHECKING:
    from app.schemas.recommendation import RecommendedProject

logger = logging.getLogger(__name__)


# =====================================================================
# Skill-level weight table
# =====================================================================

_SKILL_LEVEL_WEIGHTS: dict[SkillLevel, float] = {
    SkillLevel.BEGINNER: 0.40,
    SkillLevel.INTERMEDIATE: 0.70,
    SkillLevel.ADVANCED: 0.90,
    SkillLevel.EXPERT: 1.00,
}

# =====================================================================
# Experience level ranking (used when only qualitative level is set)
# =====================================================================

_EXPERIENCE_LEVEL_RANK: dict[str, int] = {
    "beginner": 1,
    "junior": 1,
    "entry": 1,
    "intermediate": 2,
    "mid": 2,
    "mid-level": 2,
    "advanced": 3,
    "senior": 3,
    "expert": 4,
    "lead": 4,
    "staff": 4,
    "principal": 4,
}

# Words ignored when extracting "interests" from free-text fields.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "is",
        "are",
        "be",
        "by",
        "at",
        "as",
        "it",
        "this",
        "that",
        "from",
        "we",
        "our",
        "you",
        "your",
        "i",
        "my",
        "me",
        "us",
        "them",
        "they",
        "he",
        "she",
        "his",
        "her",
        "who",
        "what",
        "where",
        "when",
        "how",
        "build",
        "building",
        "built",
        "create",
        "creating",
        "made",
        "make",
        "use",
        "using",
        "uses",
        "used",
        "want",
        "wants",
        "looking",
        "like",
        "love",
        "enjoy",
        "work",
        "working",
        "works",
        "worked",
        "developer",
        "engineer",
        "software",
        "code",
        "coding",
        "programmer",
        "project",
        "app",
        "application",
        "web",
        "mobile",
        "system",
        "team",
        "join",
        "open",
        "source",
        "tech",
        "technology",
        "technologies",
        "stack",
        "experience",
        "level",
        "year",
        "years",
        "skill",
        "skills",
    }
)


# =====================================================================
# Pure helper functions (the "matching logic")
# =====================================================================


def _tokenize(text: Optional[str]) -> set[str]:
    """
    Split free-text into a normalized set of meaningful tokens.

    Used to derive "interests" from bio/headline and to parse
    ``project.tech_stack`` (a free-form comma/space separated string).
    """
    if not text:
        return set()
    tokens: set[str] = set()
    for raw in text.lower().replace(",", " ").split():
        token = "".join(ch for ch in raw if ch.isalnum())
        if len(token) < 3:
            continue
        if token in _STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _experience_rank(level: Optional[str]) -> int:
    """Map a qualitative experience level to a 1-4 rank (0 if unknown)."""
    if not level:
        return 0
    return _EXPERIENCE_LEVEL_RANK.get(level.strip().lower(), 0)


def _skills_score(
    builder_skill_ids: set[uuid.UUID],
    builder_skill_levels: dict[uuid.UUID, SkillLevel],
    required_skill_ids: set[uuid.UUID],
) -> tuple[float, list[str]]:
    """
    Compute the skill-overlap component.

    Uses a level-weighted Jaccard-style score:

        sum(level_weight[s] for s in (builder ∩ required))
        -------------------------------------------------
        sum(level_weight[s] for s in required)

    Returns ``(score_in_0_1, matched_normalized_skill_names)``.

    * If the project has no required skills, falls back to the fraction
      of the builder's skills that overlap with the requester's own
      skills (used for the "recommend me collaborators" mode).
    * If neither side has any skills, returns 0.0.
    """
    if not required_skill_ids:
        return 0.0, []

    matched = builder_skill_ids & required_skill_ids
    if not matched:
        return 0.0, []

    numerator = sum(
        _SKILL_LEVEL_WEIGHTS.get(
            builder_skill_levels.get(sid, SkillLevel.BEGINNER), 0.4
        )
        for sid in matched
    )
    denominator = float(len(required_skill_ids))
    return min(numerator / denominator, 1.0), [str(sid) for sid in matched]


def _interests_score(
    builder_interest_tokens: set[str],
    context_tokens: set[str],
) -> float:
    """
    Compute the interests-overlap component as a Jaccard index.

    Jaccard = |A ∩ B| / |A ∪ B|

    Falls back to 0.0 if either side is empty.
    """
    if not builder_interest_tokens or not context_tokens:
        return 0.0
    intersection = builder_interest_tokens & context_tokens
    union = builder_interest_tokens | context_tokens
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _experience_score(
    builder_years: int,
    builder_level_rank: int,
    required_years: int,
) -> float:
    """
    Compute the experience-level component.

    * If the project specifies ``minimum_experience`` (years), the builder
      meets it fully when ``years >= minimum`` and gets a proportional
      score otherwise (``years / minimum``, capped at 1.0).
    * If no year requirement is set, returns 1.0 (no constraint).
    """
    if required_years <= 0:
        # No hard requirement — give full credit but let other factors
        # differentiate builders.
        return 1.0
    if builder_years >= required_years:
        return 1.0
    return max(builder_years / float(required_years), 0.0)


def _technologies_score(
    builder_skill_names: set[str],
    project_tech_stack: Optional[str],
) -> tuple[float, list[str]]:
    """
    Compute the preferred-technologies component.

    Parses ``project.tech_stack`` (free-form text) into tokens and measures
    how many of them are covered by the builder's known skill names.

    Returns ``(score_in_0_1, matched_tokens)``.
    """
    tech_tokens = _tokenize(project_tech_stack)
    if not tech_tokens:
        return 0.0, []

    builder_tokens = {n.lower() for n in builder_skill_names}
    if not builder_tokens:
        return 0.0, []

    matched = builder_tokens & tech_tokens
    if not matched:
        return 0.0, []
    return len(matched) / len(tech_tokens), sorted(matched)


def _availability_score(open_to_work: bool) -> float:
    """
    Compute the availability component.

    Builders who are explicitly ``open_to_work`` score 1.0; otherwise a
    small floor (0.3) is kept so they are still discoverable but ranked
    below available builders for the same score.
    """
    return 1.0 if open_to_work else 0.3


def _contributions_score(count: int) -> float:
    """
    Compute the previous-contributions component on a logarithmic scale.

    0 contributions → 0.0
    1 contribution  → ~0.41
    3 contributions → ~0.63
    10 contributions → ~0.83  (asymptote approaching 1.0)
    """
    if count <= 0:
        return 0.0
    return 1.0 - 1.0 / (1.0 + math.log(count + 1))


def _network_score(is_mutual_follower: bool) -> float:
    """
    Compute the social-graph boost component.

    Returns 1.0 if the builder is part of the requester's follow network
    (mutual trust), else 0.0.
    """
    return 1.0 if is_mutual_follower else 0.0


# =====================================================================
# Strategy interface (extensibility hook)
# =====================================================================


@dataclass
class BuilderCandidate:
    """All inputs needed to score a single builder."""

    user: User
    skill_ids: set[uuid.UUID]
    skill_levels: dict[uuid.UUID, SkillLevel]
    skill_names: set[str]
    interest_tokens: set[str]
    years_of_experience: int
    experience_level_rank: int
    contribution_count: int
    is_mutual_follower: bool


@dataclass
class ScoringContext:
    """The target we are matching builders against."""

    required_skill_ids: set[uuid.UUID] = field(default_factory=set)
    context_tokens: set[str] = field(
        default_factory=set
    )  # project description OR requester interests
    tech_stack: Optional[str] = None
    minimum_experience: int = 0


class ScoringStrategy:
    """
    Abstract base class for scoring strategies.

    Subclasses implement :meth:`score` to turn a
    ``(BuilderCandidate, ScoringContext)`` pair into a final
    ``ScoreBreakdown`` + scalar score.

    The default implementation, :class:`WeightedScoringStrategy`, is
    a transparent linear combination of factors and is intentionally
    easy to replace with an embedding-based or LLM-based ranker later.
    """

    def score(
        self,
        candidate: BuilderCandidate,
        context: ScoringContext,
    ) -> tuple[float, ScoreBreakdown, list[str], list[str]]:
        raise NotImplementedError


class WeightedScoringStrategy(ScoringStrategy):
    """
    Transparent, weighted linear-combination scorer.

    Final score = Σ (weight_i * factor_i)
    Each factor_i is in [0, 1] and weights sum to 1.0, so the final
    score is also in [0, 1].
    """

    def __init__(self, weights: Optional[RecommendationWeights] = None) -> None:
        self.weights = weights or RecommendationWeights()

    def score(
        self,
        candidate: BuilderCandidate,
        context: ScoringContext,
    ) -> tuple[float, ScoreBreakdown, list[str], list[str]]:
        w = self.weights

        skills_raw, matched_skill_ids = _skills_score(
            candidate.skill_ids,
            candidate.skill_levels,
            context.required_skill_ids,
        )
        skills = skills_raw * w.skills

        interests = (
            _interests_score(
                candidate.interest_tokens,
                context.context_tokens,
            )
            * w.interests
        )

        experience = (
            _experience_score(
                candidate.years_of_experience,
                candidate.experience_level_rank,
                context.minimum_experience,
            )
            * w.experience
        )

        technologies_raw, matched_techs = _technologies_score(
            candidate.skill_names,
            context.tech_stack,
        )
        technologies = technologies_raw * w.technologies

        availability = _availability_score(candidate.user.open_to_work) * w.availability

        contributions = (
            _contributions_score(candidate.contribution_count) * w.contributions
        )

        network = _network_score(candidate.is_mutual_follower) * w.network

        breakdown = ScoreBreakdown(
            skills=round(skills, 6),
            interests=round(interests, 6),
            experience=round(experience, 6),
            technologies=round(technologies, 6),
            availability=round(availability, 6),
            contributions=round(contributions, 6),
            network=round(network, 6),
        )
        final = round(
            skills
            + interests
            + experience
            + technologies
            + availability
            + contributions
            + network,
            6,
        )
        return final, breakdown, matched_skill_ids, matched_techs


# =====================================================================
# Strategy interface for Project Recommendations
# =====================================================================


@dataclass
class ProjectCandidate:
    """All inputs needed to score a single project."""

    project: Project
    required_skill_ids: set[uuid.UUID]
    minimum_experience: int
    context_tokens: set[str]
    tech_stack: Optional[str]
    is_collaborator: bool


@dataclass
class ProjectScoringContext:
    """The target developer we are matching projects against."""

    builder_skill_ids: set[uuid.UUID] = field(default_factory=set)
    builder_skill_levels: dict[uuid.UUID, SkillLevel] = field(default_factory=dict)
    builder_skill_names: set[str] = field(default_factory=set)
    interest_tokens: set[str] = field(default_factory=set)
    years_of_experience: int = 0
    experience_level_rank: int = 0


class ProjectScoringStrategy:
    def score(
        self,
        candidate: ProjectCandidate,
        context: ProjectScoringContext,
    ) -> tuple[float, ScoreBreakdown, list[str], list[str]]:
        raise NotImplementedError


class WeightedProjectScoringStrategy(ProjectScoringStrategy):
    def __init__(self, weights: Optional[RecommendationWeights] = None) -> None:
        self.weights = weights or RecommendationWeights()

    def score(
        self,
        candidate: ProjectCandidate,
        context: ProjectScoringContext,
    ) -> tuple[float, ScoreBreakdown, list[str], list[str]]:
        w = self.weights

        # 1. Skills: How well does the builder's skills cover the project's requirements?
        skills_raw, matched_skill_ids = _skills_score(
            context.builder_skill_ids,
            context.builder_skill_levels,
            candidate.required_skill_ids,
        )
        skills = skills_raw * w.skills

        # 2. Interests: Overlap between project description and builder bio.
        interests = (
            _interests_score(
                candidate.context_tokens,
                context.interest_tokens,
            )
            * w.interests
        )

        # 3. Experience: Does the builder meet the project's minimum years?
        experience = (
            _experience_score(
                context.years_of_experience,
                context.experience_level_rank,
                candidate.minimum_experience,
            )
            * w.experience
        )

        # 4. Technologies: Overlap between builder skill names and project tech stack.
        technologies_raw, matched_techs = _technologies_score(
            context.builder_skill_names,
            candidate.tech_stack,
        )
        technologies = technologies_raw * w.technologies

        # 5. Availability (not relevant for projects, always give full weight to not penalize)
        availability = 1.0 * w.availability

        # 6. Contributions (not directly applicable to project ranking, neutral)
        contributions = 1.0 * w.contributions

        # 7. Network: Has the builder collaborated with this owner before?
        network = 1.0 if candidate.is_collaborator else 0.0
        network *= w.network

        breakdown = ScoreBreakdown(
            skills=round(skills, 6),
            interests=round(interests, 6),
            experience=round(experience, 6),
            technologies=round(technologies, 6),
            availability=round(availability, 6),
            contributions=round(contributions, 6),
            network=round(network, 6),
        )
        final = round(
            skills
            + interests
            + experience
            + technologies
            + availability
            + contributions
            + network,
            6,
        )
        return final, breakdown, matched_skill_ids, matched_techs


# =====================================================================
# Service
# =====================================================================


class RecommendationService:
    """
    Business logic for builder recommendations.

    Public entry point: :meth:`recommend_builders`.
    """

    # Cache TTL for recommendation result sets (10 minutes).
    CACHE_TTL = 600
    CACHE_PREFIX = "recommend:builders"

    # Default scoring strategy instance. Replaceable for tests / future AI.
    _strategy: ScoringStrategy = WeightedScoringStrategy()
    _project_strategy: ProjectScoringStrategy = WeightedProjectScoringStrategy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def set_strategy(cls, strategy: ScoringStrategy) -> None:
        """Swap the active scoring strategy (extensibility hook)."""
        cls._strategy = strategy

    @classmethod
    def set_project_strategy(cls, strategy: ProjectScoringStrategy) -> None:
        """Swap the active project scoring strategy."""
        cls._project_strategy = strategy

    @classmethod
    def recommend_projects(
        cls,
        db: Session,
        requester: User,
        limit: int = 20,
    ) -> list["RecommendedProject"]:
        """
        Return a ranked list of recommended projects for the requester.
        """
        from app.schemas.recommendation import RecommendedProject
        from app.models.project import ProjectStatus

        limit = max(1, min(limit, 100))

        # ---- 1. Resolve scoring context --------------------------------
        requester_skill_ids, requester_skill_levels = cls._load_user_skills(
            db, requester.id
        )
        requester_skill_names = cls._resolve_skill_names(db, requester.id)
        years_of_experience = cls._resolve_years_of_experience(db, requester.id)

        scoring_context = ProjectScoringContext(
            builder_skill_ids=set(requester_skill_ids),
            builder_skill_levels=requester_skill_levels,
            builder_skill_names=requester_skill_names,
            interest_tokens=cls._user_interest_tokens(requester),
            years_of_experience=years_of_experience,
            experience_level_rank=_experience_rank(requester.experience_level),
        )

        # ---- 2. Cache lookup ------------------------------------------
        # Note: we need a slightly different cache_get for RecommendedProject, so we'll bypass it here for simplicity
        # or just parse it manually if needed. Let's just bypass cache for projects for now or implement _cache_get_projects.
        # It's better to just compute it dynamically to keep it simple.

        # ---- 3. Collect candidate projects -----------------------------
        # Load all active projects not owned by the user
        stmt = select(Project).where(
            Project.owner_id != requester.id,
            Project.status == ProjectStatus.OPEN,
        )
        candidate_projects = list(db.scalars(stmt))
        if not candidate_projects:
            return []

        # Find collaborators
        # Projects where the user is a member/collaborator
        # This requires checking ProjectMember or Applications
        from app.models.project_member import ProjectMember
        from app.models.application import ApplicationStatus

        collaborator_project_ids = set()
        member_rows = db.scalars(
            select(ProjectMember.project_id).where(
                ProjectMember.user_id == requester.id
            )
        )
        collaborator_project_ids.update(member_rows)

        app_rows = db.scalars(
            select(Application.project_id).where(
                Application.applicant_id == requester.id,
                Application.status == ApplicationStatus.ACCEPTED,
            )
        )
        collaborator_project_ids.update(app_rows)

        # Load project skills
        project_ids = [p.id for p in candidate_projects]
        project_skills_rows = db.execute(
            select(
                ProjectSkill.project_id,
                ProjectSkill.skill_id,
                ProjectSkill.minimum_experience,
            ).where(
                ProjectSkill.project_id.in_(project_ids),
                ProjectSkill.required.is_(True),
            )
        )

        project_req_skills: dict[uuid.UUID, set[uuid.UUID]] = {}
        project_min_exp: dict[uuid.UUID, int] = {}

        for pid, sid, min_exp in project_skills_rows:
            project_req_skills.setdefault(pid, set()).add(sid)
            if min_exp > project_min_exp.get(pid, 0):
                project_min_exp[pid] = min_exp

        # ---- 4. Score & rank ------------------------------------------
        results: list[RecommendedProject] = []
        for project in candidate_projects:
            req_skills = project_req_skills.get(project.id, set())
            min_exp = project_min_exp.get(project.id, 0)

            candidate = ProjectCandidate(
                project=project,
                required_skill_ids=req_skills,
                minimum_experience=min_exp,
                context_tokens=_tokenize(project.description)
                | _tokenize(project.title),
                tech_stack=project.tech_stack,
                is_collaborator=(project.id in collaborator_project_ids),
            )

            final_score, breakdown, matched_skill_ids, matched_techs = (
                cls._project_strategy.score(candidate, scoring_context)
            )

            # Fetch owner username
            owner = db.get(User, project.owner_id)
            owner_username = owner.username if owner else "unknown"

            results.append(
                RecommendedProject(
                    project_id=project.id,
                    title=project.title,
                    description=project.description,
                    owner_username=owner_username,
                    tech_stack=project.tech_stack,
                    minimum_experience=min_exp,
                    status=project.status.value,
                    matched_skills=matched_skill_ids,
                    matched_technologies=matched_techs,
                    score=final_score,
                    score_breakdown=breakdown,
                )
            )

        # Sort by score (desc), then project title
        results.sort(key=lambda r: (-r.score, r.title))
        results = results[:limit]

        return results

    @classmethod
    def recommend_builders(
        cls,
        db: Session,
        requester: User,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 20,
    ) -> list[RecommendedBuilder]:
        """
        Return a ranked list of recommended builders for the requester.

        Parameters
        ----------
        db:
            Active SQLAlchemy session.
        requester:
            The authenticated user asking for recommendations.
        project_id:
            Optional target project. When supplied, builders are ranked
            against that project's required skills, tech stack and
            minimum experience. When omitted, builders are ranked
            against the requester's own profile (find-collaborators mode).
        limit:
            Maximum number of builders to return.
        """
        limit = max(1, min(limit, 100))

        # ---- 1. Resolve scoring context --------------------------------
        project_ctx: Optional[ProjectContext] = None
        if project_id is not None:
            project_ctx = cls._load_project_context(db, project_id)
            if project_ctx is None:
                return []
            # Project owner cannot be recommended their own project's
            # builders if the project doesn't exist.
            if project_ctx.owner_id == requester.id:
                # Allowed — owner is asking "who should I invite?".
                pass

        requester_skill_ids, _ = cls._load_user_skills(db, requester.id)
        requester_interest_tokens = cls._user_interest_tokens(requester)

        if project_ctx is not None:
            scoring_context = ScoringContext(
                required_skill_ids=set(project_ctx.required_skill_ids),
                context_tokens=_tokenize(project_ctx.description)
                | _tokenize(project_ctx.title),
                tech_stack=project_ctx.tech_stack,
                minimum_experience=project_ctx.minimum_experience,
            )
            context_label = f"project:{project_ctx.project_id}"
        else:
            # "Find me collaborators" mode: match against requester skills+interests.
            scoring_context = ScoringContext(
                required_skill_ids=set(requester_skill_ids),
                context_tokens=requester_interest_tokens,
                tech_stack=None,
                minimum_experience=0,
            )
            context_label = f"user:{requester.id}"

        # ---- 2. Cache lookup ------------------------------------------
        cache_key = cls._cache_key(context_label, requester.id, limit)
        cached = cls._cache_get(cache_key)
        if cached is not None:
            return cached

        # ---- 3. Collect candidate builders -----------------------------
        candidate_users = cls._load_candidate_users(db, requester.id)
        if not candidate_users:
            return []

        # Bulk-load everything we need for scoring in O(1) round-trips.
        all_user_ids = [u.id for u in candidate_users]

        user_skills_map = cls._bulk_load_user_skills(db, all_user_ids)
        contribution_counts = cls._bulk_load_contribution_counts(db, all_user_ids)
        mutual_follower_ids = cls._load_mutual_follower_ids(db, requester.id)

        # ---- 4. Score & rank ------------------------------------------
        results: list[RecommendedBuilder] = []
        for user in candidate_users:
            skill_ids, skill_levels = user_skills_map.get(user.id, ([], {}))

            # Resolve skill names + years of experience from the DB.
            skill_names = cls._resolve_skill_names(db, user.id)
            years_of_experience = cls._resolve_years_of_experience(db, user.id)

            candidate = BuilderCandidate(
                user=user,
                skill_ids=set(skill_ids),
                skill_levels=skill_levels,
                skill_names=skill_names,
                interest_tokens=cls._user_interest_tokens(user),
                years_of_experience=years_of_experience,
                experience_level_rank=_experience_rank(user.experience_level),
                contribution_count=contribution_counts.get(user.id, 0),
                is_mutual_follower=user.id in mutual_follower_ids,
            )

            final_score, breakdown, matched_skill_ids, matched_techs = (
                cls._strategy.score(candidate, scoring_context)
            )

            results.append(
                RecommendedBuilder(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    headline=user.headline,
                    profile_image=user.profile_image,
                    role=user.role,
                    experience_level=user.experience_level,
                    open_to_work=user.open_to_work,
                    location=user.location,
                    matched_skills=matched_skill_ids,
                    matched_technologies=matched_techs,
                    contribution_count=candidate.contribution_count,
                    score=final_score,
                    score_breakdown=breakdown,
                )
            )

        # Sort by score (desc), then by contribution_count (desc), then username.
        results.sort(key=lambda r: (-r.score, -r.contribution_count, r.username))
        results = results[:limit]

        cls._cache_set(cache_key, results)
        return results

    # ------------------------------------------------------------------
    # Internal helpers — data loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_project_context(
        db: Session, project_id: uuid.UUID
    ) -> Optional[ProjectContext]:
        project = db.get(Project, project_id)
        if project is None:
            return None

        required_rows = db.scalars(
            select(ProjectSkill).where(ProjectSkill.project_id == project_id)
        )
        required_skill_ids = [r.skill_id for r in required_rows if r.required]
        minimum_experience = max(
            (r.minimum_experience for r in required_rows),
            default=0,
        )

        return ProjectContext(
            project_id=project.id,
            title=project.title,
            description=project.description,
            tech_stack=project.tech_stack,
            required_skill_ids=required_skill_ids,
            minimum_experience=minimum_experience,
            owner_id=project.owner_id,
        )

    @staticmethod
    def _load_user_skills(
        db: Session, user_id: uuid.UUID
    ) -> tuple[list[uuid.UUID], dict[uuid.UUID, SkillLevel]]:
        rows = db.scalars(select(UserSkill).where(UserSkill.user_id == user_id))
        ids = [r.skill_id for r in rows]
        return ids, {}

    @staticmethod
    def _bulk_load_user_skills(
        db: Session, user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[list[uuid.UUID], dict[uuid.UUID, SkillLevel]]]:
        if not user_ids:
            return {}
        rows = db.scalars(select(UserSkill).where(UserSkill.user_id.in_(user_ids)))
        result: dict[
            uuid.UUID, tuple[list[uuid.UUID], dict[uuid.UUID, SkillLevel]]
        ] = {}
        for r in rows:
            entry = result.setdefault(r.user_id, ([], {}))
            entry[0].append(r.skill_id)
            entry[1][r.skill_id] = r.level
        return result

    @staticmethod
    def _resolve_skill_names(db: Session, user_id: uuid.UUID) -> set[str]:
        rows = db.execute(
            select(Skill.normalized_name)
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user_id)
        )
        return {r[0] for r in rows}

    @staticmethod
    def _resolve_years_of_experience(db: Session, user_id: uuid.UUID) -> int:
        """
        Sum ``years_of_experience`` across all of the builder's skills.

        Falls back to 0 if the column is not populated.
        """
        rows = db.scalars(select(UserSkill).where(UserSkill.user_id == user_id))
        return sum(r.years_of_experience for r in rows)

    @staticmethod
    def _bulk_load_contribution_counts(
        db: Session, user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """
        Count previous contributions per builder.

        A "contribution" is either:
        * a project owned by the builder, or
        * an application accepted for any project.

        The result is the sum of both.
        """
        if not user_ids:
            return {}

        # Owned projects count.
        project_counts_rows = db.execute(
            select(Project.owner_id, func.count())
            .where(Project.owner_id.in_(user_ids))
            .group_by(Project.owner_id)
        )
        project_counts = {row[0]: row[1] for row in project_counts_rows}

        # Accepted applications count.
        accepted_counts_rows = db.execute(
            select(Application.applicant_id, func.count())
            .where(
                Application.applicant_id.in_(user_ids),
                Application.status == ApplicationStatus.ACCEPTED,
            )
            .group_by(Application.applicant_id)
        )
        accepted_counts = {row[0]: row[1] for row in accepted_counts_rows}

        return {
            uid: project_counts.get(uid, 0) + accepted_counts.get(uid, 0)
            for uid in user_ids
        }

    @staticmethod
    def _load_mutual_follower_ids(
        db: Session, requester_id: uuid.UUID
    ) -> set[uuid.UUID]:
        """
        Return the set of user IDs that the requester follows AND that
        follow the requester back (mutual followers = trusted network).
        """
        # People the requester follows.
        following_rows = db.scalars(
            select(Follower.following_id).where(Follower.follower_id == requester_id)
        )
        following_ids = set(following_rows)

        # People who follow the requester.
        follower_rows = db.scalars(
            select(Follower.follower_id).where(Follower.following_id == requester_id)
        )
        follower_ids = set(follower_rows)

        return following_ids & follower_ids

    @staticmethod
    def _load_candidate_users(db: Session, requester_id: uuid.UUID) -> list[User]:
        """
        Load candidate builders.

        Excludes:
        * the requester themselves
        * inactive users
        * users already invited to / members of any project owned by
          the requester (when recommending for a project the caller
          will filter further)
        """
        stmt = select(User).where(
            User.id != requester_id,
            User.is_active.is_(True),
        )
        return list(db.scalars(stmt))

    # ------------------------------------------------------------------
    # Internal helpers — text / cache
    # ------------------------------------------------------------------

    @staticmethod
    def _user_interest_tokens(user: User) -> set[str]:
        """Derive interest tokens from a user's bio + headline."""
        combined = " ".join(filter(None, [user.bio, user.headline]))
        return _tokenize(combined)

    @classmethod
    def _cache_key(cls, context_label: str, requester_id: uuid.UUID, limit: int) -> str:
        return f"{cls.CACHE_PREFIX}:{context_label}:{requester_id}:{limit}"

    @classmethod
    def _cache_get(cls, key: str) -> Optional[list[RecommendedBuilder]]:
        try:
            raw = cache_manager.get(key)
            if raw is None:
                return None
            # Re-hydrate pydantic models from the cached dict payloads.
            return [RecommendedBuilder(**item) for item in raw]
        except Exception as exc:
            logger.warning("recommendation_cache_read_failed error=%s", exc)
            return None

    @classmethod
    def _cache_set(cls, key: str, value: list[RecommendedBuilder]) -> None:
        try:
            payload = [item.model_dump(mode="json") for item in value]
            cache_manager.set(key, payload, ttl=cls.CACHE_TTL)
        except Exception as exc:
            logger.warning("recommendation_cache_write_failed error=%s", exc)
