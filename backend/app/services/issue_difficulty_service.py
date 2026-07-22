from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.core.config import settings
from app.models.issue import IssueDifficulty

logger = logging.getLogger(__name__)


@dataclass
class DifficultyResult:
    difficulty: IssueDifficulty
    confidence: float
    reasoning: str


class IssueDifficultyService:
    """
    AI-powered issue difficulty estimation.

    Analyzes issue title and description to classify difficulty
    as Beginner, Intermediate, Advanced, or Expert.
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
    def _build_prompt(title: str, description: str, labels: str | None = None) -> str:
        """Build the prompt for OpenAI difficulty estimation."""
        labels_text = f"\nLabels: {labels}" if labels else ""

        return f"""Analyze the following software development issue and estimate its difficulty level.

Issue Title: {title}
Issue Description: {description[:1000]}{labels_text}

Classify this issue into one of these difficulty levels:
- **beginner**: Simple tasks that require minimal experience. Examples: typo fixes, simple UI changes, documentation updates, basic configuration changes, adding simple validation.
- **intermediate**: Tasks requiring moderate skills and domain knowledge. Examples: implementing a new feature with clear requirements, writing tests, refactoring existing code, fixing bugs with known root cause.
- **advanced**: Complex tasks requiring deep expertise. Examples: performance optimization, security vulnerabilities, complex algorithm implementation, system architecture changes, database migrations.
- **expert**: Tasks requiring specialized knowledge and significant experience. Examples: distributed system design, complex data migration with zero downtime, critical security patches, ML model optimization, custom protocol implementation.

Return a JSON object with exactly these fields:
- "difficulty": one of "beginner", "intermediate", "advanced", "expert"
- "confidence": a number between 0.0 and 1.0
- "reasoning": a brief explanation of why this difficulty was chosen

Return only the JSON object, no markdown, no explanation."""

    @staticmethod
    def estimate_difficulty(
        title: str,
        description: str,
        labels: str | None = None,
    ) -> DifficultyResult:
        """
        Estimate issue difficulty using AI.

        Args:
            title: Issue title
            description: Issue description
            labels: Optional comma-separated labels

        Returns:
            DifficultyResult with difficulty, confidence, and reasoning
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, returning default estimation")
            return IssueDifficultyService._get_default_result()

        client = IssueDifficultyService._get_client()
        if not client:
            return IssueDifficultyService._get_default_result()

        try:
            prompt = IssueDifficultyService._build_prompt(title, description, labels)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software project manager who accurately estimates issue difficulty. Return only a valid JSON object.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=300,
            )

            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            result = json.loads(content)

            difficulty_str = result.get("difficulty", "intermediate")
            confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "AI estimation")

            # Validate difficulty value
            try:
                difficulty = IssueDifficulty(difficulty_str)
            except ValueError:
                difficulty = IssueDifficulty.INTERMEDIATE

            # Clamp confidence between 0 and 1
            confidence = max(0.0, min(1.0, confidence))

            return DifficultyResult(
                difficulty=difficulty,
                confidence=confidence,
                reasoning=reasoning,
            )

        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON")
            return IssueDifficultyService._get_default_result()
        except Exception as e:
            logger.error(f"Failed to estimate difficulty: {e}")
            return IssueDifficultyService._get_default_result()

    @staticmethod
    def _get_default_result() -> DifficultyResult:
        """Return default result when AI is unavailable."""
        return DifficultyResult(
            difficulty=IssueDifficulty.INTERMEDIATE,
            confidence=0.0,
            reasoning="AI estimation unavailable — defaulting to intermediate",
        )
