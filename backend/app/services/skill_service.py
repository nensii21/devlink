from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate
from app.core.cache import cached
from app.utils.skill_names import clean_skill_name, normalize_skill_name


class SkillService:
    """
    Business logic for Skill operations.
    """

    @staticmethod
    def create_skill(
        db: Session,
        skill: SkillCreate,
    ) -> Skill:
        display_name = clean_skill_name(skill.name)
        normalized_name = normalize_skill_name(display_name)
        existing = SkillService.get_by_name(db, display_name)
        if existing is not None:
            return existing

        db_skill = Skill(
            name=display_name,
            normalized_name=normalized_name,
            slug=skill.slug,
            category=skill.category,
            description=skill.description,
            icon=skill.icon,
        )

        db.add(db_skill)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            # The unique normalized-name index closes the check-then-insert
            # race. Re-read the winner and return it to the caller.
            existing = SkillService.get_by_normalized_name(db, normalized_name)
            if existing is not None:
                return existing
            raise ValueError("Skill could not be created")
        db.refresh(db_skill)

        return db_skill

    @staticmethod
    def get_skill(
        db: Session,
        skill_id: uuid.UUID,
    ) -> Skill | None:
        return db.get(Skill, skill_id)

    @staticmethod
    @cached(ttl=86400, key_prefix="skill")
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Skill | None:
        stmt = select(Skill).where(Skill.slug == slug)
        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=86400, key_prefix="skill")
    def get_by_name(
        db: Session,
        name: str,
    ) -> Skill | None:
        stmt = select(Skill).where(Skill.normalized_name == normalize_skill_name(name))
        return db.scalar(stmt)

    @staticmethod
    def get_by_normalized_name(
        db: Session,
        normalized_name: str,
    ) -> Skill | None:
        stmt = select(Skill).where(Skill.normalized_name == normalized_name)
        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=86400, key_prefix="skill")
    def list_skills(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Skill]:
        stmt = select(Skill).order_by(Skill.name).offset(skip).limit(limit)

        return list(db.scalars(stmt))

    @staticmethod
    def search_skills(
        db: Session,
        keyword: str,
    ) -> list[Skill]:
        keyword = " ".join(keyword.strip().split())
        stmt = (
            select(Skill).where(Skill.name.ilike(f"%{keyword}%")).order_by(Skill.name)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_skill(
        db: Session,
        db_skill: Skill,
        skill: SkillUpdate,
    ) -> Skill:
        data = skill.model_dump(exclude_unset=True)

        if "name" in data:
            normalized_name = normalize_skill_name(data["name"])
            duplicate = SkillService.get_by_normalized_name(db, normalized_name)
            if duplicate is not None and duplicate.id != db_skill.id:
                raise ValueError("Skill already exists")
            data["name"] = clean_skill_name(data["name"])
            data["normalized_name"] = normalized_name

        for key, value in data.items():
            setattr(db_skill, key, value)

        try:
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Skill already exists") from exc
        db.refresh(db_skill)

        return db_skill

    @staticmethod
    def delete_skill(
        db: Session,
        db_skill: Skill,
    ) -> None:
        db.delete(db_skill)
        db.flush()
