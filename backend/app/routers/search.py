from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.search import SearchResult
from app.services.search_service import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)

@router.get(
    "/",
    response_model=SearchResult,
)
def global_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    return SearchService.search(db, q)
