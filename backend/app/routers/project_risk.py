from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.project_risk import ProjectRiskInput, ProjectRiskReport
from app.services.project_risk_service import ProjectRiskService

router = APIRouter(prefix="/api/projects/risk-analysis", tags=["Project Risk Analysis"])

@router.post("/", response_model=ProjectRiskReport, status_code=status.HTTP_200_OK)
async def analyze_project_risk(
    payload: ProjectRiskInput,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze project details and return a risk report with severity levels and suggested improvements.
    """
    return ProjectRiskService.analyze_project(payload)
