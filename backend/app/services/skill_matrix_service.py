from __future__ import annotations

import uuid
from typing import Dict, List, Any
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, joinedload

from app.models.user_skill import UserSkill, SkillLevel
from app.models.skill import Skill
from app.utils.skill_names import clean_skill_name, normalize_skill_name
from app.services.skill_service import SkillService
from app.schemas.skill import SkillCreate

MATRIX_CATEGORIES = [
    "Languages",
    "Frameworks",
    "Databases",
    "Cloud",
    "DevOps",
    "AI/ML",
    "Design",
]

class SkillMatrixService:
    """
    Service to manage visual Developer Skill Matrix and backend persistence.
    """

    @staticmethod
    def get_user_skill_matrix(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        stmt = (
            select(UserSkill)
            .options(joinedload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills = list(db.scalars(stmt))

        categorized: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in MATRIX_CATEGORIES}
        categorized["Other"] = []

        total_skills = 0
        for us in user_skills:
            if not us.skill:
                continue
            cat = us.skill.category if us.skill.category in MATRIX_CATEGORIES else "Other"
            if cat not in categorized:
                categorized[cat] = []
            
            level_val = us.level.value if isinstance(us.level, SkillLevel) else str(us.level)
            categorized[cat].append({
                "id": str(us.id),
                "skill_id": str(us.skill_id),
                "name": us.skill.name,
                "category": us.skill.category or "Languages",
                "level": level_val.capitalize(),
                "years_of_experience": us.years_of_experience,
            })
            total_skills += 1

        return {
            "skills_by_category": categorized,
            "total_skills": total_skills,
        }

    @staticmethod
    def update_user_skill_matrix(
        db: Session, user_id: uuid.UUID, skills_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # Clear existing skills for user
        db.execute(delete(UserSkill).where(UserSkill.user_id == user_id))
        db.flush()

        for item in skills_data:
            skill_name = item.get("name", "").strip()
            if not skill_name:
                continue
            category = item.get("category", "Languages")
            raw_level = item.get("level", "beginner").lower()
            try:
                level_enum = SkillLevel(raw_level)
            except ValueError:
                level_enum = SkillLevel.BEGINNER
            years = int(item.get("years_of_experience", 0))

            cleaned = clean_skill_name(skill_name)
            skill_obj = SkillService.get_by_name(db, cleaned)
            if not skill_obj:
                slug = normalize_skill_name(cleaned)
                skill_obj = SkillService.create_skill(
                    db,
                    SkillCreate(
                        name=cleaned,
                        slug=slug,
                        category=category,
                    ),
                )
            else:
                if category and skill_obj.category != category:
                    skill_obj.category = category
                    db.flush()

            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill_obj.id,
                level=level_enum,
                years_of_experience=years,
            )
            db.add(user_skill)

        db.flush()
        return SkillMatrixService.get_user_skill_matrix(db, user_id)
