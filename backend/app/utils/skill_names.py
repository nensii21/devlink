"""Shared skill-name normalization helpers."""

from __future__ import annotations


def normalize_skill_name(value: str) -> str:
    """Return the canonical value used to compare skill names."""

    return " ".join(value.strip().split()).casefold()


def clean_skill_name(value: str) -> str:
    """Return a display-friendly skill name without changing its casing."""

    return " ".join(value.strip().split())
