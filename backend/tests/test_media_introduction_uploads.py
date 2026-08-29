"""
Tests for the voice- and video-introduction upload helpers.

These two features were developed on separate branches (#977 and #978) that
both edited the same three files, and the merge interleaved them: one save
helper was consumed by the next ``def``, one endpoint lost its body entirely,
and one wrote to the video directory but returned a voice URL.

The point of this module is that the two paths are exercised *independently*.
The merge damage was only possible because nothing asserted that a voice
upload lands somewhere different from a video upload, so a function that did
half of each still looked correct.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.utils import uploads
from app.utils.uploads import (
    MAX_VIDEO_SIZE_BYTES,
    MAX_VOICE_SIZE_BYTES,
    save_image_upload,
    save_resume_upload,
    save_video_introduction_upload,
    save_voice_introduction_upload,
    scan_file_for_malware,
    validate_image_upload,
    validate_resume_upload,
    validate_video_introduction_upload,
    validate_voice_introduction_upload,
)


@pytest.fixture()
def upload_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``UPLOAD_DIR`` at a temp directory for the duration of a test."""
    monkeypatch.setattr(uploads.settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def user_id() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Voice introductions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("intro.mp3", "audio/mpeg"),
        ("intro.wav", "audio/wav"),
        ("intro.webm", "audio/webm"),
        ("intro.ogg", "audio/ogg"),
    ],
)
def test_valid_voice_uploads_are_accepted(filename: str, content_type: str) -> None:
    validate_voice_introduction_upload(filename, content_type, 1024)


def test_voice_upload_rejects_unknown_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported audio format"):
        validate_voice_introduction_upload("intro.aiff", "audio/mpeg", 1024)


def test_voice_upload_rejects_mismatched_content_type() -> None:
    with pytest.raises(ValueError, match="valid audio file"):
        validate_voice_introduction_upload("intro.mp3", "video/mp4", 1024)


def test_voice_upload_rejects_missing_filename() -> None:
    with pytest.raises(ValueError, match="upload an audio file"):
        validate_voice_introduction_upload(None, "audio/mpeg", 1024)


def test_voice_upload_enforces_its_own_size_limit() -> None:
    validate_voice_introduction_upload("intro.mp3", "audio/mpeg", MAX_VOICE_SIZE_BYTES)

    with pytest.raises(ValueError, match="smaller than 10MB"):
        validate_voice_introduction_upload(
            "intro.mp3", "audio/mpeg", MAX_VOICE_SIZE_BYTES + 1
        )


