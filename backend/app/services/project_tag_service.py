from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_TAGS = 10


class ProjectTagService:
    """
    AI-powered project tag generator.

    Generates relevant tags based on project description and tech stack.
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
    def _build_prompt(title: str, description: str, tech_stack: str | None) -> str:
        """Build the prompt for OpenAI to generate tags."""
        tech_text = f"\nTech Stack: {tech_stack}" if tech_stack else ""

        prompt = f"""Generate relevant tags for a developer project based on the following information.

Project Title: {title}
Project Description: {description[:500]}
{tech_text}

Requirements:
1. Generate 5-10 relevant tags
2. Include technology tags (e.g., React, Python, FastAPI)
3. Include category tags (e.g., AI, Web, Mobile, Backend)
4. Include feature tags if relevant (e.g., Resume, NLP, Authentication)
5. Keep tags concise (1-3 words each)
6. Use PascalCase for multi-word tags (e.g., "Machine Learning")
7. Prioritize specific technologies over generic terms

Return as JSON array of objects with "name" and "confidence" fields.
Confidence should be a number between 0 and 1.
Example:
[{{"name": "FastAPI", "confidence": 0.95}}, {{"name": "React", "confidence": 0.9}}, {{"name": "AI", "confidence": 0.85}}]"""

        return prompt

    @staticmethod
    def generate_tags(
        title: str,
        description: str,
        tech_stack: str | None = None,
    ) -> list[dict]:
        """
        Generate tags for a project.

        Args:
            title: Project title
            description: Project description
            tech_stack: Optional tech stack string

        Returns:
            List of tag dicts with name and confidence
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, returning default tags")
            return ProjectTagService._get_default_tags(title, description)

        client = ProjectTagService._get_client()
        if not client:
            return ProjectTagService._get_default_tags(title, description)

        try:
            prompt = ProjectTagService._build_prompt(title, description, tech_stack)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates relevant tags for developer projects. Return only a JSON array of objects with 'name' and 'confidence' fields.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
                max_tokens=500,
            )

            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            tags = json.loads(content)

            if isinstance(tags, list):
                # Validate and clean tags
                cleaned_tags = []
                for tag in tags[:MAX_TAGS]:
                    if isinstance(tag, dict) and "name" in tag:
                        cleaned_tags.append({
                            "name": tag["name"],
                            "confidence": min(1.0, max(0.0, tag.get("confidence", 0.8))),
                        })
                if cleaned_tags:
                    return cleaned_tags

            return ProjectTagService._get_default_tags(title, description)

        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON")
            return ProjectTagService._get_default_tags(title, description)
        except Exception as e:
            logger.error(f"Failed to generate project tags: {e}")
            return ProjectTagService._get_default_tags(title, description)

    @staticmethod
    def _get_default_tags(title: str, description: str) -> list[dict]:
        """Return default tags when AI is unavailable."""
        # Simple keyword-based tag generation
        text = f"{title} {description}".lower()
        default_tags = []

        # Technology keywords
        tech_keywords = {
            "python": "Python",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "react": "React",
            "vue": "Vue",
            "angular": "Angular",
            "node": "Node.js",
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
            "postgresql": "PostgreSQL",
            "mongodb": "MongoDB",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "aws": "AWS",
            "ai": "AI",
            "machine learning": "Machine Learning",
            "nlp": "NLP",
            "deep learning": "Deep Learning",
        }

        for keyword, tag in tech_keywords.items():
            if keyword in text:
                default_tags.append({"name": tag, "confidence": 0.7})

        # Add generic tags if few found
        if len(default_tags) < 3:
            default_tags.extend([
                {"name": "Web", "confidence": 0.5},
                {"name": "Full Stack", "confidence": 0.4},
            ])

        return default_tags[:MAX_TAGS]
