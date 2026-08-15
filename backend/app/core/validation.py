from typing import Annotated

from pydantic import BeforeValidator, Field, EmailStr, HttpUrl


def sanitize_string(value: str) -> str:
    """Strip leading/trailing whitespace and remove null bytes."""
    if isinstance(value, str):
        return value.strip().replace("\x00", "")
    return value


def sanitize_lower(value: str) -> str:
    """Sanitize and convert to lowercase."""
    if isinstance(value, str):
        return sanitize_string(value).lower()
    return value


# Reusable Pydantic Annotated Types

SanitizedStr = Annotated[str, BeforeValidator(sanitize_string)]

# Usernames: 3-50 chars, alphanumeric, underscores, hyphens, dots. Must start with alphanumeric.
UsernameStr = Annotated[
    str,
    Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]+$"),
    BeforeValidator(sanitize_lower),
]

ValidEmail = Annotated[EmailStr, BeforeValidator(sanitize_lower)]

ValidURL = Annotated[HttpUrl, BeforeValidator(sanitize_string)]

# Standard name fields (e.g. first_name, last_name)
NameStr = Annotated[
    str, Field(min_length=2, max_length=100), BeforeValidator(sanitize_string)
]

# Longer text fields (e.g. bio, headline)
HeadlineStr = Annotated[str, Field(max_length=150), BeforeValidator(sanitize_string)]

BioStr = Annotated[str, Field(max_length=1000), BeforeValidator(sanitize_string)]
