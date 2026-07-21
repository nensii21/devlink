import uuid
import pytest
from app.services.recommendation_service import (
    WeightedProjectScoringStrategy,
    ProjectCandidate,
    ProjectScoringContext,
)
from app.models.project import Project
from app.schemas.recommendation import RecommendationWeights

def test_project_scoring_strategy():
    weights = RecommendationWeights(
        skills=0.30,
        interests=0.10,
        experience=0.15,
        technologies=0.20,
        availability=0.10,
        contributions=0.10,
        network=0.05,
    )
    strategy = WeightedProjectScoringStrategy(weights)
    
    skill_id = uuid.uuid4()
    
    project = Project(
        id=uuid.uuid4(),
        title="Test Project",
        description="A great project",
        tech_stack="python, react",
    )
    
    candidate = ProjectCandidate(
        project=project,
        required_skill_ids={skill_id},
        minimum_experience=2,
        context_tokens={"test", "project", "great"},
        tech_stack="python, react",
        is_collaborator=True,
    )
    
    context = ProjectScoringContext(
        builder_skill_ids={skill_id},
        builder_skill_levels={skill_id: 3}, # ADVANCED
        builder_skill_names={"python"},
        interest_tokens={"test", "python"},
        years_of_experience=3,
        experience_level_rank=3,
    )
    
    final_score, breakdown, matched_skills, matched_techs = strategy.score(candidate, context)
    
    assert final_score > 0
    assert breakdown.skills > 0
    assert breakdown.network == 0.05
    assert breakdown.experience == 0.15
