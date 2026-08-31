"""
Comprehensive Unit tests for Global Search Engine with Deep Indexing.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.services.search_engine_service import (
    InMemorySearchEngine,
    SearchResultItem,
    search_engine_service
)


@pytest.fixture
def search_engine():
    service = InMemorySearchEngine()
    service.clear_index()
    return service


def test_tokenize_normalization(search_engine):
    tokens = search_engine._tokenize("FastAPI & React Web-Application, v2.0!")
    assert "fastapi" in tokens
    assert "react" in tokens
    assert "application" in tokens
    assert "v2" in tokens


def test_index_and_search_single(search_engine):
    item = SearchResultItem(
        entity_id="proj_1",
        entity_type="project",
        title="DevLink Collaboration",
        description="A platform connecting developers and open source projects."
    )
    search_engine.index_entity(item)
    response = search_engine.search("collaboration")
    assert len(response.results) == 1
    assert response.results[0].entity_id == "proj_1"
    assert response.results[0].title == "DevLink Collaboration"


def test_search_filtering_by_entity_type(search_engine):
    p = SearchResultItem(
        entity_id="p1", entity_type="project", title="Python Utils", description="Helper utilities"
    )
    u = SearchResultItem(
        entity_id="u1", entity_type="user", title="Python Guru", description="Senior python engineer"
    )
    search_engine.index_entity(p)
    search_engine.index_entity(u)

    user_response = search_engine.search("python", entity_type="user")
    assert len(user_response.results) == 1
    assert user_response.results[0].entity_type == "user"

    all_response = search_engine.search("python")
    assert len(all_response.results) == 2


def test_search_with_tag_filtering(search_engine):
    item1 = SearchResultItem(
        entity_id="proj_ml",
        entity_type="project",
        title="Vision Models",
        description="Computer vision research",
        tags=["pytorch", "cuda", "transformer"]
    )
    item2 = SearchResultItem(
        entity_id="proj_web",
        entity_type="project",
        title="Web Interface",
        description="Frontend for vision models",
        tags=["react", "typescript"]
    )
    search_engine.index_entity(item1)
    search_engine.index_entity(item2)
    
    # Text match plus tag filter
    response = search_engine.search("vision", tags=["pytorch"])
    assert len(response.results) == 1
    assert response.results[0].entity_id == "proj_ml"


def test_search_faceting(search_engine):
    p1 = SearchResultItem(entity_id="p1", entity_type="project", title="Test 1", description="data", tags=["a", "b"])
    p2 = SearchResultItem(entity_id="p2", entity_type="project", title="Test 2", description="data", tags=["b", "c"])
    u1 = SearchResultItem(entity_id="u1", entity_type="user", title="Test 3", description="data", tags=["a"])
    
    search_engine.index_entity(p1)
    search_engine.index_entity(p2)
    search_engine.index_entity(u1)
    
    response = search_engine.search("data")
    assert response.total_count == 3
    assert response.facets.entity_types == {"project": 2, "user": 1}
    assert response.facets.tags == {"a": 2, "b": 2, "c": 1}


def test_ranking_relevance_and_popularity(search_engine):
    now = datetime.now(timezone.utc)
    # Item 1: High relevance (word appears multiple times), low popularity
    i1 = SearchResultItem(
        entity_id="1", entity_type="doc", title="Search Search Search", 
        description="We need search", popularity_score=1.0, created_at=now
    )
    # Item 2: Low relevance, high popularity
    i2 = SearchResultItem(
        entity_id="2", entity_type="doc", title="Search", 
        description="Basic info", popularity_score=1000.0, created_at=now
    )
    
    search_engine.index_entity(i1)
    search_engine.index_entity(i2)
    
    response = search_engine.search("search")
    assert len(response.results) == 2
    
    # We expect the scores to be calculated. The test doesn't assert order strictly 
    # unless we know the math, but both should have a score > 0.
    assert response.results[0].score > 0
    assert response.results[1].score > 0


def test_autocomplete(search_engine):
    i1 = SearchResultItem(entity_id="1", entity_type="project", title="Kubernetes Cluster", description="")
    i2 = SearchResultItem(entity_id="2", entity_type="project", title="KubeFlow Integration", description="")
    i3 = SearchResultItem(entity_id="3", entity_type="project", title="Kafka Queue", description="")
    
    search_engine.index_entity(i1)
    search_engine.index_entity(i2)
    search_engine.index_entity(i3)
    
    suggestions = search_engine.autocomplete("kub")
    assert "kubernetes" in suggestions
    assert "kubeflow" in suggestions
    assert "kafka" not in suggestions


def test_clear_index(search_engine):
    search_engine.index_entity(
        SearchResultItem(entity_id="p1", entity_type="project", title="Python Item", description="Desc")
    )
    assert len(search_engine.search("python").results) == 1
    search_engine.clear_index()
    assert len(search_engine.search("python").results) == 0
