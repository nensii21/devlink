import time
import re
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.models.project import Project
from app.models.organization import Organization
from app.models.message import Message
from app.models.skill import Skill
from app.models.project_skill import ProjectSkill
from app.schemas.search_index import (
    SearchIndexedResultItem,
    SearchIndexedResponse,
    SearchAnalyticsMetric,
    SearchBenchmarkReport,
)

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    words = re.findall(r"\b\w+\b", text.lower())
    return [w for w in words if len(w) > 1 and w not in STOP_WORDS]


class SearchAnalyticsStore:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def record_search(
        self, query: str, category: Optional[str], result_count: int, latency_ms: float
    ):
        q_norm = query.strip().lower()
        if not q_norm:
            return
        self.logs.append(
            {
                "query": q_norm,
                "category": category or "all",
                "result_count": result_count,
                "latency_ms": latency_ms,
                "timestamp": time.time(),
            }
        )

    def get_metrics(self) -> SearchAnalyticsMetric:
        if not self.logs:
            return SearchAnalyticsMetric(
                total_searches=0,
                avg_latency_ms=0.0,
                top_queries=[],
                zero_result_queries=[],
                category_distribution={},
            )

        total_searches = len(self.logs)
        avg_latency = sum(l["latency_ms"] for l in self.logs) / total_searches

        query_counts = Counter(l["query"] for l in self.logs)
        top_queries = [
            {"query": q, "count": count} for q, count in query_counts.most_common(5)
        ]

        zero_logs = [l["query"] for l in self.logs if l["result_count"] == 0]
        zero_counts = Counter(zero_logs)
        zero_result_queries = [
            {"query": q, "count": count} for q, count in zero_counts.most_common(5)
        ]

        cat_counts = Counter(l["category"] for l in self.logs)

        return SearchAnalyticsMetric(
            total_searches=total_searches,
            avg_latency_ms=round(avg_latency, 3),
            top_queries=top_queries,
            zero_result_queries=zero_result_queries,
            category_distribution=dict(cat_counts),
        )


analytics_store = SearchAnalyticsStore()


