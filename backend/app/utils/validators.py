"""
DevLink Validation Utilities

Reusable validation functions used across the application.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from fastapi import HTTPException, status


# ==========================================================
# Username Validation
# ==========================================================

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")


def validate_username(username: str) -> str:
    """
    Validate username.

    Rules:
    - 3-30 characters
    - letters
    - numbers
    - underscore
    - dash
    - period
    """

    username = username.strip()

    if not USERNAME_REGEX.fullmatch(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Username may contain only letters, "
                "numbers, underscores (_), dashes (-), "
                "and periods (.)."
            ),
        )

    return username


# ==========================================================
# Password Validation
# ==========================================================


def validate_password(password: str) -> str:
    """
    Validate password strength.
    """

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    if len(password) > 128:
        raise HTTPException(
            status_code=400,
            detail="Password is too long.",
        )

    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain an uppercase letter.",
        )

    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain a lowercase letter.",
        )

    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain a number.",
        )

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain a special character.",
        )

    return password


# ==========================================================
# Email Validation
# ==========================================================


EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def validate_email(email: str) -> str:
    email = email.lower().strip()

    if not EMAIL_REGEX.fullmatch(email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email address.",
        )

    return email


# ==========================================================
# URL Validation
# ==========================================================


def validate_url(url: str | None) -> str | None:
    if not url:
        return None

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid URL.",
        )

    return url


# ==========================================================
# GitHub URL
# ==========================================================


def validate_github_url(url: str | None) -> str | None:
    if not url:
        return None

    validate_url(url)

    if "github.com" not in url.lower():
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub profile URL.",
        )

    return url


# ==========================================================
# LinkedIn URL
# ==========================================================


def validate_linkedin_url(url: str | None) -> str | None:
    if not url:
        return None

    validate_url(url)

    if "linkedin.com" not in url.lower():
        raise HTTPException(
            status_code=400,
            detail="Invalid LinkedIn profile URL.",
        )

    return url


# ==========================================================
# Portfolio URL
# ==========================================================


def validate_portfolio(url: str | None) -> str | None:
    if not url:
        return None

    return validate_url(url)


# ==========================================================
# Text Sanitization
# ==========================================================


def sanitize_text(text: str | None) -> str | None:
    """
    Basic XSS protection.

    Escapes HTML characters.
    """

    if text is None:
        return None

    replacements = {
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


# ==========================================================
# Name Validation
# ==========================================================


NAME_REGEX = re.compile(r"^[A-Za-z\s'-]{2,100}$")


def validate_name(name: str) -> str:
    name = name.strip()

    if not NAME_REGEX.fullmatch(name):
        raise HTTPException(
            status_code=400,
            detail="Invalid name.",
        )

    return name


# ==========================================================
# Generic Length Validation
# ==========================================================


def validate_length(
    value: str,
    minimum: int,
    maximum: int,
    field: str,
) -> str:
    length = len(value)

    if length < minimum:
        raise HTTPException(
            status_code=400,
            detail=f"{field} must be at least {minimum} characters.",
        )

    if length > maximum:
        raise HTTPException(
            status_code=400,
            detail=f"{field} cannot exceed {maximum} characters.",
        )

    return value


# ==========================================================
# Allowed Image Types
# ==========================================================


ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}


def validate_image_type(content_type: str) -> None:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type.",
        )


# ==========================================================
# Max Upload Size
# ==========================================================


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file_size(size: int) -> None:
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File exceeds maximum allowed size.",
        )