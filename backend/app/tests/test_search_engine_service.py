"""
Comprehensive Unit tests for Global Search Engine with Deep Indexing.
"""

import pytest
from app.services.search_engine_service import (
    SearchEngineService,
    SearchResultItem,
    search_engine_service
)


@pytest.fixture
def search_engine():
    service = SearchEngineService()
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
    results = search_engine.search("collaboration")
    assert len(results) == 1
    assert results[0].entity_id == "proj_1"
    assert results[0].title == "DevLink Collaboration"


def test_search_filtering_by_entity_type(search_engine):
    p = SearchResultItem(
        entity_id="p1", entity_type="project", title="Python Utils", description="Helper utilities"
    )
    u = SearchResultItem(
        entity_id="u1", entity_type="user", title="Python Guru", description="Senior python engineer"
    )
    search_engine.index_entity(p)
    search_engine.index_entity(u)

    user_results = search_engine.search("python", entity_type="user")
    assert len(user_results) == 1
    assert user_results[0].entity_type == "user"

    all_results = search_engine.search("python")
    assert len(all_results) == 2


def test_search_with_tag_indexing(search_engine):
    item = SearchResultItem(
        entity_id="proj_ml",
        entity_type="project",
        title="Vision Models",
        description="Computer vision research",
        tags=["pytorch", "cuda", "transformer"]
    )
    search_engine.index_entity(item)
    results = search_engine.search("pytorch")
    assert len(results) == 1
    assert results[0].entity_id == "proj_ml"


def test_tokenize_empty_and_special_characters(search_engine):
    tokens = search_engine._tokenize("!@#$%^&*()_+=-`~[]{}|;:'",.<>?/")
    assert tokens == []


def test_search_no_match(search_engine):
    item = SearchResultItem(
        entity_id="proj_unique",
        entity_type="project",
        title="Unique Platform",
        description="Something completely different"
    )
    search_engine.index_entity(item)
    results = search_engine.search("nonexistentquerykeyword")
    assert results == []


def test_search_limit_parameter(search_engine):
    for i in range(25):
        search_engine.index_entity(
            SearchResultItem(
                entity_id=f"proj_{i}",
                entity_type="project",
                title=f"DevLink Project {i}",
                description="Common description keywords"
            )
        )
    results = search_engine.search("common", limit=10)
    assert len(results) == 10


def test_clear_index(search_engine):
    search_engine.index_entity(
        SearchResultItem(entity_id="p1", entity_type="project", title="Python Item", description="Desc")
    )
    assert len(search_engine.search("python")) == 1
    search_engine.clear_index()
    assert len(search_engine.search("python")) == 0
