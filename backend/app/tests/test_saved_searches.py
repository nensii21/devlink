"""
Tests for SavedSearch CRUD — service layer only (SQLite in-memory).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.saved_search import SavedSearch
from app.models.user import User
from app.schemas.saved_search import (
    ProjectSearchFilters,
    SavedSearchCreate,
    SavedSearchUpdate,
)
from app.services.saved_search_service import (
    DuplicateSavedSearchName,
    SavedSearchService,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


def _make_user(db: Session) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        username=f"user_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed",
    )
    db.add(user)
    db.flush()
    return user


def _create_payload(name: str = "My Search", **filters) -> SavedSearchCreate:
    return SavedSearchCreate(
        name=name,
        filters=ProjectSearchFilters(**filters),
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_saved_search(db):
    user = _make_user(db)
    payload = _create_payload("Backend Python", stage="idea", language="Python")

    saved = SavedSearchService.create(db, user.id, payload)

    assert saved.id is not None
    assert saved.user_id == user.id
    assert saved.name == "Backend Python"
    assert saved.filters["stage"] == "idea"
    assert saved.filters["language"] == "Python"


def test_create_strips_whitespace_from_name(db):
    user = _make_user(db)
    payload = _create_payload("  Padded Name  ")

    saved = SavedSearchService.create(db, user.id, payload)

    assert saved.name == "Padded Name"


def test_create_stores_only_set_filters(db):
    user = _make_user(db)
    payload = _create_payload("Sparse", is_remote=True)

    saved = SavedSearchService.create(db, user.id, payload)

    assert saved.filters == {"is_remote": True}
    assert "stage" not in saved.filters


def test_create_duplicate_name_raises(db):
    user = _make_user(db)
    SavedSearchService.create(db, user.id, _create_payload("Dup"))

    with pytest.raises(DuplicateSavedSearchName):
        SavedSearchService.create(db, user.id, _create_payload("Dup"))


def test_create_same_name_different_users_allowed(db):
    user_a = _make_user(db)
    user_b = _make_user(db)

    a = SavedSearchService.create(db, user_a.id, _create_payload("Shared Name"))
    b = SavedSearchService.create(db, user_b.id, _create_payload("Shared Name"))

    assert a.id != b.id


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_returns_only_current_users_searches(db):
    owner = _make_user(db)
    other = _make_user(db)

    SavedSearchService.create(db, owner.id, _create_payload("Owner Search 1"))
    SavedSearchService.create(db, owner.id, _create_payload("Owner Search 2"))
    SavedSearchService.create(db, other.id, _create_payload("Other Search"))

    results = SavedSearchService.list(db, owner.id)

    assert len(results) == 2
    names = {r.name for r in results}
    assert "Owner Search 1" in names
    assert "Owner Search 2" in names
    assert "Other Search" not in names


def test_list_returns_empty_for_new_user(db):
    user = _make_user(db)
    assert SavedSearchService.list(db, user.id) == []


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


def test_get_returns_own_search(db):
    user = _make_user(db)
    created = SavedSearchService.create(db, user.id, _create_payload("Get Me"))

    fetched = SavedSearchService.get(db, created.id, user.id)

    assert fetched is not None
    assert fetched.id == created.id


def test_get_returns_none_for_another_users_search(db):
    owner = _make_user(db)
    attacker = _make_user(db)
    created = SavedSearchService.create(db, owner.id, _create_payload("Private"))

    result = SavedSearchService.get(db, created.id, attacker.id)

    assert result is None


def test_get_returns_none_for_nonexistent_id(db):
    user = _make_user(db)
    result = SavedSearchService.get(db, uuid.uuid4(), user.id)
    assert result is None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_name(db):
    user = _make_user(db)
    saved = SavedSearchService.create(db, user.id, _create_payload("Old Name"))

    updated = SavedSearchService.update(db, saved, SavedSearchUpdate(name="New Name"))

    assert updated.name == "New Name"


def test_update_filters(db):
    user = _make_user(db)
    saved = SavedSearchService.create(
        db, user.id, _create_payload("Filter Update", stage="idea")
    )

    updated = SavedSearchService.update(
        db,
        saved,
        SavedSearchUpdate(filters=ProjectSearchFilters(stage="beta", is_remote=True)),
    )

    assert updated.filters["stage"] == "beta"
    assert updated.filters["is_remote"] is True


def test_update_name_strips_whitespace(db):
    user = _make_user(db)
    saved = SavedSearchService.create(db, user.id, _create_payload("Trim Me"))

    updated = SavedSearchService.update(
        db, saved, SavedSearchUpdate(name="  Trimmed  ")
    )

    assert updated.name == "Trimmed"


def test_update_to_duplicate_name_raises(db):
    user = _make_user(db)
    SavedSearchService.create(db, user.id, _create_payload("Existing"))
    target = SavedSearchService.create(db, user.id, _create_payload("Target"))

    with pytest.raises(DuplicateSavedSearchName):
        SavedSearchService.update(db, target, SavedSearchUpdate(name="Existing"))


def test_update_to_same_name_is_idempotent(db):
    user = _make_user(db)
    saved = SavedSearchService.create(db, user.id, _create_payload("Same"))

    updated = SavedSearchService.update(db, saved, SavedSearchUpdate(name="Same"))

    assert updated.name == "Same"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_removes_search(db):
    user = _make_user(db)
    saved = SavedSearchService.create(db, user.id, _create_payload("Delete Me"))

    SavedSearchService.delete(db, saved)

    assert SavedSearchService.get(db, saved.id, user.id) is None


def test_delete_does_not_affect_other_searches(db):
    user = _make_user(db)
    keep = SavedSearchService.create(db, user.id, _create_payload("Keep"))
    remove = SavedSearchService.create(db, user.id, _create_payload("Remove"))

    SavedSearchService.delete(db, remove)

    assert SavedSearchService.get(db, keep.id, user.id) is not None
    assert SavedSearchService.get(db, remove.id, user.id) is None


# ---------------------------------------------------------------------------
# name_exists
# ---------------------------------------------------------------------------


def test_name_exists_true(db):
    user = _make_user(db)
    SavedSearchService.create(db, user.id, _create_payload("Exists"))
    assert SavedSearchService.name_exists(db, user.id, "Exists") is True


def test_name_exists_false(db):
    user = _make_user(db)
    assert SavedSearchService.name_exists(db, user.id, "Ghost") is False


def test_name_exists_strips_whitespace(db):
    user = _make_user(db)
    SavedSearchService.create(db, user.id, _create_payload("Spaced"))
    assert SavedSearchService.name_exists(db, user.id, "  Spaced  ") is True
