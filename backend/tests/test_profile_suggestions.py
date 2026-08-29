"""
Unit & Integration Tests for AI-Powered Profile Improvement Suggestions (#619)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.profile_suggestion import (
    DismissSuggestionResponse,
    ProfileSuggestionsResponse,
    RefreshSuggestionsResponse,
)
from app.services.profile_suggestion_service import ProfileSuggestionService

# ---------------------------------------------------------------------------
# Test Fixtures / Mock Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(
    username: str = "testdev",
    first_name: str = "Test",
    last_name: str = "Developer",
    bio: str | None = None,
    headline: str | None = None,
    role: str | None = None,
    experience_level: str | None = None,
    company: str | None = None,
    github_url: str | None = None,
    portfolio_url: str | None = None,
    website: str | None = None,
    open_to_work: bool | None = True,
    is_verified: bool = False,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.email = f"{username}@example.com"
    user.bio = bio
    user.headline = headline
    user.role = role
    user.experience_level = experience_level
    user.company = company
    user.github_url = github_url
    user.portfolio_url = portfolio_url
    user.website = website
    user.open_to_work = open_to_work
    user.is_verified = is_verified
    user.created_at = datetime.now(timezone.utc)
    return user


# ---------------------------------------------------------------------------
# 1. Profile Score Calculation Tests
# ---------------------------------------------------------------------------


class TestProfileScoreCalculation:
    def test_empty_profile_score(self):
        user = _make_mock_user(bio=None, headline=None, open_to_work=None)
        score = ProfileSuggestionService.calculate_profile_score(
            user, skills=[], project_count=0
        )
        assert 0 <= score <= 100
        # Basic name (10)
        assert score == 10

    def test_complete_profile_score(self):
        user = _make_mock_user(
            bio="Senior Software Engineer with 8+ years of experience building distributed systems in Python, Go, and React.",
            headline="Staff Engineer @ TechCorp",
            role="Backend Developer",
            experience_level="Senior",
            company="TechCorp",
            github_url="https://github.com/testdev",
            portfolio_url="https://testdev.io",
            is_verified=True,
            open_to_work=True,
        )
        skills = [
            {"name": s, "level": "expert", "years": 5}
            for s in ["Python", "Go", "PostgreSQL", "FastAPI", "Docker"]
        ]
        score = ProfileSuggestionService.calculate_profile_score(
            user, skills=skills, project_count=3
        )
        assert score == 100


# ---------------------------------------------------------------------------
# 2. Rule-Based Candidate Generation Tests (5 Categories)
# ---------------------------------------------------------------------------


class TestRuleBasedSuggestions:
    def test_missing_skills_category_triggered(self):
        user = _make_mock_user(role="Frontend Developer")
        suggestions = ProfileSuggestionService._generate_rule_based_suggestions(
            user, skills=[], project_count=0
        )
        categories = [s.category for s in suggestions]
        assert "missing_skills" in categories

        no_skills_sug = next(s for s in suggestions if s.id == "missing_skills_none")
        assert no_skills_sug.impact == "high"

    def test_weak_bio_category_triggered(self):
        user = _make_mock_user(bio="Short bio", headline=None)
        suggestions = ProfileSuggestionService._generate_rule_based_suggestions(
            user, skills=[], project_count=0
        )
        categories = [s.category for s in suggestions]
        assert "weak_bio" in categories

        bio_ids = [s.id for s in suggestions if s.category == "weak_bio"]
        assert "weak_bio_short" in bio_ids
        assert "weak_bio_no_headline" in bio_ids

    def test_portfolio_improvements_category_triggered(self):
        user = _make_mock_user(portfolio_url=None, website=None)
        suggestions = ProfileSuggestionService._generate_rule_based_suggestions(
            user, skills=[], project_count=0
        )
        portfolio_ids = [
            s.id for s in suggestions if s.category == "portfolio_improvements"
        ]
        assert "portfolio_no_link" in portfolio_ids
        assert "portfolio_no_projects" in portfolio_ids

    def test_github_connection_category_triggered(self):
        user = _make_mock_user(github_url=None)
        suggestions = ProfileSuggestionService._generate_rule_based_suggestions(
            user, skills=[], project_count=0
        )
        github_ids = [s.id for s in suggestions if s.category == "github_connection"]
        assert "github_not_connected" in github_ids

    def test_experience_gaps_category_triggered(self):
        user = _make_mock_user(
            experience_level=None, company=None, role=None, open_to_work=None
        )
        suggestions = ProfileSuggestionService._generate_rule_based_suggestions(
            user, skills=[], project_count=0
        )
        exp_ids = [s.id for s in suggestions if s.category == "experience_gaps"]
        assert "experience_no_level" in exp_ids
        assert "experience_no_role_company" in exp_ids
        assert "experience_no_availability" in exp_ids


# ---------------------------------------------------------------------------
# 3. Service Get & AI Integration Tests
# ---------------------------------------------------------------------------


class TestProfileSuggestionService:
    def test_get_profile_suggestions_returns_schema(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        # Mock DB queries for UserSkill, Project, and Dismissals
        db.scalars.return_value.all.side_effect = [
            [],  # user_skills
            [],  # projects
            [],  # dismissals
        ]

        response = ProfileSuggestionService.get_profile_suggestions(
            db, user, include_dismissed=False
        )

        assert isinstance(response, ProfileSuggestionsResponse)
        assert response.user_id == user.id
        assert response.total_suggestions > 0
        assert isinstance(response.profile_score, int)

    @patch("app.core.config.settings.OPENAI_API_KEY", "mock-openai-key")
    @patch("openai.OpenAI")
    def test_openai_enrichment_success(self, mock_openai_cls):
        db = MagicMock(spec=Session)
        user = _make_mock_user(bio="Fullstack engineer")

        db.scalars.return_value.all.side_effect = [[], [], []]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        {
          "suggestions": [
            {
              "id": "ai_skills_ts",
              "category": "missing_skills",
              "title": "Add TypeScript Skill",
              "description": "Adding TypeScript will boost fullstack project matches.",
              "impact": "high",
              "action_label": "Add TypeScript",
              "action_url": "/settings/skills"
            }
          ]
        }
        """
        mock_client.chat.completions.create.return_value = mock_response

        response = ProfileSuggestionService.get_profile_suggestions(db, user)

        assert response.total_suggestions == 1
        assert response.suggestions[0].title == "Add TypeScript Skill"
        assert response.suggestions[0].category == "missing_skills"


