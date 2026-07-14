from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate


class SkillService:
    """
    Business logic for Skill operations.
    """

    @staticmethod
    def create_skill(
        db: Session,
        skill: SkillCreate,
    ) -> Skill:

        db_skill = Skill(
            name=skill.name,
            slug=skill.slug,
            category=skill.category,
            description=skill.description,
            icon=skill.icon,
        )

        db.add(db_skill)
        db.flush()
        db.refresh(db_skill)

        return db_skill

    @staticmethod
    def get_skill(
        db: Session,
        skill_id: uuid.UUID,
    ) -> Skill | None:

        return db.get(Skill, skill_id)

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Skill | None:

        stmt = select(Skill).where(Skill.slug == slug)
        return db.scalar(stmt)

    @staticmethod
    def get_by_name(
        db: Session,
        name: str,
    ) -> Skill | None:

        stmt = select(Skill).where(Skill.name == name)
        return db.scalar(stmt)

    @staticmethod
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

        for key, value in data.items():
            setattr(db_skill, key, value)

        db.flush()
        db.refresh(db_skill)

        return db_skill

    @staticmethod
    def delete_skill(
        db: Session,
        db_skill: Skill,
    ) -> None:

        db.delete(db_skill)
        db.flush()
