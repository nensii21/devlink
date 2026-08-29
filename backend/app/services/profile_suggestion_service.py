from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.profile_suggestion import ProfileSuggestionDismissal
from app.models.project import Project
from app.models.user import User
from app.models.user_skill import UserSkill
from app.schemas.profile_suggestion import (
    DismissSuggestionResponse,
    ProfileSuggestionItem,
    ProfileSuggestionsResponse,
    RefreshSuggestionsResponse,
)

logger = logging.getLogger(__name__)


class ProfileSuggestionService:
    """
    AI-powered developer profile improvement suggestion engine (#619).

    Analyzes developer profiles to produce suggestions in 5 core categories:
    - missing_skills
    - weak_bio
    - portfolio_improvements
    - github_connection
    - experience_gaps
    """

    CATEGORIES = {
        "missing_skills",
        "weak_bio",
        "portfolio_improvements",
        "github_connection",
        "experience_gaps",
    }

    # ------------------------------------------------------------------
    # Profile Score Calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_profile_score(
        user: User, skills: list[dict], project_count: int
    ) -> int:
        """
        Calculate a profile completeness score from 0 to 100.
        """
        score = 0

        # Basic identity (20 pts)
        if user.first_name and user.last_name:
            score += 10
        if getattr(user, "is_verified", False):
            score += 10

        # Bio & Headline (25 pts)
        if user.headline:
            score += 10
        if user.bio:
            bio_len = len(user.bio.strip())
            if bio_len >= 100:
                score += 15
            elif bio_len >= 30:
                score += 8

        # Skills (20 pts)
        skill_cnt = len(skills)
        if skill_cnt >= 5:
            score += 20
        elif skill_cnt >= 3:
            score += 15
        elif skill_cnt >= 1:
            score += 8

        # Portfolio & GitHub (20 pts)
        if user.github_url:
            score += 10
        if user.portfolio_url or user.website:
            score += 10

        # Experience & Availability (15 pts)
        if user.experience_level:
            score += 5
        if user.role or user.company:
            score += 5
        if user.open_to_work:
            score += 5

        return min(100, score)

    # ------------------------------------------------------------------
    # Candidate Generation (Rule-based Base / Fallback)
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_rule_based_suggestions(
        user: User, skills: list[dict], project_count: int
    ) -> list[ProfileSuggestionItem]:
        """
        Generate candidate profile suggestions across all 5 categories using rules.
        """
        suggestions: list[ProfileSuggestionItem] = []

        # 1. Missing Skills
        if not skills:
            suggestions.append(
                ProfileSuggestionItem(
                    id="missing_skills_none",
                    category="missing_skills",
                    title="No Skills Listed",
                    description=(
                        "Your profile currently has no skills listed. Adding key technical skills "
                        "(e.g., Python, React, PostgreSQL) significantly improves project recommendations "
                        "and collaborator discovery."
                    ),
                    impact="high",
                    action_label="Add Skills",
                    action_url="/settings/skills",
                )
            )
        elif len(skills) < 3:
            suggestions.append(
                ProfileSuggestionItem(
                    id="missing_skills_few",
                    category="missing_skills",
                    title="Expand Technical Skillset",
                    description=(
                        f"You have only {len(skills)} skill listed. Adding at least 3 to 5 relevant skills "
                        "helps potential project collaborators assess your technical stack match."
                    ),
                    impact="medium",
                    action_label="Add More Skills",
                    action_url="/settings/skills",
                )
            )

        # Complementary skills suggestion based on role
        user_role = (user.role or "").lower()
        existing_skills_lower = {s["name"].lower() for s in skills}
        if "frontend" in user_role and not (
            "typescript" in existing_skills_lower or "react" in existing_skills_lower
        ):
            suggestions.append(
                ProfileSuggestionItem(
                    id="missing_skills_frontend_core",
                    category="missing_skills",
                    title="Add Core Frontend Technologies",
                    description=(
                        "As a Frontend Developer, adding key frameworks like React or TypeScript "
                        "will make your profile stand out to team leads searching for UI engineers."
                    ),
                    impact="medium",
                    action_label="Update Skills",
                    action_url="/settings/skills",
                )
            )
        elif "backend" in user_role and not (
            "python" in existing_skills_lower
            or "postgresql" in existing_skills_lower
            or "fastapi" in existing_skills_lower
            or "node" in existing_skills_lower
        ):
            suggestions.append(
                ProfileSuggestionItem(
                    id="missing_skills_backend_core",
                    category="missing_skills",
                    title="Add Core Backend Technologies",
                    description=(
                        "Consider adding backend staples such as Python, FastAPI, Node.js, or PostgreSQL "
                        "to highlight your server-side architecture proficiency."
                    ),
                    impact="medium",
                    action_label="Update Skills",
                    action_url="/settings/skills",
                )
            )

        # 2. Weak Bio
        if not user.bio:
            suggestions.append(
                ProfileSuggestionItem(
                    id="weak_bio_empty",
                    category="weak_bio",
                    title="Add a Profile Bio",
                    description=(
                        "Your bio is empty. A concise, engaging 2-3 sentence overview of your background, "
                        "tech stack, and current goals helps developers get to know you quickly."
                    ),
                    impact="high",
                    action_label="Write Bio",
                    action_url="/settings/profile",
                )
            )
        elif len(user.bio.strip()) < 40:
            suggestions.append(
                ProfileSuggestionItem(
                    id="weak_bio_short",
                    category="weak_bio",
                    title="Expand Brief Bio",
                    description=(
                        "Your bio is quite short. Expanding it with details about your engineering background, "
                        "favorite tools, and collaboration preferences increases developer engagement."
                    ),
                    impact="medium",
                    action_label="Enhance Bio",
                    action_url="/settings/profile",
                )
            )

        if not user.headline:
            suggestions.append(
                ProfileSuggestionItem(
                    id="weak_bio_no_headline",
                    category="weak_bio",
                    title="Add a Professional Headline",
                    description=(
                        "A clear headline (e.g. 'Full-Stack Developer | Open Source Enthusiast') "
                        "gives a quick first impression on community leaderboards and search results."
                    ),
                    impact="medium",
                    action_label="Set Headline",
                    action_url="/settings/profile",
                )
            )

        # 3. Portfolio Improvements
        if not user.portfolio_url and not user.website:
            suggestions.append(
                ProfileSuggestionItem(
                    id="portfolio_no_link",
                    category="portfolio_improvements",
                    title="Link Portfolio or Website",
                    description=(
                        "No portfolio or personal website link found. Linking your personal website "
                        "or live demos builds credibility when applying to open builder flares."
                    ),
                    impact="high",
                    action_label="Add Portfolio Link",
                    action_url="/settings/profile",
                )
            )

        if project_count == 0:
            suggestions.append(
                ProfileSuggestionItem(
                    id="portfolio_no_projects",
                    category="portfolio_improvements",
                    title="Showcase Your First Project",
                    description=(
                        "You haven't created or linked any projects on DevLink yet. "
                        "Creating a project showcase demonstrates your hands-on building capabilities."
                    ),
                    impact="high",
                    action_label="Create Project",
                    action_url="/projects/new",
                )
            )

        # 4. GitHub Connection
        if not user.github_url:
            suggestions.append(
                ProfileSuggestionItem(
                    id="github_not_connected",
                    category="github_connection",
                    title="Connect GitHub Profile",
                    description=(
                        "Connecting your GitHub profile allows collaborators to view your repositories, "
                        "contribution activity, and commit history directly on DevLink."
                    ),
                    impact="high",
                    action_label="Connect GitHub",
                    action_url="/settings/account",
                )
            )

        # 5. Experience Gaps
        if not user.experience_level:
            suggestions.append(
                ProfileSuggestionItem(
                    id="experience_no_level",
                    category="experience_gaps",
                    title="Set Experience Level",
                    description=(
                        "Specify your experience level (e.g., Junior, Mid, Senior, Lead). "
                        "Project owners use this filter when assembling balanced team roles."
                    ),
                    impact="medium",
                    action_label="Select Level",
                    action_url="/settings/profile",
                )
            )

        if not user.company and not user.role:
            suggestions.append(
                ProfileSuggestionItem(
                    id="experience_no_role_company",
                    category="experience_gaps",
                    title="Add Current Role or Organization",
                    description=(
                        "Adding your current title or organization provides valuable professional context "
                        "to prospective project partners."
                    ),
                    impact="medium",
                    action_label="Update Profile",
                    action_url="/settings/profile",
                )
            )

        if user.open_to_work is None:
            suggestions.append(
                ProfileSuggestionItem(
                    id="experience_no_availability",
                    category="experience_gaps",
                    title="Set Availability Status",
                    description=(
                        "Indicate whether you are open to collaborating on new projects "
                        "so project recruiters know if you're available."
                    ),
                    impact="low",
                    action_label="Set Status",
                    action_url="/settings/profile",
                )
            )

        return suggestions

    # ------------------------------------------------------------------
    # AI Enrichment (OpenAI integration)
    # ------------------------------------------------------------------

    @staticmethod
    def _enrich_with_ai(
        user: User,
        skills: list[dict],
        project_count: int,
        base_suggestions: list[ProfileSuggestionItem],
    ) -> list[ProfileSuggestionItem]:
        """
        Use OpenAI (gpt-4o-mini) to refine and customize profile suggestions.
        Falls back to base_suggestions if OpenAI API is unavailable or errors out.
        """
        if not settings.OPENAI_API_KEY:
            logger.info("OPENAI_API_KEY not set; using rule-based profile suggestions.")
            return base_suggestions

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            prompt = f"""You are an expert technical career advisor for software engineers on a developer networking platform.
Analyze this developer's profile and recommend improvements to increase their visibility and collaboration opportunities.

Developer Profile:
- Name: {user.first_name} {user.last_name}
- Headline: {user.headline or "None"}
- Bio: {user.bio or "None"}
- Role: {user.role or "None"}
- Experience Level: {user.experience_level or "None"}
- Company: {user.company or "None"}
- Skills: {json.dumps(skills)}
- Portfolio URL: {user.portfolio_url or user.website or "None"}
- GitHub URL: {user.github_url or "None"}
- Open to Work: {user.open_to_work}
- Projects Created: {project_count}

Identify up to 5 prioritized suggestions across these 5 categories:
1. missing_skills
2. weak_bio
3. portfolio_improvements
4. github_connection
5. experience_gaps

Format requirements:
Return ONLY valid JSON matching this exact schema:
{{
  "suggestions": [
    {{
      "id": "category_identifier",
      "category": "missing_skills | weak_bio | portfolio_improvements | github_connection | experience_gaps",
      "title": "Short title",
      "description": "Clear 2-sentence actionable recommendation",
      "impact": "high | medium | low",
      "action_label": "Short action label",
      "action_url": "/settings/profile or appropriate path"
    }}
  ]
}}
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You analyze developer profiles and output JSON recommendations. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=600,
            )

            content = response.choices[0].message.content or ""
            data = json.loads(content)

            ai_items: list[ProfileSuggestionItem] = []
            for item in data.get("suggestions", []):
                if not isinstance(item, dict) or not item.get("category"):
                    continue
                cat = item.get("category", "experience_gaps")
                if cat not in ProfileSuggestionService.CATEGORIES:
                    cat = "experience_gaps"
                ai_items.append(
                    ProfileSuggestionItem(
                        id=item.get("id", f"{cat}_{len(ai_items)}"),
                        category=cat,
                        title=item.get("title", "Improve Profile"),
                        description=item.get(
                            "description", "Update your profile details."
                        ),
                        impact=item.get("impact", "medium").lower(),
                        action_label=item.get("action_label", "Update Profile"),
                        action_url=item.get("action_url", "/settings/profile"),
                    )
                )

            if ai_items:
                return ai_items

        except Exception as e:
            logger.error(f"OpenAI error in ProfileSuggestionService: {e}")

        return base_suggestions

    # ------------------------------------------------------------------
    # Service Methods
    # ------------------------------------------------------------------

    @staticmethod
    def get_profile_suggestions(
        db: Session,
        user: User,
        include_dismissed: bool = False,
    ) -> ProfileSuggestionsResponse:
        """
        Fetch AI profile improvement suggestions for the specified user.
        """
        # Fetch user skills
        stmt_skills = (
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user.id)
        )
        user_skills_rows = db.scalars(stmt_skills).all()
        skills = [
            {
                "name": us.skill.name,
                "level": (
                    us.level.value if hasattr(us.level, "value") else str(us.level)
                ),
                "years": us.years_of_experience,
            }
            for us in user_skills_rows
            if us.skill
        ]

        # Fetch project count
        stmt_projects = select(Project).where(Project.owner_id == user.id)
        project_count = len(db.scalars(stmt_projects).all())

        # Calculate profile score
        score = ProfileSuggestionService.calculate_profile_score(
            user, skills, project_count
        )

        # Generate base rule suggestions
        base_suggestions = ProfileSuggestionService._generate_rule_based_suggestions(
            user, skills, project_count
        )

        # Attempt AI enrichment if API key is present
        raw_suggestions = ProfileSuggestionService._enrich_with_ai(
            user, skills, project_count, base_suggestions
        )

        # Get dismissed suggestion IDs for user from DB
        stmt_dismissals = select(ProfileSuggestionDismissal.suggestion_id).where(
            ProfileSuggestionDismissal.user_id == user.id
        )
        dismissed_ids = set(db.scalars(stmt_dismissals).all())

        # Process dismissal state
        processed_suggestions: list[ProfileSuggestionItem] = []
        dismissed_count = 0

        for item in raw_suggestions:
            if item.id in dismissed_ids:
                dismissed_count += 1
                item.is_dismissed = True
                if include_dismissed:
                    processed_suggestions.append(item)
            else:
                item.is_dismissed = False
                processed_suggestions.append(item)

        active_count = len([s for s in processed_suggestions if not s.is_dismissed])

        return ProfileSuggestionsResponse(
            user_id=user.id,
            profile_score=score,
            total_suggestions=len(raw_suggestions),
            active_suggestions_count=active_count,
            dismissed_suggestions_count=dismissed_count,
            suggestions=processed_suggestions,
            generated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def dismiss_suggestion(
        db: Session,
        user_id: uuid.UUID,
        suggestion_id: str,
        category: str = "general",
    ) -> DismissSuggestionResponse:
        """
        Dismiss a specific profile improvement suggestion.
        """
        # Check if already dismissed
        existing = db.scalar(
            select(ProfileSuggestionDismissal).where(
                ProfileSuggestionDismissal.user_id == user_id,
                ProfileSuggestionDismissal.suggestion_id == suggestion_id,
            )
        )
        if not existing:
            dismissal = ProfileSuggestionDismissal(
                user_id=user_id,
                suggestion_id=suggestion_id,
                category=category,
            )
            db.add(dismissal)
            db.commit()

        return DismissSuggestionResponse(
            success=True,
            message=f"Suggestion '{suggestion_id}' has been dismissed.",
            suggestion_id=suggestion_id,
            user_id=user_id,
        )

    @staticmethod
    def dismiss_all_suggestions(
        db: Session,
        user: User,
    ) -> dict[str, Any]:
        """
        Dismiss all current profile suggestions for a user.
        """
        current_res = ProfileSuggestionService.get_profile_suggestions(
            db, user, include_dismissed=False
        )

        dismissed_now = 0
        for item in current_res.suggestions:
            if not item.is_dismissed:
                existing = db.scalar(
                    select(ProfileSuggestionDismissal).where(
                        ProfileSuggestionDismissal.user_id == user.id,
                        ProfileSuggestionDismissal.suggestion_id == item.id,
                    )
                )
                if not existing:
                    db.add(
                        ProfileSuggestionDismissal(
                            user_id=user.id,
                            suggestion_id=item.id,
                            category=item.category,
                        )
                    )
                    dismissed_now += 1

        db.commit()
        return {
            "success": True,
            "message": f"Dismissed {dismissed_now} active suggestions.",
            "dismissed_count": dismissed_now,
            "user_id": str(user.id),
        }

    @staticmethod
    def refresh_suggestions(
        db: Session,
        user: User,
        reset_dismissed: bool = False,
    ) -> RefreshSuggestionsResponse:
        """
        Re-evaluates recommendations. If reset_dismissed is True, resets previously dismissed suggestions.
        """
        reset_count = 0
        if reset_dismissed:
            stmt = delete(ProfileSuggestionDismissal).where(
                ProfileSuggestionDismissal.user_id == user.id
            )
            res = db.execute(stmt)
            reset_count = res.rowcount or 0
            db.commit()

        return RefreshSuggestionsResponse(
            success=True,
            message="Profile suggestions re-evaluated and refreshed successfully.",
            user_id=user.id,
            reset_dismissed_count=reset_count,
        )
