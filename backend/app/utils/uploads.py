from __future__ import annotations

import uuid
from pathlib import Path
from typing import Final

from app.core.config import settings

ALLOWED_RESUME_MIME_TYPES: Final[set[str]] = {"application/pdf"}
MAX_RESUME_SIZE_BYTES: Final[int] = settings.RESUME_MAX_SIZE_MB * 1024 * 1024
MAX_IMAGE_SIZE_BYTES: Final[int] = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_IMAGE_MIME_TYPES: Final[set[str]] = set(
    ct.strip().lower() for ct in settings.ALLOWED_IMAGE_TYPES.split(",") if ct.strip()
)


def validate_resume_upload(
    filename: str | None, content_type: str | None, size_bytes: int
) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise ValueError("Please upload a PDF file.")
    normalized_content_type = (content_type or "").lower()
    if normalized_content_type not in ALLOWED_RESUME_MIME_TYPES:
        raise ValueError("Please upload a PDF file.")
    if size_bytes > MAX_RESUME_SIZE_BYTES:
        raise ValueError(
            f"Resume file must be smaller than {settings.RESUME_MAX_SIZE_MB}MB."
        )


def save_resume_upload(contents: bytes, filename: str, user_id: uuid.UUID | str) -> str:
    upload_dir = Path(settings.UPLOAD_DIR) / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{user_id}-{uuid.uuid4().hex}.pdf"
    destination = upload_dir / safe_name
    destination.write_bytes(contents)

    return f"/uploads/resumes/{safe_name}"


def validate_image_upload(
    filename: str | None, content_type: str | None, size_bytes: int
) -> None:
    """
    Validates uploaded image file extension, MIME type, and size.
    """
    if not filename:
        raise ValueError("Please upload an image file.")
    ext = Path(filename).suffix.lower()
    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}
    if ext not in allowed_exts:
        raise ValueError(
            f"Unsupported file extension: {ext}. Allowed: {', '.join(allowed_exts)}"
        )
    normalized_content_type = (content_type or "").lower()
    if (
        normalized_content_type
        and normalized_content_type not in ALLOWED_IMAGE_MIME_TYPES
    ):
        if not normalized_content_type.startswith("image/"):
            raise ValueError("Please upload a valid image file.")
    if size_bytes > MAX_IMAGE_SIZE_BYTES:
        raise ValueError(
            f"Image file size must be smaller than {settings.MAX_UPLOAD_SIZE_MB}MB."
        )


def save_image_upload(
    contents: bytes,
    filename: str,
    subfolder: str = "images",
    user_id: uuid.UUID | str | None = None,
    max_dimensions: tuple[int, int] = (1920, 1080),
    thumb_dimensions: tuple[int, int] | None = (150, 150),
) -> dict[str, str | None]:
    """
    Optimizes and saves an uploaded image (and optional thumbnail) to disk.
    Returns a dictionary with 'image_url' and 'thumbnail_url'.
    """
    from app.services.image_optimizer import ImageOptimizer

    result = ImageOptimizer.process_image(
        contents,
        max_dimensions=max_dimensions,
        thumb_dimensions=thumb_dimensions,
        quality=85,
        output_format="WEBP",
    )

    upload_dir = Path(settings.UPLOAD_DIR) / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"{user_id}-" if user_id else ""
    file_id = f"{prefix}{uuid.uuid4().hex}"

    image_filename = f"{file_id}.webp"
    image_path = upload_dir / image_filename
    image_path.write_bytes(result["optimized_bytes"])

    image_url = f"/uploads/{subfolder}/{image_filename}"
    thumbnail_url = None

    if result.get("thumbnail_bytes"):
        thumb_filename = f"{file_id}_thumb.webp"
        thumb_path = upload_dir / thumb_filename
        thumb_path.write_bytes(result["thumbnail_bytes"])
        thumbnail_url = f"/uploads/{subfolder}/{thumb_filename}"
    return {
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
    }
