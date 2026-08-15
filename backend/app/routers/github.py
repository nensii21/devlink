from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User
from app.services.github_service import GitHubService
from typing import Any, List, Dict

router = APIRouter(
    prefix="/github",
    tags=["GitHub Insights"],
)


@router.get(
    "/{username}/profile",
    summary="Get GitHub profile",
)
async def get_github_profile(
    username: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    return await GitHubService.get_profile(username)


@router.get(
    "/{username}/repositories",
    summary="Get GitHub repositories",
)
async def get_github_repositories(
    username: str,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    return await GitHubService.get_repositories(username)


@router.get(
    "/{username}/stats",
    summary="Get GitHub stats",
)
async def get_github_stats(
    username: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    return await GitHubService.get_stats(username)


@router.get(
    "/{username}/contributions",
    summary="Get GitHub contributions graph data",
)
async def get_github_contributions(
    username: str,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    return await GitHubService.get_contributions(username)
