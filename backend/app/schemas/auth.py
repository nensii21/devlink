from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import CurrentUser
from app.core.validation import NameStr, UsernameStr, ValidEmail

# ==========================================================
# Register
# ==========================================================


class RegisterRequest(BaseModel):
    first_name: NameStr
    last_name: NameStr

    username: UsernameStr

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
            }
        }
    )


# ==========================================================
# Login
# ==========================================================


class LoginRequest(BaseModel):
    email: ValidEmail

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "jane.doe@example.com",
                "password": "StrongPassword123!",
            }
        }
    )


class GitHubLoginRequest(BaseModel):
    code: str
    state: str = ""


class GoogleLoginRequest(BaseModel):
    code: str
    state: str = ""


class LinkedInLoginRequest(BaseModel):
    code: str
    state: str = ""


class MicrosoftLoginRequest(BaseModel):
    code: str
    state: str = ""


class OAuthStateResponse(BaseModel):
    state: str


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


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    message: str

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    mfa_required: bool = False
    mfa_token: Optional[str] = None
    user: Optional[CurrentUser] = None


# ==========================================================
# Refresh Token
# ==========================================================


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Successfully logged out."


# ==========================================================
# Sessions & Devices
# ==========================================================


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_current: bool = False
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: datetime


# ==========================================================
# Forgot Password
# ==========================================================


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str


class VerifyRecoveryTokenResponse(BaseModel):
    valid: bool = True
    message: str
    email: Optional[str] = None


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

    id: str
    id: UUID

    first_name: str
    last_name: str

    username: str

    email: EmailStr

    profile_image: Optional[str] = None

    is_verified: bool

    is_active: bool

    last_seen: Optional[datetime] = Field(
        default=None,
        description="The date and time when the user was last active.",
    )
    is_online: bool = Field(
        default=False,
        description="Whether the user is currently online based on the active threshold.",
    )
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
