from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.utils.media import MediaStorageManager
from pydantic import BaseModel

router = APIRouter(prefix="/media", tags=["Media"])


class MediaUploadResponse(BaseModel):
    hash: str
    url: str
    thumbnail_url: str
    reused: bool


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Upload an image. The image will be optimized, converted to WebP,
    and a thumbnail will be generated. Duplicate detection is performed.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    contents = await file.read()
    try:
        result = MediaStorageManager.save_media(
            file_contents=contents,
            filename=file.filename,
            content_type=file.content_type or "",
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and store image: {str(exc)}",
        ) from exc


from pathlib import Path
from app.core.config import settings


class AttachmentUploadResponse(BaseModel):
    url: str
    filename: str
    size: int
    mime_type: str


@router.post(
    "/upload-attachment",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload general message attachment (Image, PDF, ZIP, code, doc)",
)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    import uuid

    file_id = uuid.uuid4().hex
    safe_filename = "".join(
        c for c in file.filename if c.isalnum() or c in "._-"
    ).strip()
    if not safe_filename:
        safe_filename = "attachment"

    attachments_dir = Path(settings.UPLOAD_DIR) / "attachments" / file_id
    attachments_dir.mkdir(parents=True, exist_ok=True)
    file_path = attachments_dir / safe_filename
    file_path.write_bytes(contents)

    relative_url = f"/uploads/attachments/{file_id}/{safe_filename}"

    return AttachmentUploadResponse(
        url=relative_url,
        filename=file.filename,
        size=len(contents),
        mime_type=file.content_type or "application/octet-stream",
    )
