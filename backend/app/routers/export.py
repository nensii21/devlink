from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    data = ExportService.collect_user_data(db, current_user)
    return ExportResponse(data=data)


@router.get(
    "/me/portfolio/export",
    summary="Export Developer Portfolio",
    description="Export DevLink profile as a professional portfolio in PDF, Markdown, or JSON format.",
)
def export_portfolio(
    format: str = Query("json", regex="^(pdf|markdown|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if format == "markdown":
        content = ExportService.export_portfolio_markdown(db, current_user)
        filename = f"{current_user.username}_portfolio.md"
        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    elif format == "pdf":
        content = ExportService.export_portfolio_html(db, current_user)
        filename = f"{current_user.username}_portfolio.html"
        return HTMLResponse(
            content=content,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        data = ExportService.collect_user_data(db, current_user)
        filename = f"{current_user.username}_portfolio.json"
        return JSONResponse(
            content=data.model_dump(mode="json"),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
