"""
Deciding what an uploaded file actually is, and where it is allowed to go.

Two rules, both of which the storage layer was breaking.

**What a file is comes from its bytes.** ``UploadFile.content_type`` is the
``Content-Type`` of the multipart part, which the uploader writes. Trusting it
means an attacker uploads ``payload.svg`` or an HTML document and simply
declares ``image/png``. The allowlist check passes and the file is stored.

**Where a file goes is our decision, not the client's.** The stored extension
was copied out of the client's filename, so ``x.html`` declared as
``image/png`` was written as ``<uuid>.html`` into a directory served under
``/static/uploads/`` -- same origin, attacker-authored HTML, stored XSS against
every session on the site. And ``delete_file`` joined a caller-supplied object
name straight onto ``UPLOAD_DIR``, which ``os.path.join`` does nothing to
constrain: ``"../../app/core/config.py"`` resolves outside the directory and is
removed.

This module has no FastAPI, SQLAlchemy or boto3 imports on purpose -- it is
pure byte and path handling, so it is cheap to test exhaustively and can be
used from any layer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final, Iterable, Optional

# ---------------------------------------------------------------------------
# Magic-byte signatures
# ---------------------------------------------------------------------------
#
# (offset, signature, media type). Ordered most-specific first: WEBP and the
# various TIFF flavours share prefixes with nothing else here, but RIFF alone
# is also the container for WAV, so WEBP is matched on the full pair.

_SIGNATURES: Final[tuple[tuple[int, bytes, str], ...]] = (
    (0, b"\x89PNG\r\n\x1a\n", "image/png"),
    (0, b"\xff\xd8\xff", "image/jpeg"),
    (0, b"GIF87a", "image/gif"),
    (0, b"GIF89a", "image/gif"),
    (0, b"BM", "image/bmp"),
    (0, b"II*\x00", "image/tiff"),
    (0, b"MM\x00*", "image/tiff"),
    (0, b"%PDF-", "application/pdf"),
    (0, b"PK\x03\x04", "application/zip"),
    (0, b"\x1a\x45\xdf\xa3", "video/webm"),
    (0, b"OggS", "audio/ogg"),
    (0, b"ID3", "audio/mpeg"),
    (0, b"\xff\xfb", "audio/mpeg"),
    (0, b"\xff\xf3", "audio/mpeg"),
    (0, b"\xff\xf2", "audio/mpeg"),
    (0, b"MZ", "application/x-dosexec"),
    (0, b"\x7fELF", "application/x-elf"),
)

#: Signatures that need a second check further into the file, because their
#: leading bytes are a container shared with other formats.
_RIFF_SUBTYPES: Final[dict[bytes, str]] = {
    b"WEBP": "image/webp",
    b"WAVE": "audio/wav",
    b"AVI ": "video/x-msvideo",
}

#: ISO base media file format (MP4 and friends) puts `ftyp` at offset 4.
_FTYP_BRANDS: Final[dict[bytes, str]] = {
    b"qt  ": "video/quicktime",
    b"M4A ": "audio/mp4",
}

#: How many bytes are enough to identify anything above.
SNIFF_LENGTH: Final[int] = 64

#: Media types that are never acceptable as an "image", no matter what the
#: client says or what the extension is. SVG and HTML are script hosts; served
#: from our own origin they are stored XSS. The executables are here so a
#: mislabelled binary is named accurately in the error.
DANGEROUS_TYPES: Final[frozenset[str]] = frozenset(
    {
        "image/svg+xml",
        "text/html",
        "application/xhtml+xml",
        "application/x-dosexec",
        "application/x-elf",
        "application/javascript",
        "application/x-httpd-php",
    }
)

#: The extension we give a file, chosen by its *detected* type.
EXTENSION_FOR_TYPE: Final[dict[str, str]] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "application/pdf": ".pdf",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
}

#: A path segment we are willing to create: one component, no separators, no
#: dots at the edges, nothing that could climb out of a directory.
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class UnsafeUpload(ValueError):
    """The upload is not something we are willing to store."""


class UnsafePath(ValueError):
    """A path argument resolved outside the directory it must stay inside."""


class UploadTooLarge(UnsafeUpload):
    """The payload exceeded the configured limit."""


# ---------------------------------------------------------------------------
# Sniffing
# ---------------------------------------------------------------------------


def _looks_like_markup(head: bytes) -> Optional[str]:
    """Detect SVG/HTML by content.

    Both are text formats with no magic number, and both are dangerous to
    serve from our own origin, so they are worth identifying positively rather
    than falling through to "unknown". Leading whitespace, a BOM, an XML
    declaration or a doctype can all precede the real first tag.
    """
    prefix = head.lstrip(b"\xef\xbb\xbf \t\r\n")[:512].lower()

    if not prefix.startswith(b"<"):
        return None

    if b"<svg" in prefix:
        return "image/svg+xml"

    if prefix.startswith(b"<!doctype html") or b"<html" in prefix:
        return "text/html"

    if prefix.startswith(b"<?php"):
        return "application/x-httpd-php"

    if prefix.startswith(b"<?xml") and b"<svg" in prefix:
        return "image/svg+xml"

    return None


def detect_content_type(data: bytes) -> Optional[str]:
    """The media type of ``data`` according to its bytes, or ``None``.

    ``None`` means "not a format we recognise", which callers treat as "not
    allowed" rather than "probably fine".
    """
    if not data:
        return None

    head = data[:SNIFF_LENGTH]

    # RIFF containers carry their real type at offset 8.
    if head.startswith(b"RIFF") and len(head) >= 12:
        subtype = _RIFF_SUBTYPES.get(head[8:12])
        if subtype:
            return subtype

    # ISO base media: `ftyp` at offset 4, brand at offset 8.
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return _FTYP_BRANDS.get(head[8:12], "video/mp4")

    for offset, signature, media_type in _SIGNATURES:
        if head[offset : offset + len(signature)] == signature:
            return media_type

    return _looks_like_markup(head)


def extension_for(media_type: str, fallback: str = ".bin") -> str:
    """The extension we will store a file of this type under."""
    return EXTENSION_FOR_TYPE.get(media_type, fallback)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

#: Byte sequences we refuse anywhere in the payload.
#:
#: The previous check used `contents.startswith(...)`, which any polyglot
#: defeats by construction -- a valid PNG header followed by `<?php ... ?>`
#: passed. Scanning the whole buffer costs a pass over a few megabytes and
#: catches the case the prefix check was presumably meant to catch.
_EMBEDDED_PATTERNS: Final[tuple[tuple[bytes, str], ...]] = (
    (b"<?php", "embedded PHP"),
    (b"<script", "embedded script tag"),
    (b"javascript:", "javascript: URL"),
    (b"<%@", "embedded server-side include"),
)

#: Executable formats, matched only at the start. Unlike the patterns above
#: these are legitimate byte sequences to find *inside* a media file -- "MZ"
#: is two ASCII letters -- so matching them anywhere produces false positives
#: on ordinary uploads.
_EXECUTABLE_SIGNATURES: Final[tuple[tuple[bytes, str], ...]] = (
    (b"MZ", "Windows executable"),
    (b"\x7fELF", "ELF executable"),
    (b"\xca\xfe\xba\xbe", "Mach-O executable"),
    (b"#!", "shell script"),
)


def scan_bytes(data: bytes, filename: str = "upload") -> None:
    """Reject payloads carrying executable or scriptable content.

    Raises :class:`UnsafeUpload`. This is a heuristic, not an antivirus -- it
    is the cheap layer in front of a real scanner, and the docstring says so
    rather than implying more than it does.
    """
    if not data:
        raise UnsafeUpload(f"{filename} is empty.")

    lowered = data.lower()

    for pattern, description in _EMBEDDED_PATTERNS:
        if pattern in lowered:
            raise UnsafeUpload(
                f"{filename} was rejected: {description} detected in the file."
            )

    for signature, description in _EXECUTABLE_SIGNATURES:
        if data.startswith(signature):
            raise UnsafeUpload(f"{filename} was rejected: it is a {description}.")


# ---------------------------------------------------------------------------
# Combined validation
# ---------------------------------------------------------------------------


def validate_upload_bytes(
    data: bytes,
    allowed_types: Iterable[str],
    filename: str = "upload",
    declared_type: Optional[str] = None,
) -> str:
    """Decide whether ``data`` may be stored, and return its detected type.

    ``declared_type`` -- the client's ``Content-Type`` -- is accepted as an
    argument so it can be reported in the error message when it disagrees with
    reality. It never gets a vote.
    """
    scan_bytes(data, filename)

    detected = detect_content_type(data)

    if detected is None:
        raise UnsafeUpload(
            f"{filename} is not a recognised file format. "
            f"Allowed types: {', '.join(sorted(allowed_types))}."
        )

    if detected in DANGEROUS_TYPES:
        raise UnsafeUpload(f"{filename} is a {detected} file, which cannot be stored.")

    normalised = {t.strip().lower() for t in allowed_types if t and t.strip()}

    if detected not in normalised:
        if declared_type and declared_type.strip().lower() != detected:
            raise UnsafeUpload(
                f"{filename} claims to be {declared_type} but its contents are "
                f"{detected}, which is not an allowed type."
            )

        raise UnsafeUpload(
            f"{filename} is a {detected} file. "
            f"Allowed types: {', '.join(sorted(normalised))}."
        )

    return detected


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def validate_path_segment(segment: str, label: str = "directory") -> str:
    """Assert ``segment`` is a single safe path component and return it.

    Used for the ``directory`` argument that upload callers pass. It ends up
    in ``os.path.join(UPLOAD_DIR, directory)``, which constrains nothing.
    """
    if not segment or not _SAFE_SEGMENT.match(segment):
        raise UnsafePath(
            f"Invalid {label} {segment!r}: expected a single path segment of "
            "letters, digits, hyphens and underscores."
        )

    return segment


def safe_join(base: Path | str, *parts: str) -> Path:
    """Join ``parts`` onto ``base`` and assert the result stays inside it.

    ``os.path.join`` is not a security boundary. It happily produces a path
    outside ``base`` given ``..`` segments, and given an *absolute* second
    argument it discards ``base`` entirely. Both are reachable from a
    caller-supplied object name.

    Resolution is lexical (``os.path.normpath`` semantics via
    ``Path.resolve``) so this works for paths that do not exist yet, which is
    the case on the write path.
    """
    base_path = Path(base).resolve()

    candidate = base_path
    for part in parts:
        if not part:
            continue
        candidate = candidate / part

    resolved = candidate.resolve()

    if resolved != base_path and base_path not in resolved.parents:
        raise UnsafePath(f"Path {'/'.join(parts)!r} resolves outside {base_path}.")

    return resolved
