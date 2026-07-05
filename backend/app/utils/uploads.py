from __future__ import annotations

import uuid
from pathlib import Path
from typing import Final

from app.core.config import settings

ALLOWED_RESUME_MIME_TYPES: Final[set[str]] = {"application/pdf"}
MAX_RESUME_SIZE_BYTES: Final[int] = settings.RESUME_MAX_SIZE_MB * 1024 * 1024


def validate_resume_upload(filename: str | None, content_type: str | None, size_bytes: int) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise ValueError("Please upload a PDF file.")

    normalized_content_type = (content_type or "").lower()
    if normalized_content_type not in ALLOWED_RESUME_MIME_TYPES:
        raise ValueError("Please upload a PDF file.")

    if size_bytes > MAX_RESUME_SIZE_BYTES:
        raise ValueError(f"Resume file must be smaller than {settings.RESUME_MAX_SIZE_MB}MB.")


def save_resume_upload(contents: bytes, filename: str, user_id: uuid.UUID | str) -> str:
    upload_dir = Path(settings.UPLOAD_DIR) / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{user_id}-{uuid.uuid4().hex}.pdf"
    destination = upload_dir / safe_name
    destination.write_bytes(contents)

    return f"/uploads/resumes/{safe_name}"
