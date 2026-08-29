"""
Comprehensive Unit tests for the Intelligent Matchmaking & Recommendation Engine.
"""

import pytest
from app.services.matchmaking_service import (
    MatchmakingService,
    DeveloperCandidate,
    ProjectMatchCriteria,
    ExperienceLevel,
    matchmaking_service
)


@pytest.fixture
def service():
    return MatchmakingService()


def test_calculate_skill_overlap_full(service):
    candidate_skills = ["python", "fastapi", "react", "docker"]
    required_skills = ["python", "react"]
    res = service.calculate_skill_overlap(candidate_skills, required_skills)
    assert res["score"] == 1.0
    assert set(res["matched"]) == {"python", "react"}
    assert res["missing"] == []


def test_calculate_skill_overlap_partial(service):
    candidate_skills = ["python", "typescript"]
    required_skills = ["python", "react", "docker", "fastapi"]
    res = service.calculate_skill_overlap(candidate_skills, required_skills)
    assert res["score"] == 0.25
    assert res["matched"] == ["python"]
    assert set(res["missing"]) == {"react", "docker", "fastapi"}


def test_calculate_skill_overlap_empty_requirements(service):
    candidate_skills = ["python"]
    required_skills = []
    res = service.calculate_skill_overlap(candidate_skills, required_skills)
    assert res["score"] == 1.0
    assert res["matched"] == []
    assert res["missing"] == []


def test_calculate_skill_overlap_case_insensitivity(service):
    candidate_skills = ["Python", "FASTAPI", "Docker"]
    required_skills = ["python", "fastapi"]
    res = service.calculate_skill_overlap(candidate_skills, required_skills)
    assert res["score"] == 1.0
    assert set(res["matched"]) == {"python", "fastapi"}


def test_timezone_proximity_identical(service):
    score = service.calculate_timezone_proximity(5, 5)
    assert score == 1.0


def test_timezone_proximity_opposite(service):
    score = service.calculate_timezone_proximity(-6, 6)
    assert score == 0.75


def test_timezone_proximity_none_handling(service):
    score = service.calculate_timezone_proximity(None, 5)
    assert score == 1.0
    score = service.calculate_timezone_proximity(5, None)
    assert score == 1.0


def test_experience_compatibility_met(service):
    score = service.calculate_experience_compatibility(
        ExperienceLevel.SENIOR, ExperienceLevel.INTERMEDIATE
    )
    assert score == 1.0


def test_experience_compatibility_under(service):
    score = service.calculate_experience_compatibility(
        ExperienceLevel.BEGINNER, ExperienceLevel.SENIOR
    )
    assert score < 1.0
    assert score > 0.0


def test_rank_candidates_ordering_and_fields(service):
    criteria = ProjectMatchCriteria(
        project_id="proj_1",
        title="Open Source Platform",
        required_skills=["python", "fastapi", "postgresql"],
        preferred_timezone_offset=0,
        min_experience_level=ExperienceLevel.INTERMEDIATE,
        min_hours_per_week=10
    )
    c1 = DeveloperCandidate(
        user_id="u1", username="alice", skills=["python", "fastapi", "postgresql"],
        experience_level=ExperienceLevel.SENIOR, timezone_offset=0, availability_hours_per_week=15
    )
    c2 = DeveloperCandidate(
        user_id="u2", username="bob", skills=["python"],
        experience_level=ExperienceLevel.BEGINNER, timezone_offset=10, availability_hours_per_week=5
    )
    c3 = DeveloperCandidate(
        user_id="u3", username="charlie", skills=["python", "fastapi"],
        experience_level=ExperienceLevel.INTERMEDIATE, timezone_offset=0, availability_hours_per_week=20
    )

    ranked = service.rank_candidates(criteria, [c1, c2, c3])
    assert len(ranked) == 3
    assert ranked[0].username == "alice"
    assert ranked[1].username == "charlie"
    assert ranked[2].username == "bob"
    assert ranked[0].match_score > ranked[1].match_score > ranked[2].match_score
    assert "postgresql" in ranked[0].matched_skills
    assert "postgresql" in ranked[1].missing_skills
