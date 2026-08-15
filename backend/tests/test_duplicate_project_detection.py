"""
Unit & Integration Tests for AI-Based Duplicate Project Detection (#608)
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.duplicate_detection import (
    DuplicateProjectCheckResponse,
)
from app.schemas.project import ProjectCreate
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.project_service import ProjectService


def _make_mock_project(
    title: str = "DevLink Open Source Platform",
    description: str = "A collaborative platform for developers to connect, build projects, and find teammates.",
    tech_stack: str = "python, fastapi, react, postgresql",
) -> MagicMock:
    p = MagicMock(spec=Project)
    p.id = uuid.uuid4()
    p.title = title
    p.slug = "devlink-open-source-platform"
    p.description = description
    p.tech_stack = tech_stack
    p.embedding = None
    return p


# ---------------------------------------------------------------------------
# 1. Similarity Metric Unit Tests
# ---------------------------------------------------------------------------


class TestSimilarityMetrics:
    def test_levenshtein_similarity_exact_and_case(self):
        assert (
            DuplicateDetectionService._levenshtein_similarity(
                "DevLink App", "devlink app"
            )
            == 1.0
        )
        assert (
            DuplicateDetectionService._levenshtein_similarity(
                "DevLink App", "DevLink Application"
            )
            > 0.5
        )
        assert DuplicateDetectionService._levenshtein_similarity("Alpha", "Beta") < 0.3

    def test_keyword_similarity(self):
        score = DuplicateDetectionService.keyword_similarity(
            "AI Code Assistant for Developers",
            "An AI powered code assistant to help software developers write better code",
        )
        assert score > 0.5


# ---------------------------------------------------------------------------
# 2. Duplicate Project Detection Logic Tests
# ---------------------------------------------------------------------------


class TestDuplicateProjectDetection:
    def test_find_duplicate_projects_detects_similar(self):
        db = MagicMock(spec=Session)
        existing_p = _make_mock_project(
            title="Realtime Chat Application for Teams",
            description="A real-time messaging application built with WebSockets and React.",
            tech_stack="react, websockets, nodejs",
        )
        db.scalars.return_value.all.return_value = [existing_p]

        res = DuplicateDetectionService.find_duplicate_projects(
            db,
            title="Realtime Chat App for Teams",
            description="Real-time messaging web app using WebSockets and React frontend.",
            tags=["react", "websockets"],
            threshold=0.50,
        )

        assert isinstance(res, DuplicateProjectCheckResponse)
        assert res.has_duplicates is True
        assert res.max_similarity_score > 0.50
        assert len(res.suggested_projects) == 1
        assert res.suggested_projects[0].project_id == existing_p.id
        assert (
            "Nearly identical project title"
            in res.suggested_projects[0].match_reasons[0]
            or "High title" in res.suggested_projects[0].match_reasons[0]
        )

    def test_find_duplicate_projects_filters_below_threshold(self):
        db = MagicMock(spec=Session)
        existing_p = _make_mock_project(
            title="Machine Learning Classifier",
            description="Trains PyTorch models for computer vision.",
        )
        db.scalars.return_value.all.return_value = [existing_p]

        res = DuplicateDetectionService.find_duplicate_projects(
            db,
            title="Crypto Wallet Extension",
            description="Solana browser extension wallet.",
            threshold=0.75,
        )

        assert res.has_duplicates is False
        assert len(res.suggested_projects) == 0


# ---------------------------------------------------------------------------
# 3. Project Creation & Manual Override Tests
# ---------------------------------------------------------------------------


class TestProjectCreationDuplicateGuard:
    def test_create_project_blocked_on_duplicate_without_override(self):
        db = MagicMock(spec=Session)
        owner_id = uuid.uuid4()
        existing_p = _make_mock_project(
            title="DevLink Developer Platform",
            description="Collaborative network for open source builders.",
        )

        dup_response = DuplicateProjectCheckResponse(
            has_duplicates=True,
            max_similarity_score=0.92,
            suggested_projects=[
                {
                    "project_id": existing_p.id,
                    "title": existing_p.title,
                    "slug": existing_p.slug,
                    "description": existing_p.description,
                    "similarity_score": 0.92,
                    "confidence_score": 92.0,
                    "is_duplicate": True,
                    "match_reasons": ["Nearly identical title"],
                }
            ],
            threshold_used=0.80,
            manual_override_allowed=True,
        )

        with patch.object(
            DuplicateDetectionService,
            "find_duplicate_projects",
            return_value=dup_response,
        ):
            project_in = ProjectCreate(
                title="DevLink Developer Platform",
                description="Collaborative network for open source builders.",
                allow_duplicate=False,
            )

            with pytest.raises(HTTPException) as exc_info:
                ProjectService.create_project(db, owner_id, project_in)

            assert exc_info.value.status_code == 409
            assert (
                "Potential duplicate project detected"
                in exc_info.value.detail["message"]
            )

    def test_create_project_allowed_with_manual_override(self):
        db = MagicMock(spec=Session)
        owner_id = uuid.uuid4()

        project_in = ProjectCreate(
            title="DevLink Developer Platform Duplicate",
            description="Collaborative network for open source builders.",
            allow_duplicate=True,  # Manual override enabled!
        )

        db.add = MagicMock()
        db.flush = MagicMock()
        db.refresh = MagicMock()

        # Should not raise exception
        project = ProjectService.create_project(db, owner_id, project_in)
        assert project.title == project_in.title
        assert db.add.called
