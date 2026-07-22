"""
AI-powered tech stack recommendation service.

Uses OpenAI to recommend technologies for new projects based on the project idea.
Falls back to a rule-based default when OpenAI is unavailable.
"""

from __future__ import annotations

import json
import logging

from app.core.config import settings
from app.schemas.tech_stack import (
    TechStackRecommendation,
    TechStackRequest,
    TechStackResponse,
)

logger = logging.getLogger(__name__)

# pyrefly: ignore [missing-import]
from openai import OpenAI


SYSTEM_PROMPT = """You are a senior software architect helping developers choose the best tech stack for their project.

Given a project idea, recommend 6-10 technologies ranked by importance. For each technology, provide:
- name: The technology name (e.g. "React", "FastAPI", "PostgreSQL")
- category: One of "frontend", "backend", "database", "cache", "devops", "testing", "auth", "storage"
- reason: A concise 1-2 sentence explanation of why this technology is a good fit

Also provide a brief summary (2-3 sentences) explaining the overall stack strategy.

IMPORTANT: Return ONLY valid JSON matching this exact schema:
{
  "recommendations": [
    {"name": "...", "category": "...", "reason": "..."}
  ],
  "summary": "..."
}

Do not include any text outside the JSON object."""


def _fallback_response(request: TechStackRequest) -> TechStackResponse:
    """Rule-based fallback when OpenAI is unavailable."""
    idea_lower = request.project_idea.lower()

    recommendations: list[TechStackRecommendation] = []

    if any(kw in idea_lower for kw in ["food", "delivery", "ecommerce", "e-commerce", "shop", "marketplace"]):
        recommendations = [
            TechStackRecommendation(name="React", category="frontend", reason="Fast, component-based UI ideal for dynamic product catalogs and real-time order tracking."),
            TechStackRecommendation(name="Next.js", category="frontend", reason="Server-side rendering improves SEO for restaurant/store pages and enables fast page loads."),
            TechStackRecommendation(name="FastAPI", category="backend", reason="High-performance async Python framework perfect for handling concurrent orders and real-time updates."),
            TechStackRecommendation(name="PostgreSQL", category="database", reason="Robust relational database for orders, users, inventory, and payment records with ACID compliance."),
            TechStackRecommendation(name="Redis", category="cache", reason="In-memory cache for session management, cart data, and real-time order status."),
            TechStackRecommendation(name="Docker", category="devops", reason="Containerization ensures consistent deployments across development and production environments."),
        ]
    elif any(kw in idea_lower for kw in ["chat", "messaging", "social", "community", "forum"]):
        recommendations = [
            TechStackRecommendation(name="React", category="frontend", reason="Component-based architecture is ideal for building real-time chat interfaces."),
            TechStackRecommendation(name="Node.js", category="backend", reason="Event-driven architecture handles thousands of concurrent WebSocket connections efficiently."),
            TechStackRecommendation(name="MongoDB", category="database", reason="Flexible document storage suits varied message formats and conversation threads."),
            TechStackRecommendation(name="Redis", category="cache", reason="Pub/Sub capability powers real-time message broadcasting between connected clients."),
            TechStackRecommendation(name="WebSockets", category="backend", reason="Native bidirectional communication for instant message delivery and typing indicators."),
        ]
    elif any(kw in idea_lower for kw in ["ai", "ml", "machine learning", "data", "analytics", "analytics"]):
        recommendations = [
            TechStackRecommendation(name="React", category="frontend", reason="Interactive dashboard components with rich data visualization libraries like D3.js and Recharts."),
            TechStackRecommendation(name="Python", category="backend", reason="Rich ecosystem of ML/AI libraries (scikit-learn, PyTorch, TensorFlow) for model serving."),
            TechStackRecommendation(name="FastAPI", category="backend", reason="Async support handles ML inference requests without blocking, with automatic API docs."),
            TechStackRecommendation(name="PostgreSQL", category="database", reason="Structured data storage with JSON support for flexible schema evolution."),
            TechStackRecommendation(name="Redis", category="cache", reason="Caches model predictions and feature store data for low-latency inference."),
        ]
    else:
        recommendations = [
            TechStackRecommendation(name="React", category="frontend", reason="Industry-standard component library with massive ecosystem and community support."),
            TechStackRecommendation(name="FastAPI", category="backend", reason="Modern, fast Python web framework with automatic OpenAPI docs and type safety."),
            TechStackRecommendation(name="PostgreSQL", category="database", reason="Battle-tested relational database with excellent performance and extensibility."),
            TechStackRecommendation(name="Redis", category="cache", reason="High-performance in-memory store for caching, sessions, and real-time features."),
            TechStackRecommendation(name="Docker", category="devops", reason="Industry-standard containerization for reproducible builds and easy deployments."),
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
                    {"role": "user", "content": f"Project idea: {request.project_idea}"},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            content = response.choices[0].message.content or ""
            data = json.loads(content)

            recommendations = [
                TechStackRecommendation(**rec)
                for rec in data.get("recommendations", [])
            ]

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
