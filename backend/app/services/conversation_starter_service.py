from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.user import User
from app.models.user_skill import UserSkill
from app.models.skill import Skill

logger = logging.getLogger(__name__)


class ConversationStarterService:
    """
    AI-powered conversation starter suggestions.
    
    Generates context-aware conversation prompts based on user profiles,
    skills, and shared interests.
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
    def _build_user_context(db: Session, user: User) -> dict:
        """Build context dictionary from user profile."""
        # Get user skills
        stmt = (
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user.id)
        )
        user_skills = db.scalars(stmt).all()
        skills = [
            {"name": us.skill.name, "level": us.level.value}
            for us in user_skills
            if us.skill
        ]

        return {
            "name": f"{user.first_name} {user.last_name}",
            "username": user.username,
            "headline": user.headline or "",
            "bio": user.bio or "",
            "role": user.role or "",
            "company": user.company or "",
            "location": user.location or "",
            "skills": skills,
            "open_to_work": user.open_to_work,
        }

    @staticmethod
    def _build_prompt(
        current_user_context: dict,
        target_user_context: dict,
    ) -> str:
        """Build the prompt for OpenAI to generate conversation starters."""
        skills_text = ""
        if target_user_context["skills"]:
            skills_list = [
                f"{s['name']} ({s['level']})" for s in target_user_context["skills"][:5]
            ]
            skills_text = f"Skills: {', '.join(skills_list)}"

        current_skills_text = ""
        if current_user_context["skills"]:
            skills_list = [
                f"{s['name']} ({s['level']})" for s in current_user_context["skills"][:5]
            ]
            current_skills_text = f"Your skills: {', '.join(skills_list)}"

        prompt = f"""Generate 3-5 natural, engaging conversation starters for a developer to message another developer on a collaboration platform.

Target person's profile:
- Name: {target_user_context['name']}
- Headline: {target_user_context['headline']}
- Bio: {target_user_context['bio'][:200]}
- Role: {target_user_context['role']}
- Company: {target_user_context['company']}
- Location: {target_user_context['location']}
- {skills_text}
- Open to work: {target_user_context['open_to_work']}

Your profile:
- Name: {current_user_context['name']}
- Headline: {current_user_context['headline']}
- {current_skills_text}

Requirements:
1. Generate exactly 3-5 conversation starters
2. Each should be context-aware, referencing their skills, role, or bio
3. Be natural and conversational, not robotic
4. Mix of approaches: compliment their work, ask about their expertise, suggest collaboration
5. Keep each suggestion under 100 characters
6. Make them feel personal, not generic

Return as JSON array of strings, nothing else. Example:
["I noticed your experience with FastAPI. Have you worked on any interesting projects recently?", "Your recent project looks interesting. Would you be open to collaborating?"]"""

        return prompt

    @staticmethod
    def generate_conversation_starters(
        db: Session,
        current_user_id: str,
        target_user_id: str,
    ) -> list[str]:
        """
        Generate conversation starters for messaging a potential collaborator.
        
        Args:
            db: Database session
            current_user_id: The user who will send the message
            target_user_id: The user they want to message
            
        Returns:
            List of 3-5 conversation starter suggestions
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, returning default starters")
            return ConversationStarterService._get_default_starters()

        # Fetch both users with their skills
        current_user = db.get(User, current_user_id)
        target_user = db.get(User, target_user_id)

        if not current_user or not target_user:
            return ConversationStarterService._get_default_starters()

        # Build contexts
        current_context = ConversationStarterService._build_user_context(db, current_user)
        target_context = ConversationStarterService._build_user_context(db, target_user)

        # Generate using OpenAI
        client = ConversationStarterService._get_client()
        if not client:
            return ConversationStarterService._get_default_starters()

        try:
            prompt = ConversationStarterService._build_prompt(current_context, target_context)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates natural conversation starters for developers. Return only a JSON array of strings, no markdown, no explanation.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.8,
                max_tokens=500,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            starters = json.loads(content)

            if isinstance(starters, list) and all(isinstance(s, str) for s in starters):
                return starters[:5]  # Max 5 suggestions

            return ConversationStarterService._get_default_starters()

        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON")
            return ConversationStarterService._get_default_starters()
        except Exception as e:
            logger.error(f"Failed to generate conversation starters: {e}")
            return ConversationStarterService._get_default_starters()

    @staticmethod
    def _get_default_starters() -> list[str]:
        """Return default conversation starters when AI is unavailable."""
        return [
            "Hi! I'd love to connect and learn more about your work.",
            "I noticed we're both working on interesting projects. Would you like to collaborate?",
            "Your profile caught my eye. What are you currently building?",
        ]
