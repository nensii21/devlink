from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class ConversationStarterRequest(BaseModel):
    """Request to generate conversation starters."""
    target_user_id: uuid.UUID = Field(..., description="ID of the user to generate starters for")


class ConversationStarterResponse(BaseModel):
    """Response containing conversation starter suggestions."""
    suggestions: list[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3-5 context-aware conversation starter suggestions",
    )
    target_user_id: uuid.UUID
    target_user_name: str
