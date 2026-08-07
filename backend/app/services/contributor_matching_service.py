from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.project import Project
from app.models.user import User
from app.models.user_skill import UserSkill
from app.models.skill import Skill

logger = logging.getLogger(__name__)


@dataclass
class ContributorProfile:
    user_id: str
    username: str
    full_name: str
    avatar: str | None
    headline: str | None
    bio: str | None
    role: str | None
    skills: list[dict]
    open_to_work: bool
    last_active: str | None
    github_url: str | None


@dataclass
class MatchResult:
    user_id: str
    match_score: float
    match_reason: str
    matching_skills: list[str]


@dataclass
class SkillGapResult:
    project_id: str
    user_id: str
    match_percentage: float
    matching_skills: list[str]
    missing_skills: list[str]
    recommended_learning_topics: list[str]


class ContributorMatchingService:
    """
    AI-powered contributor matching for projects and skill gap analysis.

    Analyzes project requirements and user profiles to recommend
    the best contributors based on skills, activity, and availability,
    and performs skill gap analysis.
    """

    @staticmethod
    def _get_client():
        """Get OpenAI client."""
        try:
            from openai import OpenAI # type: ignore

            return OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError:
            logger.warning("openai package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            return None

    @staticmethod
    def _build_project_context(project: Project, project_skills: list[str]) -> str:
        """Build project context for the AI prompt."""
        skills_text = ", ".join(project_skills) if project_skills else "Not specified"
        tech_text = project.tech_stack or "Not specified"

        return f"""Project: {project.title}
Description: {(project.description or '')[:500]}
Stage: {project.stage.value}
Tech Stack: {tech_text}
Required Skills: {skills_text}
Team Size: {project.team_size}/{project.max_team_size}
Hiring: {project.hiring}"""

    @staticmethod
    def _build_contributor_context(contributors: list[ContributorProfile]) -> str:
        """Build contributor profiles for the AI prompt."""
        profiles = []
        for c in contributors:
            skills_list = [f"{s['name']}({s['level']})" for s in c.skills[:5]]
            profiles.append(
                f"- {c.full_name} (@{c.username}): {c.headline or 'N/A'}. "
                f"Skills: {', '.join(skills_list) if skills_list else 'None'}. "
                f"Role: {c.role or 'N/A'}. "
                f"Open to work: {c.open_to_work}. "
                f"Last active: {c.last_active or 'Unknown'}. "
                f"GitHub: {c.github_url or 'Not provided'}"
            )
        return "\n".join(profiles)

    @staticmethod
    def _get_project_skills(db: Session, project_id) -> list[str]:
        """Get skills associated with a project via project_skills table."""
        from app.models.project_skill import ProjectSkill

        stmt = (
            select(ProjectSkill)
            .options(selectinload(ProjectSkill.skill))
            .where(ProjectSkill.project_id == project_id)
        )
        project_skills = db.scalars(stmt).all()
        return [ps.skill.name for ps in project_skills if ps.skill]

    @staticmethod
    def _get_candidate_profiles(
        db: Session, project_id, limit: int
    ) -> list[ContributorProfile]:
        """Get candidate user profiles for matching."""
        project = db.get(Project, project_id)
        if not project:
            return []

        from app.models.project_member import ProjectMember

        member_stmt = select(ProjectMember.user_id).where(
            ProjectMember.project_id == project_id
        )
        existing_members = set(db.scalars(member_stmt).all())

        stmt = (
            select(User)
            .where(User.open_to_work == True)
            .where(User.is_active == True)
            .where(User.id != project.owner_id)
            .limit(20)
        )
        candidates = db.scalars(stmt).all()

        profiles = []
        for user in candidates:
            if user.id in existing_members:
                continue

            skill_stmt = (
                select(UserSkill)
                .options(selectinload(UserSkill.skill))
                .where(UserSkill.user_id == user.id)
            )
            user_skills = db.scalars(skill_stmt).all()
            skills = [
                {"name": us.skill.name, "level": us.level.value}
                for us in user_skills
                if us.skill
            ]

            profiles.append(
                ContributorProfile(
                    user_id=str(user.id),
                    username=user.username,
                    full_name=f"{user.first_name} {user.last_name}",
                    avatar=user.profile_image,
                    headline=user.headline,
                    bio=user.bio,
                    role=user.role,
                    skills=skills,
                    open_to_work=user.open_to_work,
                    last_active=(
                        user.last_active_at.isoformat() if user.last_active_at else None
                    ),
                    github_url=user.github_url,
                )
            )

        return profiles[:limit]

    @staticmethod
    def _build_prompt(
        project_context: str, contributor_context: str, limit: int
    ) -> str:
        """Build the prompt for AI matching."""
        return f"""Analyze the following project and contributor profiles to find the best matches.

{project_context}

Candidate Contributors:
{contributor_context}

Rank the top {limit} contributors based on:
1. Skill match (40% weight): How well their skills align with project needs
2. Experience level (20% weight): Appropriate level for the project stage
3. Availability (20% weight): Currently open to work and active
4. GitHub activity (10% weight): Active GitHub presence
5. Role fit (10% weight): Relevant professional background

For each match, provide:
- user_id: The contributor's UUID
- match_score: 0.0-1.0 score
- match_reason: Brief explanation of why they're a good match (max 100 chars)
- matching_skills: List of their skills that match project needs (max 5)

Return a JSON array of objects with these fields. Return only the JSON array, no markdown.
Example: [{{"user_id": "uuid", "match_score": 0.85, "match_reason": "Strong Python skills match project needs", "matching_skills": ["Python", "FastAPI"]}}]"""

    @staticmethod
    def match_contributors(
        db: Session,
        project_id,
        limit: int = 5,
    ) -> list[MatchResult]:
        """
        Find matching contributors for a project using AI.
        """
        project = db.get(Project, project_id)
        if not project:
            logger.warning(f"Project {project_id} not found")
            return []

        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, returning empty matches")
            return []

        client = ContributorMatchingService._get_client()
        if not client:
            return []

        try:
            project_skills = ContributorMatchingService._get_project_skills(
                db, project_id
            )
            project_context = ContributorMatchingService._build_project_context(
                project, project_skills
            )

            candidates = ContributorMatchingService._get_candidate_profiles(
                db, project_id, limit=min(limit * 3, 20)
            )
            if not candidates:
                logger.info("No candidate contributors found")
                return []

            contributor_context = ContributorMatchingService._build_contributor_context(
                candidates
            )

            prompt = ContributorMatchingService._build_prompt(
                project_context, contributor_context, limit
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical recruiter who matches contributors to open source projects. Return only a valid JSON array.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            content = response.choices[0].message.content.strip()

            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            matches_data = json.loads(content)

            if not isinstance(matches_data, list):
                return []

            results = []
            candidate_map = {c.user_id: c for c in candidates}

            for match in matches_data[:limit]:
                user_id = match.get("user_id", "")
                if user_id not in candidate_map:
                    continue

                score = max(0.0, min(1.0, float(match.get("match_score", 0.5))))
                reason = match.get("match_reason", "Good match")
                skills = match.get("matching_skills", [])

                results.append(
                    MatchResult(
                        user_id=user_id,
                        match_score=score,
                        match_reason=reason,
                        matching_skills=skills[:5],
                    )
                )

            return results

        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON")
            return []
        except Exception as e:
            logger.error(f"Failed to match contributors: {e}")
            return []

    @staticmethod
    def analyze_skill_gap(
        db: Session,
        project_id,
        user_id,
    ) -> SkillGapResult:
        """
        Compare a user's skills against project requirements and identify missing skills,
        match percentage, and recommended learning topics.
        """
        default_result = SkillGapResult(
            project_id=str(project_id),
            user_id=str(user_id),
            match_percentage=0.0,
            matching_skills=[],
            missing_skills=[],
            recommended_learning_topics=[],
        )

        project = db.get(Project, project_id)
        user = db.get(User, user_id)
        if not project or not user:
            return default_result

        project_skills = ContributorMatchingService._get_project_skills(db, project_id)
        
        # Get user skills
        skill_stmt = (
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills_records = db.scalars(skill_stmt).all()
        user_skills = [us.skill.name for us in user_skills_records if us.skill]

        if not settings.OPENAI_API_KEY:
            # Fallback algorithmic comparison if OpenAI API key is missing
            p_set = {s.lower() for s in project_skills}
            u_set = {s.lower() for s in user_skills}
            matching = [s for s in project_skills if s.lower() in u_set]
            missing = [s for s in project_skills if s.lower() not in u_set]
            match_pct = (len(matching) / len(project_skills) * 100.0) if project_skills else 100.0
            return SkillGapResult(
                project_id=str(project_id),
                user_id=str(user_id),
                match_percentage=round(match_pct, 1),
                matching_skills=matching,
                missing_skills=missing,
                recommended_learning_topics=missing,
            )

        client = ContributorMatchingService._get_client()
        if not client:
            return default_result

        try:
            prompt = f"""Analyze the skill gap between a user and a project.

Project Requirements:
Title: {project.title}
Tech Stack: {project.tech_stack or 'N/A'}
Required Skills: {', '.join(project_skills) if project_skills else 'None specified'}

User Skills:
{', '.join(user_skills) if user_skills else 'None specified'}

Provide an analysis in JSON format with the following keys:
- match_percentage: float between 0.0 and 100.0 representing skill match percentage
- matching_skills: array of strings of project required skills the user possesses
- missing_skills: array of strings of project required skills the user lacks
- recommended_learning_topics: array of strings for learning topics to bridge the gap

Return only valid JSON, no markdown."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical mentor and career coach performing skill gap analysis. Return only valid JSON.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=600,
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            data = json.loads(content)
            return SkillGapResult(
                project_id=str(project_id),
                user_id=str(user_id),
                match_percentage=float(data.get("match_percentage", 0.0)),
                matching_skills=data.get("matching_skills", []),
                missing_skills=data.get("missing_skills", []),
                recommended_learning_topics=data.get("recommended_learning_topics", []),
            )
        except Exception as e:
            logger.error(f"Failed to perform skill gap analysis: {e}")
            return default_result
        