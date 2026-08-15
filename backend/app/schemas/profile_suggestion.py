from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProfileSuggestionItem(BaseModel):
    id: str = Field(description="Unique identifier for the suggestion")
    category: str = Field(
        description=(
            "Category: missing_skills, weak_bio, portfolio_improvements, "
            "github_connection, experience_gaps"
        )
    )
    title: str
    description: str
    impact: str = Field(description="Impact level: high, medium, low")
    action_label: Optional[str] = None
    action_url: Optional[str] = None
    is_dismissed: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProfileSuggestionsResponse(BaseModel):
    user_id: uuid.UUID
    profile_score: int = Field(
        description="Calculated profile completeness score (0-100)"
    )
    total_suggestions: int
    active_suggestions_count: int
    dismissed_suggestions_count: int
    suggestions: list[ProfileSuggestionItem]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DismissSuggestionResponse(BaseModel):
    success: bool = True
    message: str
    suggestion_id: str
    user_id: uuid.UUID


class RefreshSuggestionsResponse(BaseModel):
    success: bool = True
    message: str
    user_id: uuid.UUID
    reset_dismissed_count: int
