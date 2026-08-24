from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """
    AI-powered duplicate issue detection using OpenAI embeddings.

    Uses text-embedding-3-small to generate embeddings for issue text,
    then computes cosine similarity against existing issue embeddings.

    When OpenAI is unavailable (missing key, network failure, etc.) a
    keyword-based similarity fallback keeps the feature working.
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
                "OPENAI_API_KEY not configured, using keyword-based duplicate detection"
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
            logger.error(f"Failed to generate embedding, using keyword fallback: {e}")
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
    def _tokenize(text: str) -> set[str]:
        """Split text into lowercase alphanumeric tokens."""
        if not text:
            return set()
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    @staticmethod
    def keyword_similarity(text_a: str, text_b: str) -> float:
        """
        Compute a token-overlap similarity between two texts.

        Combines Jaccard similarity (shared tokens over union) with
        containment (how much of the query text is covered) so that a
        short query matching a longer issue still scores well.

        Returns:
            Similarity score between 0.0 and 1.0
        """
        tokens_a = DuplicateDetectionService._tokenize(text_a)
        tokens_b = DuplicateDetectionService._tokenize(text_b)

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        jaccard = intersection / union if union else 0.0
        containment = intersection / len(tokens_a)

        return 0.6 * jaccard + 0.4 * containment

    @staticmethod
    def find_duplicates(
        db: Session,
        project_id: UUID | str,
        embedding: Optional[list[float]] = None,
        text: Optional[str] = None,
        threshold: float = 0.75,
        limit: int = 5,
    ) -> list[dict]:
        """
        Find duplicate issues by comparing embeddings, with a keyword
        fallback for issues that have no embedding or when no query
        embedding is available.

        Args:
            db: Database session
            project_id: Project ID to search within
            embedding: The embedding to compare against (optional)
            text: The raw query text used for keyword fallback (optional)
            threshold: Minimum similarity score
            limit: Maximum number of results

        Returns:
            List of dicts with issue, issue_id, and similarity_score
        """
        from app.models.issue import Issue

        # Fetch all issues in the project
        stmt = select(Issue).where(Issue.project_id == project_id)

        issues = db.scalars(stmt).all()
        results = []

        for issue in issues:
            score: float | None = None

            # Prefer semantic embedding similarity when both sides exist
            if embedding is not None and issue.embedding:
                try:
                    existing_embedding = DuplicateDetectionService.json_to_embedding(
                        issue.embedding
                    )
                    score = DuplicateDetectionService.cosine_similarity(
                        embedding, existing_embedding
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to compute similarity for issue {issue.id}: {e}"
                    )

            # Keyword-based fallback
            if score is None and text:
                score = DuplicateDetectionService.keyword_similarity(
                    text, f"{issue.title}\n\n{issue.description}"
                )

            if score is None or score < threshold:
                continue

            results.append(
                {
                    "issue": issue,
                    "issue_id": issue.id,
                    "similarity_score": round(score, 4),
                }
            )

        # Sort by similarity score descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return results[:limit]

    @staticmethod
    def _levenshtein_similarity(s1: str, s2: str) -> float:
        """Normalized string edit similarity between s1 and s2 (0.0 to 1.0)."""
        str1 = s1.lower().strip()
        str2 = s2.lower().strip()
        if str1 == str2:
            return 1.0
        if not str1 or not str2:
            return 0.0

        len1, len2 = len(str1), len(str2)
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if str1[i - 1] == str2[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )

        dist = dp[len1][len2]
        max_len = max(len1, len2)
        return max(0.0, 1.0 - (dist / max_len))

    @staticmethod
    def find_duplicate_projects(
        db: Session,
        title: str,
        description: Optional[str] = "",
        tags: Optional[list[str]] = None,
        threshold: float = 0.65,
        limit: int = 5,
        exclude_project_id: Optional[UUID] = None,
    ) -> Any:
        """
        AI-based semantic and hybrid duplicate detection for project submissions (#608).

        Returns DuplicateProjectCheckResponse with matches, confidence scores, and reasons.
        """
        from app.models.project import Project
        from app.schemas.duplicate_detection import (
            DuplicateProjectCheckResponse,
            SuggestedProjectMatch,
        )

        query_title = title.strip()
        query_desc = (description or "").strip()
        query_tags = [t.lower().strip() for t in (tags or []) if t.strip()]

        query_full_text = f"{query_title}\n{query_desc}"
        query_embedding = DuplicateDetectionService.generate_embedding(query_full_text)

        stmt = select(Project)
        if exclude_project_id:
            stmt = stmt.where(Project.id != exclude_project_id)

        existing_projects = list(db.scalars(stmt).all())
        candidates: list[SuggestedProjectMatch] = []

        for p in existing_projects:
            match_reasons: list[str] = []

            # 1. Title Similarity (Jaccard + Levenshtein)
            title_jaccard = DuplicateDetectionService.keyword_similarity(
                query_title, p.title
            )
            title_lev = DuplicateDetectionService._levenshtein_similarity(
                query_title, p.title
            )
            title_score = 0.5 * title_jaccard + 0.5 * title_lev

            if title_lev >= 0.85:
                match_reasons.append(
                    f"Nearly identical project title ({int(title_lev * 100)}% title match)"
                )
            elif title_jaccard >= 0.6:
                match_reasons.append("High title keyword overlap")

            # 2. Description Similarity
            desc_score = 0.0
            p_desc = p.description or ""
            if query_desc and p_desc:
                desc_score = DuplicateDetectionService.keyword_similarity(
                    query_desc, p_desc
                )
                if desc_score >= 0.6:
                    match_reasons.append("High description similarity")

            # 3. Tech Stack / Tag Overlap
            tag_score = 0.0
            p_tags: set[str] = set()
            if p.tech_stack:
                p_tags.update(re.findall(r"[a-z0-9]+", p.tech_stack.lower()))
            if query_tags and p_tags:
                matched_tags = set(query_tags) & p_tags
                if matched_tags:
                    tag_score = len(matched_tags) / max(len(query_tags), len(p_tags))
                    match_reasons.append(
                        f"Matching tech stack/tags: {', '.join(list(matched_tags)[:4])}"
                    )

            # 4. Semantic Embedding Similarity
            semantic_score: Optional[float] = None
            # If project embedding stored or computed on the fly
            if query_embedding and hasattr(p, "embedding") and p.embedding:
                try:
                    p_vec = DuplicateDetectionService.json_to_embedding(p.embedding)
                    semantic_score = DuplicateDetectionService.cosine_similarity(
                        query_embedding, p_vec
                    )
                    if semantic_score >= 0.7:
                        match_reasons.append("Strong AI semantic embedding similarity")
                except Exception as e:
                    logger.debug(f"Failed to compare embedding for project {p.id}: {e}")

            # Hybrid Weighted Combination
            hybrid_score = 0.45 * title_score + 0.35 * desc_score + 0.20 * tag_score

            # Boost score if title is very close
            if title_score >= 0.85:
                hybrid_score = max(hybrid_score, title_score)

            final_score = max(semantic_score or 0.0, hybrid_score)
            final_score = min(1.0, max(0.0, final_score))

            if final_score >= threshold:
                confidence_score = round(final_score * 100.0, 1)
                is_dup = final_score >= threshold
                if not match_reasons:
                    match_reasons.append("Overall content similarity")

                candidates.append(
                    SuggestedProjectMatch(
                        project_id=p.id,
                        title=p.title,
                        slug=p.slug,
                        description=p.description[:200] if p.description else "",
                        similarity_score=round(final_score, 4),
                        confidence_score=confidence_score,
                        is_duplicate=is_dup,
                        match_reasons=match_reasons,
                    )
                )

        candidates.sort(key=lambda x: x.similarity_score, reverse=True)
        top_candidates = candidates[:limit]

        max_score = top_candidates[0].similarity_score if top_candidates else 0.0
        has_duplicates = any(c.is_duplicate for c in top_candidates)

        return DuplicateProjectCheckResponse(
            has_duplicates=has_duplicates,
            max_similarity_score=round(max_score, 4),
            suggested_projects=top_candidates,
            threshold_used=threshold,
            manual_override_allowed=True,
        )
