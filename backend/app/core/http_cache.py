"""
HTTP caching primitives.

Small, dependency-free helpers for entity tags and conditional requests as
described in RFC 9110 sections 8.8 and 13.1. Kept separate from the middleware
so the parsing/comparison rules can be unit tested on their own.
"""

import hashlib
from typing import Iterable, List, Optional

# Media types we are willing to fingerprint. Anything else (images, PDFs,
# octet-streams) is either already cheap to revalidate or too large to buffer.
ETAGGABLE_CONTENT_TYPES: tuple[str, ...] = (
    "application/json",
    "application/problem+json",
    "text/plain",
    "text/html",
)

# Header names are compared lowercase throughout; ASGI guarantees byte keys but
# not a particular case.
_WILDCARD = "*"


def generate_etag(body: bytes, weak: bool = False) -> str:
    """
    Build an entity tag for a fully buffered response body.

    Uses SHA-256 truncated to 32 hex characters. That is 128 bits of digest,
    which is far more than enough to make an accidental collision between two
    payloads of the same resource impossible in practice, while keeping the
    header short.
    """
    digest = hashlib.sha256(body).hexdigest()[:32]
    tag = f'"{digest}"'
    return f"W/{tag}" if weak else tag


def parse_if_none_match(header_value: Optional[str]) -> List[str]:
    """
    Split an ``If-None-Match`` header into individual entity tags.

    The header is a comma separated list, optionally with weak validator
    prefixes, e.g. ``W/"abc", "def"``. A bare ``*`` is returned as-is so the
    caller can apply the wildcard rule.
    """
    if not header_value:
        return []

    raw = header_value.strip()
    if raw == _WILDCARD:
        return [_WILDCARD]

    tags: List[str] = []
    for candidate in raw.split(","):
        candidate = candidate.strip()
        if candidate:
            tags.append(candidate)
    return tags


def _strip_weak_prefix(tag: str) -> str:
    """Remove a ``W/`` validator prefix if present."""
    if tag.startswith("W/"):
        return tag[2:]
    if tag.startswith("w/"):
        return tag[2:]
    return tag


def etag_matches(current_etag: str, client_tags: Iterable[str]) -> bool:
    """
    Decide whether a response still matches what the client already holds.

    ``If-None-Match`` uses the *weak* comparison function, so ``W/"abc"`` and
    ``"abc"`` are considered equivalent. A ``*`` matches any existing
    representation.
    """
    normalised_current = _strip_weak_prefix(current_etag)

    for tag in client_tags:
        if tag == _WILDCARD:
            return True
        if _strip_weak_prefix(tag) == normalised_current:
            return True

    return False


def is_etaggable_content_type(content_type: Optional[str]) -> bool:
    """
    Whether a response's ``Content-Type`` is one we fingerprint.

    The header may carry parameters (``application/json; charset=utf-8``), so
    only the media type portion is considered.
    """
    if not content_type:
        return False

    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type in ETAGGABLE_CONTENT_TYPES


def merge_vary(existing: Optional[str], additions: Iterable[str]) -> str:
    """
    Add field names to a ``Vary`` header without duplicating them.

    Returns ``*`` unchanged if the response already varies on everything.
    """
    current = [part.strip() for part in (existing or "").split(",") if part.strip()]

    if any(part == _WILDCARD for part in current):
        return _WILDCARD

    seen = {part.lower() for part in current}
    for addition in additions:
        if addition.lower() not in seen:
            current.append(addition)
            seen.add(addition.lower())

    return ", ".join(current)
