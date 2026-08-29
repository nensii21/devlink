"""
Tests for ``app.core.storage``.

The existing ``app/tests/core/test_storage.py`` covers the happy paths against
a mocked boto3. This module covers what that one could not: the cases where the
client lies about the file, and the cases where a caller-supplied string is
used as a filesystem path.
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.core import storage as storage_module
from app.core.storage import CloudStorageService, read_upload, scan_file_for_malware

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
HTML = b"<!DOCTYPE html><html><script>alert(document.cookie)</script></html>"
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>'


def make_upload(
    content: bytes,
    filename: str = "avatar.png",
    content_type: str = "image/png",
) -> UploadFile:
    """An UploadFile backed by an in-memory buffer."""
    upload = UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )
    return upload


@pytest.fixture()
def local_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A storage service writing into a temp directory."""
    monkeypatch.setattr(storage_module.settings, "STORAGE_PROVIDER", "local")
    monkeypatch.setattr(storage_module.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(
        storage_module.settings, "ALLOWED_IMAGE_TYPES", "image/png,image/jpeg"
    )
    monkeypatch.setattr(storage_module.settings, "MAX_UPLOAD_SIZE_MB", 5)

    return CloudStorageService()


# ---------------------------------------------------------------------------
# Content validation
# ---------------------------------------------------------------------------


def test_a_real_png_uploads(local_service, tmp_path: Path) -> None:
    key = local_service.upload_file(make_upload(PNG), directory="avatars")

    assert key.startswith("avatars/")
    assert key.endswith(".png")
    assert (tmp_path / key).read_bytes() == PNG


def test_html_declared_as_png_is_rejected(local_service, tmp_path: Path) -> None:
    """The central defect: validation was reading the client's header.

    Serving attacker-authored HTML from our own origin under
    ``/static/uploads/`` is stored XSS against every session on the site.
    """
    with pytest.raises(HTTPException) as exc:
        local_service.upload_file(make_upload(HTML, "avatar.png", "image/png"))

    assert exc.value.status_code == 400
    assert not list(tmp_path.rglob("*.html"))
    assert not list(tmp_path.rglob("*.png"))


def test_svg_declared_as_png_is_rejected(local_service) -> None:
    with pytest.raises(HTTPException) as exc:
        local_service.upload_file(make_upload(SVG, "logo.png", "image/png"))

    assert exc.value.status_code == 400


def test_the_stored_extension_comes_from_the_content(local_service) -> None:
    """A JPEG named ``.png`` is stored as ``.jpg``.

    The extension used to be copied out of the client's filename, which is how
    ``x.html`` declared as ``image/png`` became ``<uuid>.html``.
    """
    key = local_service.upload_file(make_upload(JPEG, "mislabelled.png", "image/png"))

    assert key.endswith(".jpg")


def test_an_executable_named_png_is_rejected(local_service) -> None:
    with pytest.raises(HTTPException) as exc:
        local_service.upload_file(
            make_upload(b"MZ\x90\x00" + b"\x00" * 64, "avatar.png", "image/png")
        )

    assert exc.value.status_code == 400


def test_a_polyglot_is_rejected(local_service) -> None:
    """Sniffs as a PNG; the whole-buffer scan is what catches it."""
    with pytest.raises(HTTPException):
        local_service.upload_file(
            make_upload(PNG + b"<?php system($_GET['c']); ?>", "avatar.png")
        )


def test_the_allowlist_is_case_insensitive(
    local_service, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(storage_module.settings, "ALLOWED_IMAGE_TYPES", "IMAGE/PNG")

    key = local_service.upload_file(make_upload(PNG))

    assert key.endswith(".png")


# ---------------------------------------------------------------------------
# Size
# ---------------------------------------------------------------------------


def test_an_oversized_upload_is_rejected(
    local_service, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(storage_module.settings, "MAX_UPLOAD_SIZE_MB", 1)

    with pytest.raises(HTTPException) as exc:
        local_service.upload_file(make_upload(PNG + b"\x00" * (2 * 1024 * 1024)))

    assert exc.value.status_code == 413


def test_the_size_limit_holds_without_a_declared_length(
    local_service, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``UploadFile.size`` is ``None`` for a chunked upload.

    The old check was ``if file.size and file.size > limit``, so an undeclared
    length short-circuited past it and the next line read the whole body into
    memory.
    """
    monkeypatch.setattr(storage_module.settings, "MAX_UPLOAD_SIZE_MB", 1)

    upload = make_upload(PNG + b"\x00" * (2 * 1024 * 1024))
    assert upload.size is None  # no content-length was set

    with pytest.raises(HTTPException) as exc:
        local_service.upload_file(upload)

    assert exc.value.status_code == 413


def test_read_upload_stops_reading_past_the_limit() -> None:
    """The body is abandoned, not buffered in full and then measured."""
    upload = make_upload(b"\x00" * (1024 * 1024))

    with pytest.raises(storage_module.UploadTooLarge):
        read_upload(upload, max_bytes=1024)


def test_an_empty_upload_is_rejected(local_service) -> None:
    with pytest.raises(HTTPException) as exc:
        local_service.upload_file(make_upload(b""))

    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "directory",
    ["../escape", "..", "a/b", "/etc", ".hidden", ""],
)
def test_a_dangerous_directory_is_rejected(local_service, directory: str) -> None:
    with pytest.raises(HTTPException) as exc:
        local_service.upload_file(make_upload(PNG), directory=directory)

    assert exc.value.status_code == 400


def test_delete_refuses_to_escape_the_upload_directory(
    local_service, tmp_path: Path
) -> None:
    """This was an arbitrary-file-delete primitive.

    ``os.path.join(UPLOAD_DIR, object_name)`` constrains nothing, and several
    endpoints forward a stored key from request data straight into it.
    """
    victim = tmp_path.parent / "important.txt"
    victim.write_text("do not delete me")

    with pytest.raises(HTTPException) as exc:
        local_service.delete_file("../important.txt")

    assert exc.value.status_code == 400
    assert victim.exists()
    assert victim.read_text() == "do not delete me"


def test_delete_refuses_an_absolute_object_name(local_service, tmp_path: Path) -> None:
    """An absolute second argument makes ``join`` discard the base entirely."""
    victim = tmp_path.parent / "absolute-target.txt"
    victim.write_text("still here")

    with pytest.raises(HTTPException):
        local_service.delete_file(str(victim))

    assert victim.exists()


def test_delete_removes_a_file_inside_the_upload_directory(
    local_service, tmp_path: Path
) -> None:
    key = local_service.upload_file(make_upload(PNG), directory="avatars")
    assert (tmp_path / key).exists()

    assert local_service.delete_file(key) is True
    assert not (tmp_path / key).exists()


def test_delete_returns_false_for_a_missing_file(local_service) -> None:
    assert local_service.delete_file("avatars/does-not-exist.png") is False


def test_uploads_do_not_collide(local_service, tmp_path: Path) -> None:
    first = local_service.upload_file(make_upload(PNG), directory="avatars")
    second = local_service.upload_file(make_upload(PNG), directory="avatars")

    assert first != second
    assert len(list((tmp_path / "avatars").iterdir())) == 2


# ---------------------------------------------------------------------------
# Cloud provider
# ---------------------------------------------------------------------------


@pytest.fixture()
def s3_service(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(storage_module.settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(storage_module.settings, "AWS_BUCKET_NAME", "bucket")
    monkeypatch.setattr(
        storage_module.settings, "ALLOWED_IMAGE_TYPES", "image/png,image/jpeg"
    )
    monkeypatch.setattr(storage_module.settings, "MAX_UPLOAD_SIZE_MB", 5)

    with patch("app.core.storage.boto3") as boto3_mock:
        client = MagicMock()
        boto3_mock.client.return_value = client
        service = CloudStorageService()
        yield service, client


def test_s3_objects_are_tagged_with_the_detected_type(s3_service) -> None:
    """Not the client's header -- the CDN would serve it as whatever was
    claimed."""
    service, client = s3_service

    service.upload_file(make_upload(JPEG, "avatar.png", "image/png"))

    kwargs = client.put_object.call_args.kwargs
    assert kwargs["ContentType"] == "image/jpeg"


def test_s3_objects_are_stored_as_attachments(s3_service) -> None:
    """Defence in depth: anything that slips through downloads rather than
    rendering in the origin's context."""
    service, client = s3_service

    service.upload_file(make_upload(PNG))

    assert client.put_object.call_args.kwargs["ContentDisposition"] == "attachment"


def test_a_presigned_url_failure_raises_instead_of_returning_empty(
    s3_service,
) -> None:
    """Returning ``""`` rendered as ``<img src="">`` and logged nothing at the
    call site, so a misconfigured bucket looked like a missing image."""
    from botocore.exceptions import ClientError

    service, client = s3_service
    client.generate_presigned_url.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "GetObject"
    )

    with pytest.raises(HTTPException) as exc:
        service.generate_presigned_url("avatars/x.png")

    assert exc.value.status_code == 500


# ---------------------------------------------------------------------------
# The scanner shim
# ---------------------------------------------------------------------------


def test_scan_file_for_malware_still_raises_value_error() -> None:
    """Existing callers catch ``ValueError``; that contract is unchanged."""
    with pytest.raises(ValueError):
        scan_file_for_malware(b"MZ\x90\x00", "x.png")

    with pytest.raises(ValueError):
        scan_file_for_malware(b"", "x.png")


def test_scan_file_for_malware_now_scans_the_whole_buffer() -> None:
    """The old version only checked ``startswith``."""
    with pytest.raises(ValueError):
        scan_file_for_malware(PNG + b"<?php echo 1; ?>", "x.png")


# ---------------------------------------------------------------------------
# Async wrappers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_file_async_runs_off_the_event_loop(
    local_service, tmp_path: Path
) -> None:
    key = await local_service.upload_file_async(make_upload(PNG), directory="avatars")

    assert (tmp_path / key).exists()


@pytest.mark.asyncio
async def test_delete_file_async_runs_off_the_event_loop(
    local_service, tmp_path: Path
) -> None:
    key = await local_service.upload_file_async(make_upload(PNG), directory="avatars")

    assert await local_service.delete_file_async(key) is True
    assert not (tmp_path / key).exists()
