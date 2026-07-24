import pytest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id,
    is_access_token,
    is_refresh_token,
    validate_password_strength,
)


def test_password_hashing():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_password_strength_validation():
    # Valid password
    valid, msg = validate_password_strength("StrongPass1!")
    assert valid is True

    # Too short
    valid, msg = validate_password_strength("Str1!")
    assert valid is False
    assert "least 8 characters" in msg

    # No uppercase
    valid, msg = validate_password_strength("weakpass1!")
    assert valid is False
    assert "uppercase" in msg

    # No lowercase
    valid, msg = validate_password_strength("WEAKPASS1!")
    assert valid is False
    assert "lowercase" in msg

    # No digit
    valid, msg = validate_password_strength("WeakPass!")
    assert valid is False
    assert "number" in msg

    # No special character
    valid, msg = validate_password_strength("WeakPass123")
    assert valid is False
    assert "special character" in msg


def test_create_access_token():
    user_id = "test-user-id"
    extra_data = {"email": "test@example.com"}

    token = create_access_token(user_id, extra=extra_data)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert payload["email"] == "test@example.com"

    # Check helpers
    assert get_user_id(token) == user_id
    assert is_access_token(token) is True
    assert is_refresh_token(token) is False


def test_create_refresh_token():
    user_id = "test-user-id"

    token = create_refresh_token(user_id)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"

    # Check helpers
    assert is_refresh_token(token) is True
    assert is_access_token(token) is False


def test_decode_invalid_token():
    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_token("invalid.token.string")
