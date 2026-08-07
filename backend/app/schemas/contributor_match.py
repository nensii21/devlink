from __future__ import annotations

import uuid
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class ContributorMatchRequest(BaseModel):
    project_id: uuid.UUID
    limit: int = 5


class MatchedContributor(BaseModel):
    user_id: uuid.UUID
    username: str
    full_name: str
    avatar: Optional[str] = None
    headline: Optional[str] = None
    match_score: float
    match_reason: str
    matching_skills: list[str]
    availability: bool


class ContributorMatchResponse(BaseModel):
    project_id: uuid.UUID
    project_title: str
    matches: list[MatchedContributor]
    generated_at: str


class SkillGapAnalysisRequest(BaseModel):
    project_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None


class SkillGapAnalysisResponse(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    match_percentage: float
    matching_skills: list[str]
    missing_skills: list[str]
    recommended_learning_topics: list[str]
    