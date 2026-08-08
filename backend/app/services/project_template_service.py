from __future__ import annotations

import re
import uuid
from typing import Optional

from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_template import ProjectTemplate, ProjectTemplateFavorite
from app.schemas.project_template import (
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
    ProjectTemplateResponse,
)


def _generate_slug(title: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", title).strip().lower()
    slug_base = re.sub(r"[\s-]+", "-", cleaned)
    short_hash = uuid.uuid4().hex[:6]
    return f"{slug_base}-{short_hash}" if slug_base else f"template-{short_hash}"


class ProjectTemplateService:
    @staticmethod
    def create_template(
        db: Session,
        author_id: uuid.UUID,
        payload: ProjectTemplateCreate,
    ) -> ProjectTemplate:
        slug = _generate_slug(payload.title)

        template = ProjectTemplate(
            title=payload.title,
            slug=slug,
            description=payload.description,
            category=payload.category,
            tech_stack=payload.tech_stack,
            features=payload.features,
            repository_url=payload.repository_url,
            demo_url=payload.demo_url,
            author_id=author_id,
            is_published=True,
        )

        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_template_by_id(
        db: Session,
        template_id: uuid.UUID,
    ) -> ProjectTemplate | None:
        stmt = select(ProjectTemplate).where(ProjectTemplate.id == template_id)
        return db.scalar(stmt)

    @staticmethod
    def get_template_detail(
        db: Session,
        template_id: uuid.UUID,
        current_user_id: Optional[uuid.UUID] = None,
    ) -> ProjectTemplateResponse | None:
        template = ProjectTemplateService.get_template_by_id(db, template_id)
        if not template:
            return None

        is_favorited = False
        if current_user_id:
            fav_stmt = select(ProjectTemplateFavorite).where(
                ProjectTemplateFavorite.template_id == template_id,
                ProjectTemplateFavorite.user_id == current_user_id,
            )
            is_favorited = db.scalar(fav_stmt) is not None

        res = ProjectTemplateResponse.model_validate(template)
        res.is_favorited = is_favorited
        return res

    @staticmethod
    def list_templates(
        db: Session,
        search: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        sort_by: str = "popular",
        current_user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[ProjectTemplateResponse], int]:
        stmt = select(ProjectTemplate).where(ProjectTemplate.is_published == True)  # noqa: E712

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    ProjectTemplate.title.ilike(search_pattern),
                    ProjectTemplate.description.ilike(search_pattern),
                )
            )

        if category and category.lower() != "all":
            stmt = stmt.where(ProjectTemplate.category == category.lower())

        if sort_by == "recent":
            stmt = stmt.order_by(desc(ProjectTemplate.created_at))
        elif sort_by == "clones":
            stmt = stmt.order_by(desc(ProjectTemplate.clones_count), desc(ProjectTemplate.created_at))
        else:  # "popular" (default)
            stmt = stmt.order_by(
                desc(ProjectTemplate.is_featured),
                desc(ProjectTemplate.stars_count),
                desc(ProjectTemplate.clones_count),
                desc(ProjectTemplate.created_at),
            )

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(total_stmt) or 0

        templates = list(db.scalars(stmt.offset(skip).limit(limit)))

        # Get list of favorited template IDs for current user
        favorited_ids: set[uuid.UUID] = set()
        if current_user_id and templates:
            t_ids = [t.id for t in templates]
            fav_stmt = select(ProjectTemplateFavorite.template_id).where(
                ProjectTemplateFavorite.user_id == current_user_id,
                ProjectTemplateFavorite.template_id.in_(t_ids),
            )
            favorited_ids = set(db.scalars(fav_stmt))

        items: list[ProjectTemplateResponse] = []
        for t in templates:
            item = ProjectTemplateResponse.model_validate(t)
            item.is_favorited = t.id in favorited_ids
            items.append(item)

        return items, total

    @staticmethod
    def update_template(
        db: Session,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: ProjectTemplateUpdate,
    ) -> ProjectTemplate | None:
        template = ProjectTemplateService.get_template_by_id(db, template_id)
        if not template or template.author_id != user_id:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)

        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(
        db: Session,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        template = ProjectTemplateService.get_template_by_id(db, template_id)
        if not template or template.author_id != user_id:
            return False

        db.delete(template)
        db.commit()
        return True

    @staticmethod
    def toggle_favorite(
        db: Session,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[bool, int]:
        """
        Toggles favorite status for a template. Returns (is_favorited, new_stars_count).
        """
        template = ProjectTemplateService.get_template_by_id(db, template_id)
        if not template:
            raise ValueError("Template not found")

        stmt = select(ProjectTemplateFavorite).where(
            ProjectTemplateFavorite.template_id == template_id,
            ProjectTemplateFavorite.user_id == user_id,
        )
        existing = db.scalar(stmt)

        if existing:
            db.delete(existing)
            template.stars_count = max(0, template.stars_count - 1)
            is_favorited = False
        else:
            fav = ProjectTemplateFavorite(template_id=template_id, user_id=user_id)
            db.add(fav)
            template.stars_count += 1
            is_favorited = True

        db.commit()
        db.refresh(template)
        return is_favorited, template.stars_count

    @staticmethod
    def clone_template(
        db: Session,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        new_project_title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        template = ProjectTemplateService.get_template_by_id(db, template_id)
        if not template:
            raise ValueError("Template not found")

        # Increment clone count
        template.clones_count += 1

        title = new_project_title.strip() if new_project_title else f"{template.title} (Cloned)"
        proj_desc = description.strip() if description else f"Cloned from template '{template.title}'. {template.description}"

        # Create new Project based on template
        project = Project(
            title=title,
            slug=_generate_slug(title),
            description=proj_desc,
            tagline=f"Cloned from template: {template.title}",
            owner_id=user_id,
            tech_stack=", ".join(template.tech_stack) if isinstance(template.tech_stack, list) else str(template.tech_stack or ""),
        )

        db.add(project)
        db.commit()
        db.refresh(project)
        return project
