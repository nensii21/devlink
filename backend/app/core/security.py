import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
import bcrypt

# bcrypt refuses passwords longer than 72 bytes. passlib does not truncate for
# us, so the call is wrapped to do it.
#
# This block was duplicated -- the identical patch appeared twice, presumably
# from a bad merge -- and the second copy captured the *already patched*
# function as its `_original_hashpw`. `_patched_hashpw` therefore called
# itself, and every password hash died with:
#
#     RecursionError: maximum recursion depth exceeded
#
# which took registration and login with it. Nothing caught it because
# tests/conftest.py replaces pwd_context with a mock before the suite runs, so
# bcrypt is never exercised there.
#
# `_ALREADY_PATCHED` makes reapplying the patch a no-op, so a re-import or a
# future duplicate cannot recreate the loop.
if not getattr(bcrypt.hashpw, "_devlink_patched", False):
    _original_hashpw = bcrypt.hashpw

    def _patched_hashpw(password, salt):
        if len(password) > 72:
            return _original_hashpw(password[:72], salt)
        return _original_hashpw(password, salt)

    _patched_hashpw._devlink_patched = True
    bcrypt.hashpw = _patched_hashpw

from passlib.context import CryptContext  # noqa: E402

from app.core.config import settings  # noqa: E402

# ------------------------------------------------------------------
# Password Hashing
# ------------------------------------------------------------------

pwd_context = CryptContext(
    schemes=[settings.PASSWORD_HASH_SCHEME],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


# ------------------------------------------------------------------
# JWT Token Types
# ------------------------------------------------------------------
#
# Every token this module mints carries a `type` claim saying what it is for.
# The claim is only worth something if the code consuming a token checks it,
# which is what `decode_token(..., expected_type=...)` below is for.
#
# The distinction matters most for the pair that is deliberately asymmetric:
# an access token is short-lived and travels on every request, a refresh token
# is long-lived and sits in browser storage. That trade only holds while the
# long-lived one cannot be presented as the short-lived one.


class TokenType:
    """The `type` claim values in use. String constants, not an Enum, so they
    compare directly against the decoded claim without unwrapping."""

    ACCESS = "access"
    REFRESH = "refresh"
    VERIFICATION = "verification"
    RESET_PASSWORD = "reset_password"
    MFA_PENDING = "mfa_pending"


#: Historic aliases. `reset` predates `reset_password` and still appears in
#: tokens that were issued before the rename, so it stays accepted for the
#: password-reset flow only.
_TOKEN_TYPE_ALIASES: Dict[str, frozenset] = {
    TokenType.RESET_PASSWORD: frozenset({"reset_password", "reset"}),
}


class InvalidTokenType(ValueError):
    """
    Raised when a token is well-formed and correctly signed but is not the
    kind of token the caller asked for.

    Subclasses :class:`ValueError` because that is what :func:`decode_token`
    has always raised for a token it will not accept, and every existing
    caller either catches ``ValueError`` or catches ``Exception``. Having its
    own type lets the places that care tell "this token is junk" apart from
    "this is a real token, but the wrong one".
    """


def _accepted_types(expected_type: str) -> frozenset:
    """The set of `type` claim values that satisfy ``expected_type``."""
    return _TOKEN_TYPE_ALIASES.get(expected_type, frozenset({expected_type}))


# ------------------------------------------------------------------
# JWT Tokens
# ------------------------------------------------------------------


#: Claims that identify the token and may not be supplied through ``extra``.
_RESERVED_CLAIMS = frozenset({"sub", "type", "iat", "exp"})


def _create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Internal JWT token creator.

    ``extra`` carries additional claims, and cannot overwrite the four the
    creator sets itself. It previously could -- ``payload.update(extra)`` ran
    last -- so ``create_access_token(uid, {"type": "mfa_pending"})`` was how
    the MFA flow minted its token. Convenient, but it also meant any caller
    could stamp ``"type": "access"`` onto a token from a flow that had no
    business issuing one, which is precisely the confusion the type claim
    exists to prevent. Callers that want a different type ask for it here.
    """

    now = datetime.now(timezone.utc)

    if extra:
        conflicting = _RESERVED_CLAIMS.intersection(extra)
        if conflicting:
            raise ValueError(
                "extra may not overwrite reserved claims: "
                + ", ".join(sorted(conflicting))
            )

    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }

    if extra:
        payload.update(extra)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    user_id: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate JWT access token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.ACCESS,
        extra=extra,
    )


def create_refresh_token(
    user_id: str,
) -> str:
    """
    Generate refresh token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=TokenType.REFRESH,
        extra={"jti": str(uuid.uuid4())},
    )


