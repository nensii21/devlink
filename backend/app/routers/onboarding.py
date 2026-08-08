from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/api/contributors/onboarding", tags=["AI Contributor Onboarding"])

@router.post("/", response_model=OnboardingResponse, status_code=status.HTTP_200_OK)
async def get_contributor_onboarding(
    payload: OnboardingRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Provide personalized onboarding guidance for first-time contributors including 
    project structure, beginner issues, documentation links, and coding standards.
    """
    return OnboardingService.get_onboarding_guidance(payload)
