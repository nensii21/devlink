import pytest
from uuid import uuid4

from app.models.user import User
from app.models.project import Project
from app.models.organization import Organization
from app.models.skill import Skill
from app.services.search_index_service import (
    SearchIndexService,
    search_index_engine,
    analytics_store,
)


@pytest.fixture
def seed_search_data(db):
    user = User(
        id=uuid4(),
        first_name="Frontend",
        last_name="Architect",
        username=f"react_expert_{uuid4().hex[:6]}",
        email=f"react_{uuid4().hex[:6]}@example.com",
        role="Senior Developer",
        headline="React & TypeScript Specialist",
        bio="Building scalable web apps with React and Next.js",
        is_active=True,
        is_verified=True,
    )
    project = Project(
        id=uuid4(),
        title="DevLink Analytics Platform",
        slug=f"devlink-analytics-{uuid4().hex[:6]}",
        owner_id=user.id,
        description="Real-time analytics and tracking system for developers",
        tech_stack="React TypeScript FastAPI Python",
    )
    org = Organization(
        id=uuid4(),
        owner_id=user.id,
        name="OpenSource Builders",
        slug=f"opensource-builders-{uuid4().hex[:4]}",
        description="Community of passionate open-source developers",
    )
    skill = Skill(
        id=uuid4(),
        name="TypeScript",
        normalized_name="typescript",
        slug=f"typescript-{uuid4().hex[:4]}",
        category="Languages",
        description="Typed JavaScript at scale",
    )

    db.add_all([user, project, org, skill])
    db.commit()

    return {"user": user, "project": project, "org": org, "skill": skill}


def test_reindex_all(db, seed_search_data):
    res = SearchIndexService.reindex_all(db)
    assert res["status"] == "reindexed"
    assert res["indexed_documents"] >= 4
    assert search_index_engine.is_indexed is True


def test_execute_search_query_matching(db, seed_search_data):
    SearchIndexService.reindex_all(db)

    # Search for "react"
    res = SearchIndexService.execute_search(db, query="React", limit=10)
    assert res.total_results >= 2
    assert res.execution_time_ms >= 0.0

    titles = [r.title for r in res.results]
    assert any("react" in t.lower() or "devlink" in t.lower() for t in titles)


def test_search_category_filter(db, seed_search_data):
    SearchIndexService.reindex_all(db)

    res = SearchIndexService.execute_search(
        db, query="React", category="projects", limit=10
    )
    for item in res.results:
        assert item.entity_type == "projects"


def test_search_analytics_tracking(db, seed_search_data):
    analytics_store.logs.clear()

    SearchIndexService.execute_search(db, query="python", category="all")
    SearchIndexService.execute_search(db, query="nonexistentqueryxyz", category="all")

    metrics = SearchIndexService.get_analytics()
    assert metrics.total_searches == 2
    assert metrics.avg_latency_ms >= 0.0
    assert len(metrics.top_queries) >= 1
    assert any(q["query"] == "nonexistentqueryxyz" for q in metrics.zero_result_queries)


def test_run_search_benchmark(db, seed_search_data):
    report = SearchIndexService.run_benchmark(db, query="react", iterations=5)
    assert report.status == "success"
    assert report.query == "react"
    assert report.iterations == 5
    assert report.naive_sql_avg_ms >= 0.0
    assert report.inverted_index_avg_ms >= 0.0
    assert report.speedup_factor >= 0.0


def test_search_indexed_api_endpoints(client, seed_search_data):
    # Test reindex API
    reindex_res = client.post("/api/v1/search/index/reindex")
    assert reindex_res.status_code == 200
    assert reindex_res.json()["status"] == "reindexed"

    # Test indexed search API
    search_res = client.get("/api/v1/search/indexed?q=React")
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["query"] == "React"
    assert "execution_time_ms" in data

    # Test analytics API
    analytics_res = client.get("/api/v1/search/analytics")
    assert analytics_res.status_code == 200
    assert "total_searches" in analytics_res.json()

    # Test benchmark API
    benchmark_res = client.get("/api/v1/search/benchmark?q=React&iterations=3")
    assert benchmark_res.status_code == 200
    bench_data = benchmark_res.json()
    assert bench_data["status"] == "success"
    assert "speedup_factor" in bench_data
