from __future__ import annotations

"""
AI-powered tech stack recommendation service.

Uses OpenAI to recommend technologies for new projects based on the project idea.
Falls back to a rule-based default when OpenAI is unavailable.
"""


import json
import logging

from app.core.config import settings
from app.schemas.ai import (
    ProjectDescriptionGenerateRequest,
    ProjectDescriptionGenerateResponse,
)
from app.schemas.tech_stack import (
    TechStackRecommendation,
    TechStackRequest,
    TechStackResponse,
)

logger = logging.getLogger(__name__)

# pyrefly: ignore [missing-import]
from openai import OpenAI

DESCRIPTION_SYSTEM_PROMPT = """You are an expert technical writer and project manager helping developers write compelling project descriptions.

Given a short prompt or idea, generate a comprehensive, professional project description. The description should:
1. Clearly state the project's purpose and value proposition.
2. Outline key features or functionality.
3. Be engaging, well-structured, and concise (around 2-3 paragraphs).

Return the description as plain text, formatted nicely with markdown if appropriate. Do not include JSON formatting or other structural wrappers."""

SYSTEM_PROMPT = """You are a senior software architect helping developers choose the best tech stack for their project.

Given a project idea, recommend 6-10 technologies ranked by importance. For each technology, provide:
- name: The technology name (e.g. "React", "FastAPI", "PostgreSQL")
- category: One of "frontend", "backend", "database", "cache", "devops", "testing", "auth", "storage"
- reason: A concise 1-2 sentence explanation of why this technology is a good fit
- confidence: A number between 0 and 1 indicating how confident you are that this technology fits the project idea

Also provide a brief summary (2-3 sentences) explaining the overall stack strategy.

IMPORTANT: Return ONLY valid JSON matching this exact schema:
{
  "recommendations": [
    {"name": "...", "category": "...", "reason": "...", "confidence": 0.0}
  ],
  "summary": "..."
}

Do not include any text outside the JSON object."""


def _rec(
    name: str, category: str, reason: str, confidence: float
) -> TechStackRecommendation:
    """Build a fallback recommendation with an explicit confidence score."""
    return TechStackRecommendation(
        name=name,
        category=category,
        reason=reason,
        confidence=confidence,
    )


def _fallback_response(request: TechStackRequest) -> TechStackResponse:
    """Rule-based fallback when OpenAI is unavailable."""
    idea_lower = request.project_idea.lower()

    recommendations: list[TechStackRecommendation] = []

    if any(
        kw in idea_lower
        for kw in ["food", "delivery", "ecommerce", "e-commerce", "shop", "marketplace"]
    ):
        recommendations = [
            _rec(
                "React",
                "frontend",
                "Fast, component-based UI ideal for dynamic product catalogs and real-time order tracking.",
                0.85,
            ),
            _rec(
                "Next.js",
                "frontend",
                "Server-side rendering improves SEO for restaurant/store pages and enables fast page loads.",
                0.8,
            ),
            _rec(
                "FastAPI",
                "backend",
                "High-performance async Python framework perfect for handling concurrent orders and real-time updates.",
                0.85,
            ),
            _rec(
                "PostgreSQL",
                "database",
                "Robust relational database for orders, users, inventory, and payment records with ACID compliance.",
                0.9,
            ),
            _rec(
                "Redis",
                "cache",
                "In-memory cache for session management, cart data, and real-time order status.",
                0.75,
            ),
            _rec(
                "Docker",
                "devops",
                "Containerization ensures consistent deployments across development and production environments.",
                0.8,
            ),
        ]
    elif any(
        kw in idea_lower for kw in ["chat", "messaging", "social", "community", "forum"]
    ):
        recommendations = [
            _rec(
                "React",
                "frontend",
                "Component-based architecture is ideal for building real-time chat interfaces.",
                0.85,
            ),
            _rec(
                "Node.js",
                "backend",
                "Event-driven architecture handles thousands of concurrent WebSocket connections efficiently.",
                0.85,
            ),
            _rec(
                "MongoDB",
                "database",
                "Flexible document storage suits varied message formats and conversation threads.",
                0.8,
            ),
            _rec(
                "Redis",
                "cache",
                "Pub/Sub capability powers real-time message broadcasting between connected clients.",
                0.85,
            ),
            _rec(
                "WebSockets",
                "backend",
                "Native bidirectional communication for instant message delivery and typing indicators.",
                0.75,
            ),
        ]
    elif any(
        kw in idea_lower
        for kw in ["ai", "ml", "machine learning", "data", "analytics", "analytics"]
    ):
        recommendations = [
            _rec(
                "React",
                "frontend",
                "Interactive dashboard components with rich data visualization libraries like D3.js and Recharts.",
                0.8,
            ),
            _rec(
                "Python",
                "backend",
                "Rich ecosystem of ML/AI libraries (scikit-learn, PyTorch, TensorFlow) for model serving.",
                0.9,
            ),
            _rec(
                "FastAPI",
                "backend",
                "Async support handles ML inference requests without blocking, with automatic API docs.",
                0.85,
            ),
            _rec(
                "PostgreSQL",
                "database",
                "Structured data storage with JSON support for flexible schema evolution.",
                0.8,
            ),
            _rec(
                "Redis",
                "cache",
                "Caches model predictions and feature store data for low-latency inference.",
                0.75,
            ),
        ]
    else:
        recommendations = [
            _rec(
                "React",
                "frontend",
                "Industry-standard component library with massive ecosystem and community support.",
                0.8,
            ),
            _rec(
                "FastAPI",
                "backend",
                "Modern, fast Python web framework with automatic OpenAPI docs and type safety.",
                0.8,
            ),
            _rec(
                "PostgreSQL",
                "database",
                "Battle-tested relational database with excellent performance and extensibility.",
                0.85,
            ),
            _rec(
                "Redis",
                "cache",
                "High-performance in-memory store for caching, sessions, and real-time features.",
                0.7,
            ),
            _rec(
                "Docker",
                "devops",
                "Industry-standard containerization for reproducible builds and easy deployments.",
                0.75,
            ),
        ]

    return TechStackResponse(
        project_idea=request.project_idea,
        recommendations=recommendations,
        summary="This stack balances developer productivity with production readiness. "
        "The frontend and backend are decoupled for independent scaling, "
        "with PostgreSQL for reliable data persistence and Redis for performance-critical caching.",
    )


