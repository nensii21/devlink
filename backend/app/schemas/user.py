from __future__ import annotations

import uuid
from datetime import datetime, time
from enum import Enum

# pyrefly: ignore [missing-import]
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.core.validation import (
    BioStr,
    HeadlineStr,
    NameStr,
    SanitizedStr,
    UsernameStr,
    ValidEmail,
    ValidURL,
)


class AvailabilitySlot(BaseModel):
    day: str
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class PrivacyVisibility(str, Enum):
    PUBLIC = "public"
    FOLLOWERS = "followers"
    AUTHENTICATED = "authenticated"
    PRIVATE = "private"


class CollaborationStatus(str, Enum):
    """Live collaboration presence status a user can set."""

    CODING = "coding"
    REVIEWING_PR = "reviewing_pr"
    IN_MEETING = "in_meeting"
    LOOKING_FOR_PROJECT = "looking_for_project"
    AVAILABLE = "available"


COLLABORATION_STATUSES = tuple(status.value for status in CollaborationStatus)


class PrivacySettings(BaseModel):
    email: PrivacyVisibility = PrivacyVisibility.PRIVATE
    github: PrivacyVisibility = PrivacyVisibility.PUBLIC
    resume: PrivacyVisibility = PrivacyVisibility.PUBLIC
    social_links: PrivacyVisibility = PrivacyVisibility.PUBLIC
    availability: PrivacyVisibility = PrivacyVisibility.PUBLIC
    activity: PrivacyVisibility = PrivacyVisibility.PUBLIC


class PrivacySettingsUpdate(BaseModel):
    email: PrivacyVisibility | None = None
    github: PrivacyVisibility | None = None
    resume: PrivacyVisibility | None = None
    social_links: PrivacyVisibility | None = None
    availability: PrivacyVisibility | None = None
    activity: PrivacyVisibility | None = None


# ==========================================================
# Base User Schema
# ==========================================================


class UserBase(BaseModel):
    first_name: NameStr
    last_name: NameStr

    username: UsernameStr

    public_email: ValidEmail | None = None

    headline: HeadlineStr | None = None

    bio: BioStr | None = None

    location: SanitizedStr | None = None
    timezone: SanitizedStr | None = None

    website: ValidURL | None = None
    profile_image: ValidURL | None = None
    resume_url: ValidURL | None = None
    voice_introduction_url: ValidURL | None = None
    portfolio_url: ValidURL | None = None
    github_url: ValidURL | None = None
    linkedin_url: ValidURL | None = None
    twitter_url: ValidURL | None = None

    skills: list[str] = Field(default_factory=list)

    role: SanitizedStr | None = None
    experience_level: SanitizedStr | None = None
    company: SanitizedStr | None = None

    experience: list | None = None
    education: list | None = None
    certifications: list | None = None

    open_to_work: bool = True
    is_private: bool = False
    is_active: bool = True
    is_verified: bool = False
    privacy_settings: PrivacySettings | None = Field(default_factory=PrivacySettings)
    availability: list[AvailabilitySlot] = Field(default_factory=list)
    collaboration_status: CollaborationStatus | None = CollaborationStatus.AVAILABLE


# ==========================================================
# Create User
# ==========================================================


class UserCreate(UserBase):
    email: ValidEmail
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "email": "jane.doe@example.com",
                "password": "StrongPassword123!",
                "open_to_work": True,
            }
        }
    )


# ==========================================================
# Update User
# ==========================================================


class UserUpdate(BaseModel):
    first_name: NameStr | None = None
    last_name: NameStr | None = None
    username: UsernameStr | None = None

    headline: HeadlineStr | None = None
    bio: BioStr | None = None

    location: SanitizedStr | None = None
    timezone: SanitizedStr | None = None
    public_email: ValidEmail | None = None

    website: ValidURL | None = None
    profile_image: ValidURL | None = None
    resume_url: ValidURL | None = None
    voice_introduction_url: ValidURL | None = None
    portfolio_url: ValidURL | None = None
    github_url: ValidURL | None = None
    linkedin_url: ValidURL | None = None
    twitter_url: ValidURL | None = None

    skills: list[str] | None = None

    role: SanitizedStr | None = None
    experience_level: SanitizedStr | None = None
    company: SanitizedStr | None = None

    experience: list | None = None
    education: list | None = None
    certifications: list | None = None

    open_to_work: bool | None = None
    is_private: bool | None = None
    privacy_settings: PrivacySettingsUpdate | None = None
    availability: list[AvailabilitySlot] | None = None
    version: int | None = None
    collaboration_status: CollaborationStatus | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Jane",
                "last_name": "Smith",
                "headline": "Senior Full-Stack Developer",
                "bio": "I love building scalable web applications.",
                "location": "San Francisco, CA",
                "github_url": "https://github.com/janesmith",
            }
        }
    )


# ==========================================================
# Public User Response
# ==========================================================


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    is_active: bool
    is_verified: bool
    premium: bool = False
    is_superuser: bool
    version: int = 1
    video_introduction_url: ValidURL | None = None
    video_introduction_thumbnail_url: ValidURL | None = None


# ==========================================================
# Resume Parse Response
# ==========================================================


class ResumeParseResponse(BaseModel):
    skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    certifications: list[dict] = Field(default_factory=list)


# ==========================================================
# Private User Response
# ==========================================================


class CurrentUser(UserResponse):
    email: ValidEmail
    email_verified_at: datetime | None = None
    last_login: datetime | None = None


# ==========================================================
# Profile Statistics
# ==========================================================


class UserStats(BaseModel):
    projects: int = 0
    followers: int = 0
    following: int = 0
    applications: int = 0
    accepted: int = 0


# ==========================================================
# Developer Profile
# ==========================================================


class DeveloperProfile(BaseModel):
    user: UserResponse
    stats: UserStats


# ==========================================================
# Generic API Response
# ==========================================================


class UserMessage(BaseModel):
    message: str


# ==========================================================
# Username Availability
# ==========================================================


class UsernameAvailabilityResponse(BaseModel):
    available: bool
    message: str


# ==========================================================
# Profile Completion Response
# ==========================================================


class ProfileCompletionResponse(BaseModel):
    completion: int = Field(
        ...,
        ge=0,
        le=100,
        description="Profile completion percentage (0-100)",
    )
    missing: list[str] = Field(
        ...,
        description="List of missing profile factors",
    )
    completed_factors: list[str] = Field(
        default_factory=list,
        description="List of completed profile factors",
    )
    reward_unlocked: bool = Field(
        default=False,
        description="Whether the profile completion reward is unlocked",
    )
    reward_badge: str | None = Field(
        default=None,
        description="Badge awarded for 100% profile completion",
    )