def create_verification_token(
    user_id: str,
) -> str:
    """
    Generate email verification token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        token_type=TokenType.VERIFICATION,
    )


# ------------------------------------------------------------------
# Decode Tokens
# ------------------------------------------------------------------


def decode_token(
    token: str,
    expected_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decode and validate a JWT.

    Verifies the signature and expiry, and -- when ``expected_type`` is given
    -- that the token's ``type`` claim is the kind of token the caller asked
    for.

    ``expected_type`` defaults to ``None``, meaning "any type", because a
    handful of callers legitimately want the payload before they know what
    they are holding (``/api/auth/refresh`` reads the claim itself, the
    logging middleware only wants ``sub`` for attribution). Every caller that
    is making an *authorisation* decision must pass it. Leaving it off there
    is what let a refresh, verification or password-reset token authenticate
    as an access token.

    A token with no ``type`` claim at all is rejected whenever a type is
    expected. Tokens predating the claim would be indistinguishable from an
    access token otherwise, and treating an unknown token as the most
    privileged kind is the wrong default -- worst case those tokens are
    already past their expiry, and the recovery path is to sign in again.

    Raises:
        InvalidTokenType: correctly signed, but not ``expected_type``.
        ValueError: malformed, expired, or not signed by us.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    if expected_type is not None:
        actual = payload.get("type")
        if actual not in _accepted_types(expected_type):
            raise InvalidTokenType(
                f"Expected a {expected_type} token, got {actual or 'an untyped token'}."
            )

    return payload


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode a token that must be an access token.

    The one to reach for in an authentication dependency: it is shorter than
    passing the constant every time, and it cannot be called without the check
    the way ``decode_token`` can.
    """

    return decode_token(token, expected_type=TokenType.ACCESS)


# ------------------------------------------------------------------
# Token Helpers
# ------------------------------------------------------------------


def get_user_id(token: str) -> Optional[str]:
    """
    Extract user ID from token.

    Does not check the token type -- callers that care should decode with an
    ``expected_type`` instead of reading the subject out of an arbitrary
    token.
    """

    payload = decode_token(token)

    return payload.get("sub")


def _is_token_of_type(token: str, expected_type: str) -> bool:
    """
    Whether ``token`` is a valid token of ``expected_type``.

    Returns ``False`` for a token that is expired, forged or malformed rather
    than raising. A predicate named ``is_...`` that throws instead of
    answering forces every call site into a try/except, and the ones that
    forgot are the interesting ones.
    """

    try:
        decode_token(token, expected_type=expected_type)
    except ValueError:
        return False

    return True


def is_access_token(token: str) -> bool:
    """
    Check if token is an access token.
    """

    return _is_token_of_type(token, TokenType.ACCESS)


def is_refresh_token(token: str) -> bool:
    """
    Check if token is a refresh token.
    """

    return _is_token_of_type(token, TokenType.REFRESH)


def is_verification_token(token: str) -> bool:
    """
    Check if token is an email verification token.
    """

    return _is_token_of_type(token, TokenType.VERIFICATION)


# ------------------------------------------------------------------
# Password Strength
# ------------------------------------------------------------------


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password against minimum security rules.
    """

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if not any(c.isupper() for c in password):
        return False, "Password must contain an uppercase letter."

    if not any(c.islower() for c in password):
        return False, "Password must contain a lowercase letter."

    if not any(c.isdigit() for c in password):
        return False, "Password must contain a number."

    if not any(not c.isalnum() for c in password):
        return False, "Password must contain a special character."

    return True, "Password is strong."


# ------------------------------------------------------------------
# Security Utilities
# ------------------------------------------------------------------


def generate_token_payload(user_id: str, email: str) -> Dict[str, Any]:
    """
    Common payload included in JWTs.
    """

    return {
        "uid": user_id,
        "email": email,
    }
