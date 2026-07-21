from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

# ==========================================================
# Base User Schema
# ==========================================================


class UserBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    public_email: Optional[EmailStr] = None

    headline: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    bio: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    location: Optional[str] = None
    timezone: Optional[str] = None

    website: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None

    role: Optional[str] = None
    experience_level: Optional[str] = None
    company: Optional[str] = None

    open_to_work: bool = True


# ==========================================================
# Create User
# ==========================================================


class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


# ==========================================================
# Update User
# ==========================================================


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    headline: Optional[str] = None
    bio: Optional[str] = None

    location: Optional[str] = None
    timezone: Optional[str] = None
    public_email: Optional[EmailStr] = None

    website: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None

    role: Optional[str] = None
    experience_level: Optional[str] = None
    company: Optional[str] = None

    open_to_work: Optional[bool] = None


# ==========================================================
# Public User Response
# ==========================================================


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    profile_image: Optional[str] = None
    cover_image: Optional[str] = None

    is_active: bool
    is_verified: bool
    is_superuser: bool

    last_active_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


# ==========================================================
# Private User Response
# ==========================================================


class CurrentUser(UserResponse):
    email: EmailStr
    email_verified_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


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
