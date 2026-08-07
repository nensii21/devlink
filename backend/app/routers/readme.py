from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.readme import ReadmeGenerationRequest, ReadmeGenerationResponse
from app.services.readme_service import ReadmeService

router = APIRouter(prefix="/api/projects/readme", tags=["AI README Generator"])

@router.post("/", response_model=ReadmeGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_readme(
    payload: ReadmeGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a professional markdown README with Overview, Features, Installation, Tech Stack, Roadmap, and License.
    """
    return ReadmeService.generate_readme(payload)
