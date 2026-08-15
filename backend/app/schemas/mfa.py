from typing import List
from pydantic import BaseModel, Field


class MFASetupResponse(BaseModel):
    secret: str = Field(..., description="TOTP Base32 secret key")
    provisioning_uri: str = Field(
        ..., description="otpauth:// URI for authenticator setup"
    )


class MFAEnableRequest(BaseModel):
    secret: str = Field(..., description="TOTP Base32 secret key")
    code: str = Field(
        ..., description="6-digit verification code from authenticator app"
    )


class MFAEnableResponse(BaseModel):
    mfa_enabled: bool
    backup_codes: List[str]
    message: str


class MFADisableRequest(BaseModel):
    code: str = Field(..., description="6-digit TOTP code or single-use recovery code")


class MFARecoveryCodesRequest(BaseModel):
    code: str = Field(..., description="6-digit TOTP code")


class MFARecoveryCodesResponse(BaseModel):
    backup_codes: List[str]


class MFAStatusResponse(BaseModel):
    mfa_enabled: bool


class MFAVerifyLoginRequest(BaseModel):
    mfa_token: str = Field(
        ..., description="Short-lived pending MFA authentication token"
    )
    code: str = Field(..., description="6-digit TOTP code or recovery code")