class GlobalSearchIndex:
    def __init__(self):
        # term -> { doc_id -> score_weight }
        self.index: Dict[str, Dict[str, float]] = defaultdict(dict)
        # doc_id -> doc_dict
        self.documents: Dict[str, Dict[str, Any]] = {}
        # doc_id -> set of terms
        self.doc_terms: Dict[str, set] = defaultdict(set)
        self.is_indexed = False

    def remove_document(self, doc_id: str):
        if doc_id in self.doc_terms:
            for term in self.doc_terms[doc_id]:
                if doc_id in self.index[term]:
                    del self.index[term][doc_id]
            del self.doc_terms[doc_id]
        if doc_id in self.documents:
            del self.documents[doc_id]

    def add_document(
        self,
        doc_id: str,
        entity_type: str,
        title: str,
        description: Optional[str],
        weighted_fields: Dict[str, tuple[str, float]],
        popularity_boost: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.remove_document(doc_id)

        doc_data = {
            "id": doc_id,
            "entity_type": entity_type,
            "title": title,
            "description": description or "",
            "popularity_boost": popularity_boost,
            "metadata": metadata or {},
        }
        self.documents[doc_id] = doc_data

        term_weights = defaultdict(float)

        for field_name, (text_val, weight) in weighted_fields.items():
            if not text_val:
                continue
            tokens = _tokenize(text_val)
            for token in tokens:
                term_weights[token] += weight

        for term, weight in term_weights.items():
            final_weight = weight + (popularity_boost * 0.1)
            self.index[term][doc_id] = final_weight
            self.doc_terms[doc_id].add(term)

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SearchIndexedResultItem]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        doc_scores: Dict[str, float] = defaultdict(float)

        for token in query_tokens:
            if token in self.index:
                for doc_id, weight in self.index[token].items():
                    doc_scores[doc_id] += weight
            # Prefix partial matching
            else:
                for indexed_term in self.index:
                    if indexed_term.startswith(token):
                        for doc_id, weight in self.index[indexed_term].items():
                            doc_scores[doc_id] += weight * 0.7

        results = []
        for doc_id, score in doc_scores.items():
            doc = self.documents.get(doc_id)
            if not doc:
                continue

            if (
                category
                and category.lower() != "all"
                and doc["entity_type"].lower() != category.lower()
            ):
                continue

            results.append(
                SearchIndexedResultItem(
                    id=doc["id"],
                    entity_type=doc["entity_type"],
                    title=doc["title"],
                    description=doc["description"],
                    score=round(score, 3),
                    metadata=doc["metadata"],
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[offset : offset + limit]


search_index_engine = GlobalSearchIndex()


class SearchIndexService:
    @classmethod
    def reindex_all(cls, db: Session):
        engine = search_index_engine
        engine.index.clear()
        engine.documents.clear()
        engine.doc_terms.clear()

        # 1. Developers (Users)
        users = db.query(User).filter(User.is_active.is_(True)).all()
        for u in users:
            doc_id = f"dev_{u.id}"
            full_name = f"{u.first_name} {u.last_name}".strip()
            engine.add_document(
                doc_id=doc_id,
                entity_type="developers",
                title=u.username or full_name,
                description=u.headline or u.bio or "",
                weighted_fields={
                    "username": (u.username, 5.0),
                    "name": (full_name, 4.0),
                    "role": (u.role, 3.0),
                    "headline": (u.headline, 2.0),
                    "bio": (u.bio, 1.0),
                },
                popularity_boost=(
                    2.0
                    if (u.is_verified and getattr(u, "premium", False))
                    else (1.0 if u.is_verified else 0.0)
                ),
                metadata={
                    "user_id": str(u.id),
                    "username": u.username,
                    "avatar": u.profile_image,
                },
            )

        # 2. Projects
        projects = db.query(Project).all()
        for p in projects:
            doc_id = f"project_{p.id}"
            title_text = getattr(p, "title", None) or getattr(p, "name", "Project")
            stack_text = getattr(p, "tech_stack", None) or " ".join(
                getattr(p, "stack", []) or []
            )
            engine.add_document(
                doc_id=doc_id,
                entity_type="projects",
                title=title_text,
                description=p.description or getattr(p, "tagline", "") or "",
                weighted_fields={
                    "title": (title_text, 5.0),
                    "stack": (stack_text, 3.0),
                    "description": (p.description, 2.0),
                },
                popularity_boost=float(getattr(p, "stars", 0) or 0),
                metadata={
                    "project_id": str(p.id),
                    "title": title_text,
                    "stars": getattr(p, "stars", 0),
                },
            )

        # 3. Organizations
        orgs = db.query(Organization).all()
        for o in orgs:
            doc_id = f"org_{o.id}"
            engine.add_document(
                doc_id=doc_id,
                entity_type="organizations",
                title=o.name,
                description=o.description or "",
                weighted_fields={
                    "name": (o.name, 5.0),
                    "slug": (o.slug, 4.0),
                    "description": (o.description, 2.0),
                },
                popularity_boost=0.0,
                metadata={"organization_id": str(o.id), "slug": o.slug},
            )

        # 4. Discussions (Messages)
        messages = db.query(Message).limit(200).all()
        for m in messages:
            doc_id = f"msg_{m.id}"
            content_preview = m.content[:100] if m.content else "Discussion message"
            engine.add_document(
                doc_id=doc_id,
                entity_type="discussions",
                title=f"Message in conversation {str(m.conversation_id)[:8]}",
                description=content_preview,
                weighted_fields={
                    "content": (m.content, 2.0),
                },
                popularity_boost=0.0,
                metadata={
                    "message_id": str(m.id),
                    "conversation_id": str(m.conversation_id),
                },
            )

        # 5. Skills
        skills = db.query(Skill).all()
        for s in skills:
            doc_id = f"skill_{s.id}"
            engine.add_document(
                doc_id=doc_id,
                entity_type="skills",
                title=s.name,
                description=s.description or s.category or "",
                weighted_fields={
                    "name": (s.name, 5.0),
                    "category": (s.category, 3.0),
                    "description": (s.description, 2.0),
                },
                popularity_boost=0.0,
                metadata={"skill_id": str(s.id), "category": s.category},
            )

        # 6. Technologies (Project Skills)
        proj_skills = db.query(ProjectSkill).all()
        for ps in proj_skills:
            doc_id = f"tech_{ps.id}"
            engine.add_document(
                doc_id=doc_id,
                entity_type="technologies",
                title=ps.name,
                description=f"Technology used in project {str(ps.project_id)[:8]}",
                weighted_fields={
                    "name": (ps.name, 5.0),
                    "category": (ps.category, 3.0),
                },
                popularity_boost=0.0,
                metadata={
                    "project_skill_id": str(ps.id),
                    "project_id": str(ps.project_id),
                },
            )

        engine.is_indexed = True
        return {"status": "reindexed", "indexed_documents": len(engine.documents)}

    @classmethod
    def execute_search(
        cls,
        db: Session,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchIndexedResponse:
        start_time = time.perf_counter()

        if (
            not search_index_engine.is_indexed
            or len(search_index_engine.documents) == 0
        ):
            cls.reindex_all(db)

        results = search_index_engine.search(
            query=query,
            category=category,
            limit=limit,
            offset=offset,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        analytics_store.record_search(
            query=query,
            category=category,
            result_count=len(results),
            latency_ms=elapsed_ms,
        )

        return SearchIndexedResponse(
            query=query,
            category=category,
            total_results=len(results),
            execution_time_ms=round(elapsed_ms, 3),
            results=results,
        )

    @classmethod
    def get_analytics(cls) -> SearchAnalyticsMetric:
        return analytics_store.get_metrics()

    @classmethod
    def run_benchmark(
        cls, db: Session, query: str = "dev", iterations: int = 10
    ) -> SearchBenchmarkReport:
        if not search_index_engine.is_indexed:
            cls.reindex_all(db)

        # 1. Naive SQL ILIKE search timing
        sql_start = time.perf_counter()
        pattern = f"%{query}%"
        for _ in range(iterations):
            db.query(User).filter(
                or_(User.username.ilike(pattern), User.first_name.ilike(pattern))
            ).all()
            db.query(Project).filter(Project.title.ilike(pattern)).all()
            db.query(Organization).filter(Organization.name.ilike(pattern)).all()
        sql_elapsed = (time.perf_counter() - sql_start) * 1000.0 / iterations

        # 2. Optimized Inverted Index search timing
        idx_start = time.perf_counter()
        for _ in range(iterations):
            search_index_engine.search(query=query, limit=20)
        idx_elapsed = (time.perf_counter() - idx_start) * 1000.0 / iterations

        # Prevent division by zero
        idx_elapsed = max(idx_elapsed, 0.05)
        speedup = round(sql_elapsed / idx_elapsed, 2)
        reduction = round(
            max(0.0, ((sql_elapsed - idx_elapsed) / sql_elapsed) * 100.0), 1
        )

        return SearchBenchmarkReport(
            query=query,
            iterations=iterations,
            naive_sql_avg_ms=round(sql_elapsed, 3),
            inverted_index_avg_ms=round(idx_elapsed, 3),
            latency_reduction_percent=reduction,
            speedup_factor=speedup,
            status="success",
        )
