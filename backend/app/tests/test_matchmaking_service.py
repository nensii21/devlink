import pytest
from app.services.matchmaking_service import (
    MatchmakingService,
    DeveloperCandidate,
    ProjectMatchCriteria,
    ExperienceLevel
)


@pytest.fixture
def matchmaking():
    return MatchmakingService()


def test_basic_gale_shapley_stable_match(matchmaking):
    dev1 = DeveloperCandidate(user_id="d1", username="dev1", skills=["python", "react"], experience_level=ExperienceLevel.SENIOR)
    dev2 = DeveloperCandidate(user_id="d2", username="dev2", skills=["java", "spring"], experience_level=ExperienceLevel.INTERMEDIATE)
    
    proj1 = ProjectMatchCriteria(project_id="p1", title="Python Backend", required_skills=["python"], capacity=1)
    proj2 = ProjectMatchCriteria(project_id="p2", title="Java Enterprise", required_skills=["java"], capacity=1)
    
    response = matchmaking.execute_stable_match(
        developers=[dev1, dev2],
        projects=[proj1, proj2]
    )
    
    assert len(response.matches) == 2
    match_p1 = next(m for m in response.matches if m.project_id == "p1")
    match_p2 = next(m for m in response.matches if m.project_id == "p2")
    
    assert match_p1.developer_ids == ["d1"]
    assert match_p2.developer_ids == ["d2"]


def test_capacity_balancing(matchmaking):
    devs = [
        DeveloperCandidate(user_id=f"d{i}", username=f"dev{i}", skills=["python"])
        for i in range(1, 6)
    ]
    # Project needs 3 python devs
    proj = ProjectMatchCriteria(project_id="p1", title="Big Python", required_skills=["python"], capacity=3)
    
    response = matchmaking.execute_stable_match(developers=devs, projects=[proj])
    
    assert len(response.matches) == 1
    match_p1 = response.matches[0]
    # Expect 3 developers to be assigned
    assert len(match_p1.developer_ids) == 3
    # 2 developers left unmatched
    assert len(response.unmatched_developers) == 2


def test_conflict_avoidance(matchmaking):
    dev1 = DeveloperCandidate(user_id="d1", username="dev1", skills=["python"], conflicts=["p1"]) # Hates p1
    dev2 = DeveloperCandidate(user_id="d2", username="dev2", skills=["python"])
    
    proj1 = ProjectMatchCriteria(project_id="p1", title="Project 1", required_skills=["python"], capacity=2)
    
    response = matchmaking.execute_stable_match(developers=[dev1, dev2], projects=[proj1])
    
    assert len(response.matches) == 1
    match_p1 = response.matches[0]
    
    # d1 should NOT be in the match
    assert "d1" not in match_p1.developer_ids
    assert "d2" in match_p1.developer_ids
    
    # d1 remains unmatched
    assert "d1" in response.unmatched_developers


def test_asymmetric_market_unmatched_handling(matchmaking):
    dev1 = DeveloperCandidate(user_id="d1", username="dev1", skills=["c++"])
    proj1 = ProjectMatchCriteria(project_id="p1", title="Project 1", required_skills=["python"], capacity=1)
    
    # No compatibility at all, base score is 0. 
    response = matchmaking.execute_stable_match(developers=[dev1], projects=[proj1])
    
    # No matches made
    assert len(response.matches) == 0
    assert "p1" in response.unmatched_projects
    assert "d1" in response.unmatched_developers


def test_explanation_generation(matchmaking):
    dev1 = DeveloperCandidate(user_id="d1", username="dev1", skills=["go"], experience_level=ExperienceLevel.LEAD)
    proj1 = ProjectMatchCriteria(project_id="p1", title="Go Microservices", required_skills=["go"], min_experience_level=ExperienceLevel.SENIOR, capacity=1)
    
    response = matchmaking.execute_stable_match([dev1], [proj1])
    assert len(response.matches) == 1
    
    explanation = response.matches[0].explanation
    assert "Matched 1 developer(s) fulfilling capacity 1." in explanation
    assert "match_quality_metrics" in response.matches[0].__dict__
