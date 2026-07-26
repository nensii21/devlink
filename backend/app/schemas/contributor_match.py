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
