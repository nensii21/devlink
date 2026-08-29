"""
Token type enforcement.

Every JWT this application mints carries a ``type`` claim. These tests pin
down the thing that makes the claim worth having: that a token minted for one
purpose cannot be presented for another.

The case that matters most is the refresh token. It is deliberately
long-lived and it lives in browser storage, and that trade is only acceptable
while it cannot be used as a bearer credential. The same argument applies to
the verification and password-reset tokens, both of which travel by email --
to an address that, in the verification case, has not yet been proven to
belong to the account holder.
"""

from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.security import (
    InvalidTokenType,
    TokenType,
    _create_token,
    create_access_token,
    create_refresh_token,
    create_verification_token,
    decode_access_token,
    decode_token,
    is_access_token,
    is_refresh_token,
    is_verification_token,
)

USER_ID = "3f1d9f5e-6a2c-4f7b-9c1e-2b8a7d4e5f60"


def _reset_password_token(user_id: str = USER_ID) -> str:
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=15),
        token_type=TokenType.RESET_PASSWORD,
    )


def _mfa_pending_token(user_id: str = USER_ID) -> str:
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=5),
        token_type=TokenType.MFA_PENDING,
    )


#: Every token type that is *not* an access token, with the flow that mints it.
NON_ACCESS_TOKENS = [
    pytest.param(create_refresh_token, id="refresh"),
    pytest.param(create_verification_token, id="verification"),
    pytest.param(_reset_password_token, id="reset_password"),
    pytest.param(_mfa_pending_token, id="mfa_pending"),
]


# ---------------------------------------------------------------------------
# decode_token
# ---------------------------------------------------------------------------


def test_decode_token_without_expected_type_accepts_any_type():
    """The permissive form still exists, for callers that read the claim."""
    payload = decode_token(create_refresh_token(USER_ID))

    assert payload["type"] == TokenType.REFRESH
    assert payload["sub"] == USER_ID


def test_decode_token_accepts_the_matching_type():
    payload = decode_token(create_access_token(USER_ID), expected_type=TokenType.ACCESS)

    assert payload["sub"] == USER_ID


@pytest.mark.parametrize("mint", NON_ACCESS_TOKENS)
def test_decode_access_token_rejects_every_other_type(mint):
    """The regression this file exists for."""
    with pytest.raises(InvalidTokenType):
        decode_access_token(mint(USER_ID))


def test_invalid_token_type_is_a_value_error():
    """
    Callers that predate the distinction catch ``ValueError``; they must keep
    working without being changed.
    """
    assert issubclass(InvalidTokenType, ValueError)

    with pytest.raises(ValueError):
        decode_access_token(create_refresh_token(USER_ID))


