from __future__ import annotations
from app.schemas.user import CurrentUser
from datetime import datetime
from typing import Optional
from uuid import UUID

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ==========================================================
# Register
# ==========================================================


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)

    username: str = Field(..., min_length=3, max_length=50)

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


# ==========================================================
# Login
# ==========================================================


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


class GitHubLoginRequest(BaseModel):
    code: str


class GitHubLoginRequest(BaseModel):
    code: str


# ==========================================================
# JWT Tokens
# ==========================================================


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int


# ==========================================================
# Authentication Response
# ==========================================================


from app.schemas.user import UserResponse


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    message: str

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None

    user: CurrentUser


# ==========================================================
# Refresh Token
# ==========================================================


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ==========================================================
# Logout
# ==========================================================


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Successfully logged out."


# ==========================================================
# Forgot Password
# ==========================================================


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str


# ==========================================================
# Reset Password
# ==========================================================


class ResetPasswordRequest(BaseModel):
    token: str

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


# ==========================================================
# Change Password
# ==========================================================


class ChangePasswordRequest(BaseModel):
    current_password: str

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


# ==========================================================
# Verify Email
# ==========================================================


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    success: bool = True
    message: str


# ==========================================================
# Resend Verification Email
# ==========================================================


class ResendVerificationEmailRequest(BaseModel):
    email: EmailStr


# ==========================================================
# Current User
# ==========================================================


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    first_name: str
    last_name: str

    username: str

    email: EmailStr

    profile_image: Optional[str] = None

    is_verified: bool

    is_active: bool

    last_active_at: Optional[datetime] = None

    created_at: datetime


# ==========================================================
# Generic Success
# ==========================================================


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


# ==========================================================
# Generic Error
# ==========================================================


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