def test_saving_a_voice_upload_writes_to_the_voice_directory(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    url = save_voice_introduction_upload(b"RIFFfake-wav-bytes", "intro.wav", user_id)

    assert url.startswith("/uploads/voice_introductions/")

    written = upload_root / "voice_introductions"
    files = list(written.iterdir())
    assert len(files) == 1
    assert files[0].read_bytes() == b"RIFFfake-wav-bytes"

    # The returned URL has to name the file that was actually written. The
    # merged version wrote to voice_introductions/ and returned a
    # video_introductions/ URL, so every saved clip 404'd.
    assert url.endswith(files[0].name)


def test_voice_upload_preserves_the_source_extension(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    url = save_voice_introduction_upload(b"fake-ogg", "Recording.OGG", user_id)
    assert url.endswith(".ogg")


def test_voice_filename_is_not_taken_from_the_client(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    """The stored name is ours; only the extension comes from the upload."""
    url = save_voice_introduction_upload(b"fake", "../../escape.mp3", user_id)

    assert ".." not in url
    assert url.startswith(f"/uploads/voice_introductions/{user_id}-")


# ---------------------------------------------------------------------------
# Video introductions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("intro.mp4", "video/mp4"),
        ("intro.webm", "video/webm"),
        ("intro.mov", "video/quicktime"),
    ],
)
def test_valid_video_uploads_are_accepted(filename: str, content_type: str) -> None:
    validate_video_introduction_upload(filename, content_type, 1024)


def test_video_upload_rejects_unknown_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported video format"):
        validate_video_introduction_upload("intro.avi", "video/mp4", 1024)


def test_video_upload_rejects_mismatched_content_type() -> None:
    with pytest.raises(ValueError, match="valid video file"):
        validate_video_introduction_upload("intro.mp4", "audio/mpeg", 1024)


def test_video_upload_has_a_larger_budget_than_an_image() -> None:
    """Videos were sharing the image size limit, which rejected real clips.

    The specific number is configurable; what matters is that a video is
    allowed to be meaningfully larger than a profile picture.
    """
    assert MAX_VIDEO_SIZE_BYTES > uploads.MAX_IMAGE_SIZE_BYTES

    validate_video_introduction_upload("intro.mp4", "video/mp4", MAX_VIDEO_SIZE_BYTES)

    with pytest.raises(ValueError, match="Video file must be smaller"):
        validate_video_introduction_upload(
            "intro.mp4", "video/mp4", MAX_VIDEO_SIZE_BYTES + 1
        )


def test_saving_a_video_upload_writes_to_the_video_directory(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    url = save_video_introduction_upload(b"fake-mp4-bytes", "intro.mp4", user_id)

    assert url.startswith("/uploads/video_introductions/")

    written = upload_root / "video_introductions"
    files = list(written.iterdir())
    assert len(files) == 1
    assert files[0].read_bytes() == b"fake-mp4-bytes"
    assert url.endswith(files[0].name)


def test_voice_and_video_do_not_share_a_directory(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    """The regression test for the merge itself.

    Both helpers previously resolved to the same directory, so a voice clip and
    a video clip landed in the same place under URLs that disagreed with where
    they were written.
    """
    voice_url = save_voice_introduction_upload(b"audio", "a.mp3", user_id)
    video_url = save_video_introduction_upload(b"video", "v.mp4", user_id)

    assert "voice_introductions" in voice_url
    assert "video_introductions" in video_url

    voice_files = list((upload_root / "voice_introductions").iterdir())
    video_files = list((upload_root / "video_introductions").iterdir())

    assert len(voice_files) == 1
    assert len(video_files) == 1
    assert voice_files[0].read_bytes() == b"audio"
    assert video_files[0].read_bytes() == b"video"


def test_each_upload_gets_a_unique_name(upload_root: Path, user_id: uuid.UUID) -> None:
    """Two uploads of the same filename must not overwrite each other."""
    first = save_video_introduction_upload(b"one", "intro.mp4", user_id)
    second = save_video_introduction_upload(b"two", "intro.mp4", user_id)

    assert first != second
    assert len(list((upload_root / "video_introductions").iterdir())) == 2


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------


def test_resume_validation_accepts_pdf_and_docx() -> None:
    validate_resume_upload("cv.pdf", "application/pdf", 1024)
    validate_resume_upload(
        "cv.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        1024,
    )


def test_resume_validation_rejects_other_formats() -> None:
    with pytest.raises(ValueError, match="PDF or DOCX"):
        validate_resume_upload("cv.txt", "text/plain", 1024)


def test_a_docx_resume_keeps_its_docx_extension(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    """A DOCX was being stored as ``.pdf`` and would not open on download."""
    url = save_resume_upload(b"PK\x03\x04docx-bytes", "cv.docx", user_id)

    assert url.endswith(".docx")
    assert (upload_root / "resumes" / Path(url).name).exists()


def test_a_pdf_resume_keeps_its_pdf_extension(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    url = save_resume_upload(b"%PDF-1.7 bytes", "cv.pdf", user_id)
    assert url.endswith(".pdf")


def test_an_unexpected_resume_extension_falls_back_to_pdf(
    upload_root: Path, user_id: uuid.UUID
) -> None:
    """``save_`` is only reachable after ``validate_``, but it does not trust
    that -- an unknown extension is normalised rather than written through."""
    url = save_resume_upload(b"bytes", "cv.exe", user_id)
    assert url.endswith(".pdf")


# ---------------------------------------------------------------------------
# The shared scanner
# ---------------------------------------------------------------------------


def test_scanner_rejects_an_empty_payload() -> None:
    with pytest.raises(ValueError, match="empty"):
        scan_file_for_malware(b"", "empty.mp3")


@pytest.mark.parametrize("signature", [b"<?php", b"<script", b"MZ", b"\x7fELF"])
def test_scanner_rejects_known_signatures(signature: bytes) -> None:
    with pytest.raises(ValueError, match="Prohibited file signature"):
        scan_file_for_malware(signature + b" trailing", "payload.mp3")


def test_scanner_allows_ordinary_media_bytes() -> None:
    scan_file_for_malware(b"\x00\x00\x00\x18ftypmp42", "intro.mp4")
    scan_file_for_malware(b"RIFF\x24\x08\x00\x00WAVE", "intro.wav")


def test_saving_runs_the_scanner(upload_root: Path, user_id: uuid.UUID) -> None:
    """The scan is not optional on the way to disk."""
    with pytest.raises(ValueError, match="Prohibited file signature"):
        save_video_introduction_upload(b"MZ\x90\x00", "intro.mp4", user_id)

    assert not (upload_root / "video_introductions").exists() or not list(
        (upload_root / "video_introductions").iterdir()
    )


# ---------------------------------------------------------------------------
# Images -- unchanged behaviour, covered so the shared helpers stay honest
# ---------------------------------------------------------------------------


def test_image_validation_rejects_an_unknown_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported file extension"):
        validate_image_upload("avatar.svg", "image/svg+xml", 1024)


def test_image_validation_rejects_a_non_image_content_type() -> None:
    with pytest.raises(ValueError, match="valid image file"):
        validate_image_upload("avatar.png", "application/pdf", 1024)


def test_image_validation_accepts_a_png() -> None:
    validate_image_upload("avatar.png", "image/png", 1024)


def test_save_image_upload_is_importable() -> None:
    """``users.py`` imports it; the merge left that import intact but the
    module unparseable, so nothing proved it resolved."""
    assert callable(save_image_upload)
