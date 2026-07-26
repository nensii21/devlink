from __future__ import annotations

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_active_user
from app.models.user import User
from app.schemas.export import ExportResponse
from app.services.export_service import ExportService

router = APIRouter()


@router.post(
    "/me/export",
    response_model=ExportResponse,
    summary="Export all user data",
    description="Return a JSON archive of everything the authenticated user has on DevLink.",
)
def export_user_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    data = ExportService.collect_user_data(db, current_user)
    return ExportResponse(data=data)
