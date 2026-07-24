import uuid

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate
from app.services.skill_service import SkillService


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def skill_input(name: str) -> SkillCreate:
    return SkillCreate(name=name, slug=f"skill-{uuid.uuid4()}")


def test_skill_variants_reuse_one_canonical_record(db):
    canonical = SkillService.create_skill(db, skill_input(" Python "))

    for variant in ("python", "PYTHON", "pYtHoN"):
        assert SkillService.create_skill(db, skill_input(variant)).id == canonical.id

    assert db.scalar(select(func.count()).select_from(Skill)) == 1
    assert canonical.name == "Python"
    assert canonical.normalized_name == "python"


def test_internal_whitespace_is_normalized_and_distinct_skills_remain(db):
    python = SkillService.create_skill(db, skill_input("Python"))
    assert SkillService.create_skill(db, skill_input("  PYTHON  ")).id == python.id

    names = ["C", "C++", "C#", "Java", "JavaScript"]
    for name in names:
        SkillService.create_skill(db, skill_input(name))

    assert db.scalar(select(func.count()).select_from(Skill)) == 6


def test_invalid_skill_names_are_rejected():
    with pytest.raises(ValueError):
        SkillCreate(name="   ", slug="empty")

    with pytest.raises(ValueError):
        SkillCreate(name=[], slug="array")


def test_update_to_case_insensitive_duplicate_is_rejected(db):
    python = SkillService.create_skill(db, skill_input("Python"))
    javascript = SkillService.create_skill(db, skill_input("JavaScript"))

    with pytest.raises(ValueError, match="already exists"):
        SkillService.update_skill(db, javascript, SkillUpdate(name=" python "))

    assert javascript.name == "JavaScript"
    assert python.id != javascript.id


def test_database_unique_constraint_rejects_duplicate_normalized_names(db):
    SkillService.create_skill(db, skill_input("Python"))
    duplicate = Skill(
        name="python",
        normalized_name="python",
        slug=f"skill-{uuid.uuid4()}",
    )
    db.add(duplicate)

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
