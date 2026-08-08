"""
Unit & Integration Tests for Project Templates Marketplace (#596)
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_template import ProjectTemplate, ProjectTemplateFavorite
from app.models.user import User
from app.schemas.project_template import (
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
)
from app.services.project_template_service import ProjectTemplateService


def _make_mock_user() -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.username = "templateauthor"
    u.avatar = "https://example.com/avatar.png"
    return u


def _make_mock_template(author_id: uuid.UUID, title: str = "FastAPI React Boilerplate") -> MagicMock:
    t = MagicMock(spec=ProjectTemplate)
    t.id = uuid.uuid4()
    t.title = title
    t.slug = f"fastapi-react-boilerplate-{uuid.uuid4().hex[:6]}"
    t.description = "A production-ready fullstack template with Auth and Tailwind."
    t.category = "web-app"
    t.tech_stack = ["FastAPI", "React", "PostgreSQL"]
    t.features = ["JWT Auth", "Docker Compose"]
    t.repository_url = "https://github.com/example/boilerplate"
    t.demo_url = "https://demo.example.com"
    t.author_id = author_id
    t.is_featured = False
    t.is_published = True
    t.clones_count = 10
    t.stars_count = 5
    t.created_at = None
    t.updated_at = None
    return t


class TestProjectTemplatesMarketplace:
    def test_create_template_generates_slug_and_stores_record(self):
        db = MagicMock(spec=Session)
        author = _make_mock_user()

        payload = ProjectTemplateCreate(
            title="Next.js SaaS Starter",
            description="Complete starter with Stripe & Prisma.",
            category="web-app",
            tech_stack=["Next.js", "Stripe", "Prisma"],
            features=["Subscription Billing", "Auth"],
        )

        template = ProjectTemplateService.create_template(
            db=db,
            author_id=author.id,
            payload=payload,
        )

        assert template.title == "Next.js SaaS Starter"
        assert "nextjs-saas-starter" in template.slug
        assert template.author_id == author.id
        assert db.add.called
        assert db.commit.called

    def test_toggle_favorite_adds_and_removes(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        template = _make_mock_template(author_id=user.id)
        template.stars_count = 5

        # First call: no existing favorite -> Add favorite
        db.scalar.side_effect = [template, None]

        is_fav, stars = ProjectTemplateService.toggle_favorite(
            db=db,
            template_id=template.id,
            user_id=user.id,
        )

        assert is_fav is True
        assert stars == 6
        assert db.add.called

        # Second call: existing favorite -> Remove favorite
        db.scalar.side_effect = [template, MagicMock(spec=ProjectTemplateFavorite)]

        is_fav_2, stars_2 = ProjectTemplateService.toggle_favorite(
            db=db,
            template_id=template.id,
            user_id=user.id,
        )

        assert is_fav_2 is False
        assert stars_2 == 5
        assert db.delete.called

    def test_clone_template_creates_new_project_and_increments_count(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        template = _make_mock_template(author_id=user.id)
        template.clones_count = 10

        db.scalar.return_value = template

        cloned_project = ProjectTemplateService.clone_template(
            db=db,
            template_id=template.id,
            user_id=user.id,
            new_project_title="My Custom App",
        )

        assert template.clones_count == 11
        assert cloned_project.title == "My Custom App"
        assert cloned_project.owner_id == user.id
        assert cloned_project.tech_stack == "FastAPI, React, PostgreSQL"
        assert db.add.called
        assert db.commit.called

    def test_update_template_checks_author(self):
        db = MagicMock(spec=Session)
        author = _make_mock_user()
        other_user = _make_mock_user()
        template = _make_mock_template(author_id=author.id)

        db.scalar.return_value = template

        payload = ProjectTemplateUpdate(title="Updated Title")

        # Other user cannot update author's template
        res_unauthorized = ProjectTemplateService.update_template(
            db=db,
            template_id=template.id,
            user_id=other_user.id,
            payload=payload,
        )
        assert res_unauthorized is None

        # Author can update
        res_author = ProjectTemplateService.update_template(
            db=db,
            template_id=template.id,
            user_id=author.id,
            payload=payload,
        )
        assert res_author is not None
        assert template.title == "Updated Title"
