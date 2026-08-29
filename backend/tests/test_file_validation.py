"""
Tests for ``app.core.file_validation``.

Pure byte and path handling, so these run with no fixtures, no database and no
FastAPI app. The two behaviours worth being exhaustive about are the ones that
were exploitable: a file that lies about what it is, and a path that climbs out
of the directory it was supposed to stay in.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.file_validation import (
    DANGEROUS_TYPES,
    SNIFF_LENGTH,
    UnsafePath,
    UnsafeUpload,
    detect_content_type,
    extension_for,
    safe_join,
    scan_bytes,
    validate_path_segment,
    validate_upload_bytes,
)

# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
GIF = b"GIF89a" + b"\x00" * 32
BMP = b"BM" + b"\x00" * 32
TIFF_LE = b"II*\x00" + b"\x00" * 32
TIFF_BE = b"MM\x00*" + b"\x00" * 32
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 16
WAV = b"RIFF\x24\x08\x00\x00WAVEfmt " + b"\x00" * 16
MP4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 16
MOV = b"\x00\x00\x00\x14ftypqt  " + b"\x00" * 16
WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 32
MP3 = b"ID3\x03\x00\x00\x00" + b"\x00" * 32
OGG = b"OggS\x00\x02" + b"\x00" * 32
PDF = b"%PDF-1.7\n" + b"\x00" * 32
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>'
HTML = b"<!DOCTYPE html><html><body>hi</body></html>"
ELF = b"\x7fELF\x02\x01\x01" + b"\x00" * 32
EXE = b"MZ\x90\x00\x03" + b"\x00" * 32

IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (PNG, "image/png"),
        (JPEG, "image/jpeg"),
        (GIF, "image/gif"),
        (BMP, "image/bmp"),
        (TIFF_LE, "image/tiff"),
        (TIFF_BE, "image/tiff"),
        (WEBP, "image/webp"),
        (WAV, "audio/wav"),
        (MP4, "video/mp4"),
        (MOV, "video/quicktime"),
        (WEBM, "video/webm"),
        (MP3, "audio/mpeg"),
        (OGG, "audio/ogg"),
        (PDF, "application/pdf"),
        (SVG, "image/svg+xml"),
        (HTML, "text/html"),
        (ELF, "application/x-elf"),
        (EXE, "application/x-dosexec"),
    ],
)
def test_detection_reads_the_bytes(payload: bytes, expected: str) -> None:
    assert detect_content_type(payload) == expected


def test_riff_is_not_assumed_to_be_webp() -> None:
    """RIFF is a container. WAV and WEBP share the first four bytes."""
    assert detect_content_type(WEBP) == "image/webp"
    assert detect_content_type(WAV) == "audio/wav"


def test_detection_returns_none_for_unknown_bytes() -> None:
    assert detect_content_type(b"just some plain text, no signature") is None


def test_detection_returns_none_for_empty_input() -> None:
    assert detect_content_type(b"") is None


def test_detection_needs_only_the_head_of_the_file() -> None:
    assert detect_content_type(PNG[:SNIFF_LENGTH]) == "image/png"


@pytest.mark.parametrize(
    "prefix",
    [b"", b"  \n\t", b"\xef\xbb\xbf", b'<?xml version="1.0"?>'],
)
def test_svg_is_detected_behind_leading_noise(prefix: bytes) -> None:
    """Whitespace, a BOM or an XML declaration can all precede the real tag."""
    assert detect_content_type(prefix + SVG) == "image/svg+xml"


def test_extension_follows_the_detected_type() -> None:
    assert extension_for("image/png") == ".png"
    assert extension_for("image/jpeg") == ".jpg"
    assert extension_for("video/quicktime") == ".mov"


def test_extension_falls_back_for_an_unmapped_type() -> None:
    assert extension_for("application/x-whatever") == ".bin"


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def test_scan_rejects_empty_payloads() -> None:
    with pytest.raises(UnsafeUpload, match="empty"):
        scan_bytes(b"", "empty.png")


def test_scan_catches_a_payload_embedded_after_a_valid_header() -> None:
    """The whole point of scanning the buffer instead of its prefix.

    ``startswith`` was trivially defeated by exactly this construction: a
    real PNG header followed by whatever you wanted.
    """
    polyglot = PNG + b"<?php system($_GET['c']); ?>"

    with pytest.raises(UnsafeUpload, match="embedded PHP"):
        scan_bytes(polyglot, "avatar.png")


def test_scan_catches_a_script_tag_anywhere_in_the_file() -> None:
    with pytest.raises(UnsafeUpload, match="script tag"):
        scan_bytes(GIF + b"\n<script>alert(1)</script>", "x.gif")


def test_scan_is_case_insensitive() -> None:
    with pytest.raises(UnsafeUpload, match="script tag"):
        scan_bytes(GIF + b"<SCRIPT>alert(1)</SCRIPT>", "x.gif")


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (EXE, "Windows executable"),
        (ELF, "ELF executable"),
        (b"#!/bin/sh\necho hi", "shell script"),
    ],
)
def test_scan_rejects_executables(payload: bytes, match: str) -> None:
    with pytest.raises(UnsafeUpload, match=match):
        scan_bytes(payload, "thing")


def test_scan_allows_ordinary_media() -> None:
    for payload in (PNG, JPEG, GIF, WEBP, MP4, MP3, PDF):
        scan_bytes(payload, "file")


def test_executable_signatures_are_only_matched_at_the_start() -> None:
    """ "MZ" is two ASCII letters and appears in ordinary binary data.

    Matching it anywhere would reject legitimate uploads.
    """
    scan_bytes(PNG + b"some MZ bytes in the middle", "avatar.png")


# ---------------------------------------------------------------------------
# Combined validation
# ---------------------------------------------------------------------------


def test_a_real_png_is_accepted() -> None:
    assert validate_upload_bytes(PNG, IMAGE_TYPES, "a.png", "image/png") == "image/png"


def test_the_declared_content_type_does_not_decide() -> None:
    """The attack the old allowlist could not see.

    Upload HTML, declare `image/png`, and the header-based check passed.
    """
    with pytest.raises(UnsafeUpload) as exc:
        validate_upload_bytes(HTML, IMAGE_TYPES, "avatar.png", "image/png")

    assert "text/html" in str(exc.value)


def test_an_svg_declared_as_png_is_rejected() -> None:
    with pytest.raises(UnsafeUpload):
        validate_upload_bytes(SVG, IMAGE_TYPES, "avatar.png", "image/png")


def test_svg_is_rejected_even_when_explicitly_allowed() -> None:
    """SVG is a script host. Allowing it by configuration is still stored XSS."""
    assert "image/svg+xml" in DANGEROUS_TYPES

    with pytest.raises(UnsafeUpload, match="cannot be stored"):
        validate_upload_bytes(
            SVG, IMAGE_TYPES | {"image/svg+xml"}, "logo.svg", "image/svg+xml"
        )


def test_html_is_rejected_even_when_explicitly_allowed() -> None:
    with pytest.raises(UnsafeUpload, match="cannot be stored"):
        validate_upload_bytes(
            HTML, IMAGE_TYPES | {"text/html"}, "page.html", "text/html"
        )


def test_a_disallowed_but_harmless_type_is_rejected_clearly() -> None:
    with pytest.raises(UnsafeUpload) as exc:
        validate_upload_bytes(PDF, IMAGE_TYPES, "doc.pdf", "application/pdf")

    assert "application/pdf" in str(exc.value)


def test_unrecognised_bytes_are_rejected_rather_than_assumed_fine() -> None:
    with pytest.raises(UnsafeUpload, match="not a recognised file format"):
        validate_upload_bytes(b"hello there", IMAGE_TYPES, "x.png", "image/png")


def test_the_allowlist_comparison_is_case_insensitive() -> None:
    """`IMAGE/PNG` in configuration was rejecting perfectly good PNGs."""
    assert validate_upload_bytes(PNG, {"IMAGE/PNG"}, "a.png", "image/png") == (
        "image/png"
    )


def test_a_polyglot_is_caught_before_type_detection() -> None:
    """It sniffs as a PNG; the scan is what stops it."""
    polyglot = PNG + b"<?php echo 1; ?>"
    assert detect_content_type(polyglot) == "image/png"

    with pytest.raises(UnsafeUpload, match="embedded PHP"):
        validate_upload_bytes(polyglot, IMAGE_TYPES, "avatar.png", "image/png")


# ---------------------------------------------------------------------------
# Path segments
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("segment", ["general", "avatars", "user_123", "a-b-c", "x"])
def test_ordinary_segments_are_accepted(segment: str) -> None:
    assert validate_path_segment(segment) == segment


@pytest.mark.parametrize(
    "segment",
    [
        "",
        "..",
        "../etc",
        "a/b",
        "a\\b",
        "/absolute",
        ".hidden",
        "-leading-hyphen",
        "with space",
        "x" * 100,
        "nul\x00byte",
    ],
)
def test_dangerous_segments_are_rejected(segment: str) -> None:
    with pytest.raises(UnsafePath):
        validate_path_segment(segment)


# ---------------------------------------------------------------------------
# safe_join
# ---------------------------------------------------------------------------


def test_safe_join_builds_a_path_inside_the_base(tmp_path: Path) -> None:
    result = safe_join(tmp_path, "avatars", "abc.png")

    assert result == (tmp_path / "avatars" / "abc.png").resolve()


def test_safe_join_works_for_paths_that_do_not_exist_yet(tmp_path: Path) -> None:
    """Resolution has to be lexical -- this runs on the write path."""
    result = safe_join(tmp_path, "brand", "new", "file.png")
    assert not result.exists()
    assert str(result).startswith(str(tmp_path.resolve()))


@pytest.mark.parametrize(
    "parts",
    [
        ("..", "escaped.txt"),
        ("..", "..", "etc", "passwd"),
        ("avatars", "..", "..", "secret.py"),
        ("a", "..", "..", "..", "b"),
    ],
)
def test_safe_join_refuses_to_climb_out(tmp_path: Path, parts) -> None:
    base = tmp_path / "uploads"
    base.mkdir()

    with pytest.raises(UnsafePath):
        safe_join(base, *parts)


def test_safe_join_is_not_fooled_by_the_dot_stripping_bypass(tmp_path: Path) -> None:
    """``....//`` defeats sanitisers that *remove* occurrences of ``../``.

    It does nothing here, because containment is decided by resolving the path
    and comparing, not by rewriting the string. ``....`` is simply an
    oddly-named directory inside the base, so this is allowed -- and staying
    inside is the property that matters.
    """
    base = tmp_path / "uploads"
    base.mkdir()

    result = safe_join(base, "....//", "file.txt")

    assert base.resolve() in result.parents


def test_safe_join_refuses_an_absolute_component(tmp_path: Path) -> None:
    """`Path("/a") / "/etc/passwd"` discards the base entirely.

    So does `os.path.join`. This is reachable from a caller-supplied object
    name.
    """
    base = tmp_path / "uploads"
    base.mkdir()

    with pytest.raises(UnsafePath):
        safe_join(base, "/etc/passwd")


def test_safe_join_allows_the_base_itself(tmp_path: Path) -> None:
    assert safe_join(tmp_path) == tmp_path.resolve()


def test_safe_join_ignores_empty_components(tmp_path: Path) -> None:
    assert safe_join(tmp_path, "", "a.png") == (tmp_path / "a.png").resolve()
