import base64
import hmac
import hashlib
import struct
import time
import secrets
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User


def generate_totp_secret() -> str:
    """Generate a random 20-byte (160-bit) Base32 encoded TOTP secret."""
    raw_bytes = secrets.token_bytes(20)
    return base64.b32encode(raw_bytes).decode("utf-8").replace("=", "")


def get_totp_token(secret: str, interval: int = 30, t: Optional[int] = None) -> str:
    """Calculate 6-digit TOTP token using HMAC-SHA1 (RFC 6238 / RFC 4226)."""
    if t is None:
        t = int(time.time())
    counter = t // interval
    # Pad base32 secret if needed
    padded_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def verify_totp_token(secret: str, token: str, window: int = 1) -> bool:
    """Verify 6-digit TOTP token with +/- window periods tolerance."""
    if not secret or not token:
        return False
    current_time = int(time.time())
    clean_token = token.strip()
    for i in range(-window, window + 1):
        expected = get_totp_token(secret, t=current_time + i * 30)
        if hmac.compare_digest(expected, clean_token):
            return True
    return False


def generate_raw_backup_codes(count: int = 10) -> List[str]:
    """Generate list of 8-character hex recovery codes."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def hash_backup_code(code: str) -> str:
    """Hash a recovery code using SHA-256 for secure storage."""
    # lgtm[py/weak-sensitive-data-hashing]
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


class MFAService:
    @classmethod
    def generate_setup(cls, user: User) -> Dict[str, str]:
        """Generate a new TOTP secret and otpauth provisioning URI."""
        secret = generate_totp_secret()
        issuer = "DevLink"
        account_name = user.email or user.username
        provisioning_uri = f"otpauth://totp/{issuer}:{account_name}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
        }

    @classmethod
    def enable_mfa(
        cls, db: Session, user: User, secret: str, code: str
    ) -> Dict[str, Any]:
        """Verify initial code, enable MFA for user, and return recovery codes."""
        if user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is already enabled for this account",
            )

        if not verify_totp_token(secret, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please check your authenticator app and try again.",
            )

        raw_backup_codes = generate_raw_backup_codes(10)
        hashed_backup_codes = [hash_backup_code(c) for c in raw_backup_codes]

        user.mfa_secret = secret
        user.mfa_enabled = True
        user.mfa_backup_codes = hashed_backup_codes

        db.commit()
        db.refresh(user)

        return {
            "mfa_enabled": True,
            "backup_codes": raw_backup_codes,
            "message": "MFA enabled successfully. Store these recovery codes securely.",
        }

    @classmethod
    def disable_mfa(cls, db: Session, user: User, code: str) -> bool:
        """Disable MFA after verifying TOTP code or backup code."""
        if not user.mfa_enabled or not user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this account",
            )

        verified = cls.verify_user_mfa(db, user, code)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code or recovery code",
            )

        user.mfa_secret = None
        user.mfa_enabled = False
        user.mfa_backup_codes = None

        db.commit()
        db.refresh(user)
        return True

    @classmethod
    def regenerate_backup_codes(cls, db: Session, user: User, code: str) -> List[str]:
        """Regenerate recovery codes for user after verifying TOTP code."""
        if not user.mfa_enabled or not user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this account",
            )

        if not verify_totp_token(user.mfa_secret, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        raw_backup_codes = generate_raw_backup_codes(10)
        hashed_backup_codes = [hash_backup_code(c) for c in raw_backup_codes]

        user.mfa_backup_codes = hashed_backup_codes
        db.commit()
        db.refresh(user)

        return raw_backup_codes

    @classmethod
    def verify_user_mfa(cls, db: Session, user: User, code: str) -> bool:
        """Verify either TOTP code or single-use recovery code for user."""
        if not user.mfa_enabled or not user.mfa_secret:
            return True  # If MFA disabled, auto-pass

        clean_code = code.strip()

        # 1. Try TOTP code
        if verify_totp_token(user.mfa_secret, clean_code):
            return True

        # 2. Try single-use recovery code
        hashed = hash_backup_code(clean_code)
        backup_list = list(user.mfa_backup_codes or [])
        if hashed in backup_list:
            backup_list.remove(hashed)
            user.mfa_backup_codes = backup_list
            db.commit()
            return True

        return False