def test_untyped_token_is_rejected_when_a_type_is_expected():
    """
    A token with no ``type`` claim must not be assumed to be an access token.
    Treating an unrecognised token as the most privileged kind is the wrong
    way round.
    """
    untyped = _create_token(
        subject=USER_ID,
        expires_delta=timedelta(minutes=5),
        token_type=TokenType.ACCESS,
    )
    # Strip the claim the way a pre-`type` token would have looked.
    from jose import jwt

    from app.core.config import settings

    payload = jwt.decode(
        untyped, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    payload.pop("type")
    stripped = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    with pytest.raises(InvalidTokenType):
        decode_access_token(stripped)

    # ...and is still readable by the callers that do not assert a type.
    assert decode_token(stripped)["sub"] == USER_ID


def test_expired_token_still_raises_value_error_not_invalid_type():
    """An expired access token is expired, not the wrong type."""
    expired = _create_token(
        subject=USER_ID,
        expires_delta=timedelta(seconds=-30),
        token_type=TokenType.ACCESS,
    )

    with pytest.raises(ValueError) as excinfo:
        decode_access_token(expired)

    assert not isinstance(excinfo.value, InvalidTokenType)


def test_garbage_is_rejected():
    with pytest.raises(ValueError):
        decode_token("not-a-jwt", expected_type=TokenType.ACCESS)


def test_reset_token_accepts_the_legacy_alias():
    """
    ``reset`` predates ``reset_password``. Tokens carrying the old spelling
    are still in flight for up to 15 minutes after a deploy.
    """
    legacy = _create_token(
        subject=USER_ID,
        expires_delta=timedelta(minutes=15),
        token_type="reset",
    )

    assert (
        decode_token(legacy, expected_type=TokenType.RESET_PASSWORD)["sub"] == USER_ID
    )

    # The alias is one-directional: a reset token is not an access token.
    with pytest.raises(InvalidTokenType):
        decode_access_token(legacy)


# ---------------------------------------------------------------------------
# Reserved claims
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("claim", ["type", "sub", "exp", "iat"])
def test_extra_cannot_overwrite_a_reserved_claim(claim):
    """
    Otherwise any flow could stamp ``"type": "access"`` onto its token and
    walk straight past the check above.
    """
    with pytest.raises(ValueError, match="reserved claims"):
        _create_token(
            subject=USER_ID,
            expires_delta=timedelta(minutes=5),
            token_type=TokenType.VERIFICATION,
            extra={claim: "access"},
        )


def test_extra_still_carries_ordinary_claims():
    token = create_access_token(USER_ID, extra={"email": "dev@example.com"})
    payload = decode_access_token(token)

    assert payload["email"] == "dev@example.com"
    assert payload["type"] == TokenType.ACCESS


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def test_predicates_agree_with_the_minting_function():
    access = create_access_token(USER_ID)
    refresh = create_refresh_token(USER_ID)
    verification = create_verification_token(USER_ID)

    assert is_access_token(access) is True
    assert is_refresh_token(access) is False
    assert is_verification_token(access) is False

    assert is_refresh_token(refresh) is True
    assert is_access_token(refresh) is False

    assert is_verification_token(verification) is True
    assert is_access_token(verification) is False


def test_predicates_answer_false_for_junk_rather_than_raising():
    """
    A predicate that throws instead of answering forces a try/except at every
    call site, and the sites that forget are the ones that matter.
    """
    assert is_access_token("not-a-jwt") is False
    assert is_refresh_token("") is False
    assert is_verification_token("a.b.c") is False


# ---------------------------------------------------------------------------
# The authentication dependency
# ---------------------------------------------------------------------------


@pytest.fixture
def stored_user(db):
    """A persisted user for the token subject to point at."""
    from app.models.user import User

    user = User(
        first_name="Ada",
        last_name="Lovelace",
        username="ada_tokentype",
        email="ada.tokentype@example.com",
        password_hash="irrelevant_hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def guarded_client(db):
    """
    A minimal app with one endpoint behind ``get_current_user``.

    Mounted standalone rather than reusing the real app so the assertion is
    about the dependency itself and not about whichever router happened to be
    picked as a sample.
    """
    from app.dependencies import get_current_user, get_database
    from app.models.user import User

    app = FastAPI()

    @app.get("/whoami")
    def whoami(current_user: User = Depends(get_current_user)):
        return {"id": str(current_user.id)}

    app.dependency_overrides[get_database] = lambda: db

    with TestClient(app) as client:
        yield client


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_access_token_authenticates(guarded_client, stored_user):
    response = guarded_client.get(
        "/whoami", headers=_auth(create_access_token(str(stored_user.id)))
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(stored_user.id)


@pytest.mark.parametrize("mint", NON_ACCESS_TOKENS)
def test_non_access_tokens_do_not_authenticate(guarded_client, stored_user, mint):
    """
    The bug: all four of these are correctly signed for a real user, and all
    four used to authenticate on every endpoint in the application.
    """
    response = guarded_client.get("/whoami", headers=_auth(mint(str(stored_user.id))))

    assert response.status_code == 401


def test_missing_credentials_are_rejected(guarded_client):
    assert guarded_client.get("/whoami").status_code == 401


def test_optional_user_dependency_also_rejects_non_access_tokens(db, stored_user):
    from app.dependencies import get_database, get_optional_current_user
    from app.models.user import User

    app = FastAPI()

    @app.get("/maybe")
    def maybe(current_user: User | None = Depends(get_optional_current_user)):
        return {"id": str(current_user.id) if current_user else None}

    app.dependency_overrides[get_database] = lambda: db

    with TestClient(app) as client:
        signed_in = client.get(
            "/maybe", headers=_auth(create_access_token(str(stored_user.id)))
        )
        assert signed_in.json()["id"] == str(stored_user.id)

        with_refresh = client.get(
            "/maybe", headers=_auth(create_refresh_token(str(stored_user.id)))
        )
        assert with_refresh.status_code == 200
        assert with_refresh.json()["id"] is None


def test_get_current_user_id_is_defined_once_and_returns_a_string():
    """
    This module used to define ``get_current_user_id`` twice, annotated
    ``-> UUID`` and ``-> str``, with the second silently winning. Every call
    site in the tree annotates ``str``.
    """
    import inspect

    import app.dependencies as dependencies

    source = inspect.getsource(dependencies)

    assert source.count("def get_current_user_id(") == 1
    assert source.count("def get_optional_current_user(") == 1
