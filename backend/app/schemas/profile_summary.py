from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class ProfileSummaryRequest(BaseModel):
    """Request to generate a profile summary."""
    user_id: uuid.UUID = Field(..., description="ID of the user to generate summary for")


class ProfileSummaryResponse(BaseModel):
    """Response containing the generated profile summary."""
    summary: str = Field(
        ...,
        max_length=500,
        description="Generated professional profile summary",
    )
    user_id: uuid.UUID
    user_name: str
