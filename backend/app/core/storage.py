import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.file_validation import (
    UnsafePath,
    UnsafeUpload,
    UploadTooLarge,
    detect_content_type,
    extension_for,
    safe_join,
    scan_bytes,
    validate_path_segment,
    validate_upload_bytes,
)

logger = logging.getLogger(__name__)

#: Read the upload in chunks so an oversized body is abandoned partway rather
#: than buffered in full before anyone checks its size.
CHUNK_SIZE = 64 * 1024


def scan_file_for_malware(contents: bytes, filename: str) -> None:
    """Reject uploads carrying executable or scriptable content.

    Kept as a module-level function because callers import it by this name.
    The implementation now lives in :mod:`app.core.file_validation` and scans
    the whole payload rather than only its first few bytes.

    ``app/utils/uploads.py`` still carries its own copy of the old prefix-only
    version. Consolidating the two is deliberately left out of this change so
    it does not collide with the repair in #1199, which rewrites large parts of
    that file; once that lands it is a one-line import swap.
    """
    try:
        scan_bytes(contents, filename)
    except UnsafeUpload as exc:
        # Callers have always caught ValueError here, and UnsafeUpload is one.
        raise ValueError(str(exc)) from exc


def _allowed_image_types() -> set[str]:
    """The configured image allowlist, parsed once per call and normalised.

    Previously re-split on every validation without lowercasing either side,
    so a perfectly good ``IMAGE/PNG`` was rejected.
    """
    return {
        media_type.strip().lower()
        for media_type in settings.ALLOWED_IMAGE_TYPES.split(",")
        if media_type.strip()
    }


def _max_upload_bytes() -> int:
    return settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def read_upload(file: UploadFile, max_bytes: Optional[int] = None) -> bytes:
    """Read an upload, enforcing the size limit as we go.

    The previous code checked ``file.size`` and then read the whole body::

        if file.size and file.size > limit:   # `size` is often None
            raise ...
        file_bytes = file.file.read()         # unbounded

    ``UploadFile.size`` comes from the part's ``Content-Length``. A chunked
    upload -- or a client that simply omits the header -- leaves it ``None``,
    the ``and`` short-circuits, and the limit never runs. The next line then
    pulls the entire body into memory. A handful of concurrent large uploads
    is an OOM, prevented by a check that did not execute.

    Reading in bounded chunks means the limit holds whether or not the client
    declared a length, and an oversized body is abandoned after one chunk past
    the limit rather than after all of it.
    """
    limit = _max_upload_bytes() if max_bytes is None else max_bytes

    chunks: list[bytes] = []
    total = 0

    file.file.seek(0)

    while True:
        chunk = file.file.read(CHUNK_SIZE)
        if not chunk:
            break

        total += len(chunk)
        if total > limit:
            raise UploadTooLarge(
                f"File size exceeds maximum limit of " f"{limit // (1024 * 1024)}MB"
            )

        chunks.append(chunk)

    if total == 0:
        raise UnsafeUpload("Uploaded file is empty.")

    return b"".join(chunks)


class CloudStorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER.lower()
        self.bucket_name = settings.AWS_BUCKET_NAME
        self.client = None

        if self.provider in ["s3", "r2"]:
            if not self.bucket_name:
                logger.warning("AWS_BUCKET_NAME is not set, cloud storage may fail.")

            endpoint_url = None
            if self.provider == "r2":
                if not settings.R2_ACCOUNT_ID:
                    logger.warning("R2_ACCOUNT_ID is not set for Cloudflare R2.")
                else:
                    endpoint_url = (
                        f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
                    )

            self.client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION if settings.AWS_REGION else "auto",
            )
        elif self.provider == "local":
            logger.info("Storage provider is set to local. S3 client not initialized.")
        else:
            logger.error(f"Unknown storage provider: {self.provider}")

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    @property
    def upload_root(self) -> Path:
        """The directory local uploads may never escape."""
        return Path(settings.UPLOAD_DIR).resolve()

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_file(self, file: UploadFile, directory: str = "general") -> str:
        """Validate and store an upload. Returns the object key.

        The file's type is determined by sniffing its bytes. The client's
        ``Content-Type`` header is reported in the error when the two
        disagree, but it does not decide anything -- an attacker writes that
        header, so an allowlist checked against it is an allowlist checked
        against the attacker.
        """
        # `directory` is joined onto the upload root, and `os.path.join`
        # constrains nothing.
        try:
            safe_directory = validate_path_segment(directory, "directory")
        except UnsafePath as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        try:
            file_bytes = read_upload(file)
        except UploadTooLarge as exc:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(exc),
            ) from exc
        except UnsafeUpload as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            logger.error(f"Failed to read upload stream: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to read uploaded file contents.",
            ) from exc

        try:
            detected_type = validate_upload_bytes(
                file_bytes,
                allowed_types=_allowed_image_types(),
                filename=file.filename or "upload",
                declared_type=file.content_type,
            )
        except UnsafeUpload as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        # The extension follows what the file *is*, not what it was called.
        # Copying the client's extension is how `x.html` declared as
        # `image/png` became `<uuid>.html` under a directory we serve.
        filename = f"{uuid.uuid4().hex}{extension_for(detected_type)}"
        object_name = f"{safe_directory}/{filename}"

        if self.provider == "local":
            destination = safe_join(self.upload_root, safe_directory, filename)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(file_bytes)

            return object_name

        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud storage client is not properly initialized.",
            )

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_bytes,
                # The detected type, so the CDN serves it as what it is.
                ContentType=detected_type,
                # Belt and braces: even if something slips through, the object
                # downloads instead of rendering in the origin's context.
                ContentDisposition="attachment",
            )
            return object_name
        except ClientError as exc:
            logger.error(f"Error uploading file to {self.provider}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to cloud storage.",
            ) from exc

    async def upload_file_async(
        self, file: UploadFile, directory: str = "general"
    ) -> str:
        """:meth:`upload_file` off the event loop.

        Reading the body, hashing it, writing it to disk and `put_object` are
        all synchronous and were being called directly from `async def`
        endpoints, blocking every other request on the worker for the duration
        of the upload.
        """
        return await asyncio.to_thread(self.upload_file, file, directory)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """A URL the client can fetch the object from.

        Raises on failure rather than returning ``""``. An empty string
        rendered as ``<img src="">`` on the page and logged nothing at the
        call site, so a misconfigured bucket looked like a missing image.
        """
        if self.provider == "local":
            if settings.CDN_BASE_URL:
                return f"{settings.CDN_BASE_URL}/{object_name}"
            return f"/static/uploads/{object_name}"

        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud storage client is not properly initialized.",
            )

        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
        except ClientError as exc:
            logger.error(f"Error generating presigned URL: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate a download URL.",
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_file(self, object_name: str) -> bool:
        """Delete a stored object.

        ``object_name`` reaches this from request data in several places, and
        the local branch used to do::

            file_path = os.path.join(settings.UPLOAD_DIR, object_name)
            if os.path.exists(file_path):
                os.remove(file_path)

        ``os.path.join`` does not constrain anything: ``"../../app/main.py"``
        resolves outside ``UPLOAD_DIR`` and is deleted, and an *absolute*
        object name discards ``UPLOAD_DIR`` altogether. Any endpoint
        forwarding a caller-supplied key here was an arbitrary-file-delete
        primitive.
        """
        if self.provider == "local":
            try:
                file_path = safe_join(self.upload_root, *Path(object_name).parts)
            except UnsafePath as exc:
                logger.warning("Refusing to delete outside upload dir: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid object name.",
                ) from exc

            if file_path.is_file():
                file_path.unlink()
                return True
            return False

        if not self.client:
            return False

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as exc:
            logger.error(f"Error deleting file from {self.provider}: {exc}")
            return False

    async def delete_file_async(self, object_name: str) -> bool:
        """:meth:`delete_file` off the event loop."""
        return await asyncio.to_thread(self.delete_file, object_name)


storage_service = CloudStorageService()

# Re-exported so callers can catch them without importing the validation
# module directly.
__all__ = [
    "CloudStorageService",
    "UnsafePath",
    "UnsafeUpload",
    "UploadTooLarge",
    "detect_content_type",
    "read_upload",
    "scan_file_for_malware",
    "storage_service",
]