# ---------------------------------------------------------------------------
# 4. Dismissal & Refresh Logic Tests
# ---------------------------------------------------------------------------


class TestDismissAndRefresh:
    def test_dismiss_suggestion_creates_record(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None  # No existing dismissal

        user_id = uuid.uuid4()
        res = ProfileSuggestionService.dismiss_suggestion(
            db, user_id, "weak_bio_empty", "weak_bio"
        )

        assert isinstance(res, DismissSuggestionResponse)
        assert res.success is True
        assert res.suggestion_id == "weak_bio_empty"
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_dismiss_all_suggestions(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()

        db.scalars.return_value.all.side_effect = [[], [], []]
        db.scalar.return_value = None

        res = ProfileSuggestionService.dismiss_all_suggestions(db, user)
        assert res["success"] is True
        assert res["dismissed_count"] > 0

    def test_refresh_suggestions_resets_dismissals(self):
        db = MagicMock(spec=Session)
        mock_execute_res = MagicMock()
        mock_execute_res.rowcount = 4
        db.execute.return_value = mock_execute_res

        user = _make_mock_user()
        res = ProfileSuggestionService.refresh_suggestions(
            db, user, reset_dismissed=True
        )

        assert isinstance(res, RefreshSuggestionsResponse)
        assert res.success is True
        assert res.reset_dismissed_count == 4
        db.commit.assert_called_once()
