from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """
    AI-powered duplicate issue detection using OpenAI embeddings.

    Uses text-embedding-3-small to generate embeddings for issue text,
    then computes cosine similarity against existing issue embeddings.
    """

    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536

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
    def generate_embedding(text: str) -> Optional[list[float]]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The text to embed (typically title + description)

        Returns:
            List of floats representing the embedding, or None on failure
        """
        if not settings.OPENAI_API_KEY:
            logger.warning(
                "OPENAI_API_KEY not configured, skipping embedding generation"
            )
            return None

        client = DuplicateDetectionService._get_client()
        if not client:
            return None

        try:
            # Truncate text to avoid token limits
            truncated_text = text[:8000]

            response = client.embeddings.create(
                model=DuplicateDetectionService.EMBEDDING_MODEL,
                input=truncated_text,
                dimensions=DuplicateDetectionService.EMBEDDING_DIMENSIONS,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    @staticmethod
    def embedding_to_json(embedding: list[float]) -> str:
        """Serialize embedding to JSON string for storage."""
        return json.dumps(embedding)

    @staticmethod
    def json_to_embedding(json_str: str) -> list[float]:
        """Deserialize embedding from JSON string."""
        return json.loads(json_str)

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Similarity score between -1 and 1
        """
        if len(a) != len(b):
            raise ValueError("Vectors must have the same length")

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    @staticmethod
    def find_duplicates(
        db: Session,
        project_id: str,
        embedding: list[float],
        threshold: float = 0.75,
        limit: int = 5,
    ) -> list[dict]:
        """
        Find duplicate issues by comparing embeddings.

        Args:
            db: Database session
            project_id: Project ID to search within
            embedding: The embedding to compare against
            threshold: Minimum similarity score
            limit: Maximum number of results

        Returns:
            List of dicts with issue_id and similarity_score
        """
        from app.models.issue import Issue

        # Fetch all issues in the project that have embeddings
        stmt = select(Issue).where(
            Issue.project_id == project_id,
            Issue.embedding.isnot(None),
        )

        issues = db.scalars(stmt).all()
        results = []

        for issue in issues:
            if not issue.embedding:
                continue

            try:
                existing_embedding = DuplicateDetectionService.json_to_embedding(
                    issue.embedding
                )
                score = DuplicateDetectionService.cosine_similarity(
                    embedding, existing_embedding
                )

                if score >= threshold:
                    results.append(
                        {
                            "issue_id": issue.id,
                            "similarity_score": round(score, 4),
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to compute similarity for issue {issue.id}: {e}"
                )
                continue

        # Sort by similarity score descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return results[:limit]
