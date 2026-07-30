from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict

from app.models.hackathon import HackathonStatus
from app.models.hackathon_registration import RegistrationStatus
from app.models.hackathon_submission import SubmissionStatus
from app.models.hackathon_team import TeamMemberRole

# ==============================================================
# Hackathon
# ==============================================================


class HackathonBase(BaseModel):
    name: str
    description: str
    theme: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    min_team_size: int = 1
    max_team_size: int = 4
    prize: Optional[str] = None
    website_url: Optional[str] = None


class HackathonCreate(HackathonBase):
    registration_starts_at: Optional[datetime] = None
    registration_ends_at: Optional[datetime] = None


class HackathonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    registration_starts_at: Optional[datetime] = None
    registration_ends_at: Optional[datetime] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    min_team_size: Optional[int] = None
    max_team_size: Optional[int] = None
    prize: Optional[str] = None
    website_url: Optional[str] = None


class HackathonResponse(HackathonBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by: uuid.UUID
    status: HackathonStatus
    is_published: bool
    registration_starts_at: Optional[datetime] = None
    registration_ends_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ==============================================================
# Hackathon Team
# ==============================================================


class HackathonTeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class HackathonTeamCreate(HackathonTeamBase):
    pass


class HackathonTeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role: TeamMemberRole
    is_active: bool
    created_at: datetime


class HackathonTeamResponse(HackathonTeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hackathon_id: uuid.UUID
    created_by: uuid.UUID
    member_count: int
    created_at: datetime
    updated_at: datetime
    members: list[HackathonTeamMemberResponse] = []


# ==============================================================
# Hackathon Registration
# ==============================================================


class HackathonRegistrationBase(BaseModel):
    motivation: Optional[str] = None
    experience_level: Optional[str] = None


class HackathonRegistrationCreate(HackathonRegistrationBase):
    pass


class HackathonRegistrationResponse(HackathonRegistrationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hackathon_id: uuid.UUID
    user_id: uuid.UUID
    team_id: Optional[uuid.UUID] = None
    status: RegistrationStatus
    created_at: datetime
    updated_at: datetime


# ==============================================================
# Hackathon Submission
# ==============================================================


class HackathonSubmissionBase(BaseModel):
    title: str
    description: str
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None


class HackathonSubmissionCreate(HackathonSubmissionBase):
    team_id: uuid.UUID


class HackathonSubmissionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None


class HackathonSubmissionResponse(HackathonSubmissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hackathon_id: uuid.UUID
    team_id: uuid.UUID
    submitted_by: uuid.UUID
    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime


# ==============================================================
# Hackathon Judge
# ==============================================================


class HackathonJudgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hackathon_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


# ==============================================================
# Hackathon Score
# ==============================================================


class HackathonScoreBase(BaseModel):
    score: int
    comments: Optional[str] = None


class HackathonScoreCreate(HackathonScoreBase):
    submission_id: uuid.UUID


class HackathonScoreResponse(HackathonScoreBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submission_id: uuid.UUID
    judge_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ==============================================================
# Leaderboard
# ==============================================================


class HackathonLeaderboardEntry(BaseModel):
    rank: int = 0
    team_id: str
    team_name: str
    submission_title: str = ""
    avg_score: float = 0.0
    judge_count: int = 0