class AIService:
    """AI-powered recommendation service."""

    @staticmethod
    def recommend_tech_stack(request: TechStackRequest) -> TechStackResponse:
        """
        Recommend a tech stack for a project idea using OpenAI.

        Falls back to rule-based recommendations if OpenAI is unavailable
        or the API key is not configured.
        """
        if not settings.OPENAI_API_KEY:
            logger.info("OPENAI_API_KEY not configured, using fallback recommendations")
            return _fallback_response(request)

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Project idea: {request.project_idea}",
                    },
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            content = response.choices[0].message.content or ""
            data = json.loads(content)

            recommendations: list[TechStackRecommendation] = []
            for rec in data.get("recommendations", []):
                if not isinstance(rec, dict) or not rec.get("name"):
                    continue
                try:
                    confidence = max(0.0, min(1.0, float(rec.get("confidence", 0.5))))
                except (TypeError, ValueError):
                    confidence = 0.5
                recommendations.append(
                    TechStackRecommendation(
                        name=rec["name"],
                        category=rec.get("category", "general"),
                        reason=rec.get("reason", ""),
                        confidence=confidence,
                    )
                )

            if not recommendations:
                logger.warning("Empty recommendations from OpenAI, using fallback")
                return _fallback_response(request)

            return TechStackResponse(
                project_idea=request.project_idea,
                recommendations=recommendations,
                summary=data.get("summary"),
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error("Failed to parse OpenAI response: %s", e)
            return _fallback_response(request)
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
            return _fallback_response(request)

    @staticmethod
    def generate_project_description(
        request: ProjectDescriptionGenerateRequest,
    ) -> ProjectDescriptionGenerateResponse:
        """
        Generate a comprehensive project description based on a short prompt using OpenAI.
        """
        fallback_description = (
            "A comprehensive project description could not be generated at this time. "
            "Please manually describe your project's goals, key features, and target audience."
        )

        if not settings.OPENAI_API_KEY:
            logger.info("OPENAI_API_KEY not configured, using fallback description")
            return ProjectDescriptionGenerateResponse(description=fallback_description)

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": DESCRIPTION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Project idea: {request.prompt}",
                    },
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            content = response.choices[0].message.content or ""
            if not content.strip():
                logger.warning("Empty description from OpenAI, using fallback")
                return ProjectDescriptionGenerateResponse(
                    description=fallback_description
                )

            return ProjectDescriptionGenerateResponse(description=content.strip())

        except Exception as e:
            logger.error("OpenAI API error generating description: %s", e)
            return ProjectDescriptionGenerateResponse(description=fallback_description)
