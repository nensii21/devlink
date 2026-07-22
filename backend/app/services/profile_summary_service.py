from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.user import User
from app.models.user_skill import UserSkill

logger = logging.getLogger(__name__)

MAX_SUMMARY_LENGTH = 500


class ProfileSummaryService:
    """
    AI-powered developer profile summary generator.

    Generates professional summaries based on user profile data,
    skills, and activity.
    """

    @staticmethod
    def _get_client():
        """Get OpenAI client."""
        try:
            from openai import OpenAI
            return OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError:
            logger.warning("openai package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            return None

    @staticmethod
    def _get_user_skills(db: Session, user_id: str) -> list[dict]:
        """Get user's skills with levels."""
        stmt = (
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills = db.scalars(stmt).all()
        return [
            {
                "name": us.skill.name,
                "level": us.level.value,
                "years": us.years_of_experience,
            }
            for us in user_skills
            if us.skill
        ]

    @staticmethod
    def _build_prompt(user: User, skills: list[dict], stats: dict) -> str:
        """Build the prompt for OpenAI to generate a profile summary."""
        skills_text = ""
        if skills:
            skills_list = [
                f"{s['name']} ({s['level']}, {s['years']} years)" for s in skills[:10]
            ]
            skills_text = f"Skills: {', '.join(skills_list)}"

        stats_text = ""
        if stats:
            parts = []
            if stats.get("projects"):
                parts.append(f"{stats['projects']} projects")
            if stats.get("followers"):
                parts.append(f"{stats['followers']} followers")
            if stats.get("accepted"):
                parts.append(f"{stats['accepted']} accepted applications")
            stats_text = f"Activity: {', '.join(parts)}" if parts else ""

        prompt = f"""Generate a professional developer profile summary based on the following information.

Name: {user.first_name} {user.last_name}
Headline: {user.headline or 'Not specified'}
Bio: {user.bio or 'Not specified'}
Role: {user.role or 'Not specified'}
Company: {user.company or 'Not specified'}
Experience Level: {user.experience_level or 'Not specified'}
Location: {user.location or 'Not specified'}
Open to Work: {user.open_to_work}
{skills_text}
{stats_text}

Requirements:
1. Write a concise, professional summary (2-4 sentences, max {MAX_SUMMARY_LENGTH} characters)
2. Highlight key strengths based on skills and experience
3. Mention their role and what they likely specialize in
4. If they have notable activity, mention it briefly
5. Make it engaging and suitable for a developer portfolio
6. Use first-person style (e.g., "Full-stack developer specializing in...")
7. Do NOT include the person's name in the summary

Return ONLY the summary text, nothing else."""

        return prompt

    @staticmethod
    def generate_summary(
        db: Session,
        user: User,
        stats: dict | None = None,
    ) -> str:
        """
        Generate a professional summary for a developer profile.

        Args:
            db: Database session
            user: User to generate summary for
            stats: Optional user stats dict

        Returns:
            Generated professional summary
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, returning default summary")
            return ProfileSummaryService._get_default_summary(user)

        # Fetch user skills
        skills = ProfileSummaryService._get_user_skills(db, str(user.id))

        # Generate using OpenAI
        client = ProfileSummaryService._get_client()
        if not client:
            return ProfileSummaryService._get_default_summary(user)

        try:
            prompt = ProfileSummaryService._build_prompt(user, skills, stats or {})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional developer profile writer. Generate concise, engaging summaries for developer profiles. Return ONLY the summary text.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
                max_tokens=300,
            )

            summary = response.choices[0].message.content.strip()

            # Enforce character limit
            if len(summary) > MAX_SUMMARY_LENGTH:
                summary = summary[:MAX_SUMMARY_LENGTH - 3] + "..."

            return summary

        except Exception as e:
            logger.error(f"Failed to generate profile summary: {e}")
            return ProfileSummaryService._get_default_summary(user)

    @staticmethod
    def _get_default_summary(user: User) -> str:
        """Return a default summary when AI is unavailable."""
        parts = []
        if user.role:
            parts.append(user.role)
        if user.company:
            parts.append(f"at {user.company}")
        if user.experience_level:
            parts.append(f"({user.experience_level} level)")

        if parts:
            return f"{' '.join(parts)}. Passionate about building great software and collaborating with other developers."
        return "Passionate developer building great software and collaborating with other developers."
