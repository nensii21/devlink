"""
Unit tests for the recommendation scoring engine.

These tests intentionally avoid the database — they exercise the pure
scoring helpers directly, which is where the "matching logic" lives.
"""
from __future__ import annotations

import uuid

from app.models.user_skill import SkillLevel
from app.schemas.recommendation import RecommendationWeights
from app.services.recommendation_service import (
    BuilderCandidate,
    ScoringContext,
    WeightedScoringStrategy,
    _availability_score,
    _contributions_score,
    _experience_score,
    _interests_score,
    _skills_score,
    _technologies_score,
    _tokenize,
)


# ---------- pure helpers ----------

def test_tokenize_strips_stopwords_and_punctuation():
    tokens = _tokenize("Building a React, Node and Postgres app for developers!")
    assert "react" in tokens
    assert "node" in tokens
    assert "postgres" in tokens
    assert "building" not in tokens  # stopword
    assert "developers" not in tokens  # stopword
    assert "a" not in tokens  # too short


def test_skills_score_weighted_by_level():
    req = {uuid.uuid4(), uuid.uuid4()}
    levels = {
        next(iter(req)): SkillLevel.EXPERT,        # matches with weight 1.0
    }
    score, matched = _skills_score(req, levels, req)
    assert 0.0 < score <= 1.0
    assert len(matched) == 1


def test_skills_score_zero_when_no_overlap():
    req = {uuid.uuid4()}
    builder = {uuid.uuid4()}
    score, _ = _skills_score(builder, {}, req)
    assert score == 0.0


def test_interests_score_jaccard():
    a = {"react", "node", "postgres"}
    b = {"react", "node", "redis"}
    # intersection 2, union 4 → 0.5
    assert _interests_score(a, b) == 0.5


def test_interests_score_zero_on_empty():
    assert _interests_score(set(), {"a"}) == 0.0
    assert _interests_score({"a"}, set()) == 0.0


def test_experience_score_meets_requirement():
    assert _experience_score(5, 3, 3) == 1.0


def test_experience_score_proportional():
    assert _experience_score(1, 1, 4) == 0.25


def test_experience_score_no_requirement():
    assert _experience_score(0, 0, 0) == 1.0


def test_technologies_score_overlap():
    names = {"react", "node", "postgres"}
    stack = "React, Redis, Docker"
    score, matched = _technologies_score(names, stack)
    assert "react" in matched
    assert 0.0 < score <= 1.0


def test_availability_score():
    assert _availability_score(True) == 1.0
    assert _availability_score(False) == 0.3


def test_contributions_score_log_scale():
    assert _contributions_score(0) == 0.0
    assert _contributions_score(1) > 0.0
    assert _contributions_score(10) > _contributions_score(1)
    assert _contributions_score(100) < 1.0


# ---------- full strategy ----------

def test_weighted_strategy_returns_score_in_unit_interval():
    sid = uuid.uuid4()
    from app.models.user import User

    class _FakeUser:
        open_to_work = True

    candidate = BuilderCandidate(
        user=_FakeUser(),  # type: ignore[arg-type]
        skill_ids={sid},
        skill_levels={sid: SkillLevel.EXPERT},
        skill_names={"react"},
        interest_tokens={"react", "node"},
        years_of_experience=5,
        experience_level_rank=3,
        contribution_count=3,
        is_mutual_follower=True,
    )
    ctx = ScoringContext(
        required_skill_ids={sid},
        context_tokens={"react", "node", "postgres"},
        tech_stack="React, Postgres",
        minimum_experience=3,
    )
    strategy = WeightedScoringStrategy(RecommendationWeights())
    final, breakdown, matched_skills, matched_techs = strategy.score(candidate, ctx)
    assert 0.0 <= final <= 1.0
    assert breakdown.skills > 0.0
    assert breakdown.technologies > 0.0
    assert breakdown.experience == 0.15  # full credit * weight
    assert "react" in matched_techs
