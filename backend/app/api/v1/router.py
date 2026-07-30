from fastapi import APIRouter

from app.routers import (
    activities,
    applications,
    auth,
    blocks,
    bookmark_collections,
    bookmarks,
    builder_flares,
    contributor_matching,
    conversation_starters,
    conversations,
    export,
    followers,
    hackathons,
    health,
    issues,
    messages,
    notifications,
    organizations,
    profile_summary,
    project_tags,
    projects,
    recommendations,
    repositories,
    repository_quality,
    saved_searches,
    search,
    skills,
    users,
    websockets,
)

api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("", tags=["Root"])
@api_v1_router.get("/", tags=["Root"])
async def v1_root():
    """
    API v1 Root Endpoint.
    """
    return {
        "name": "DevLink API",
        "version": "v1",
        "status": "running",
        "documentation": "/docs",
    }


# Router inclusions under /api/v1
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(blocks.router, prefix="/blocks", tags=["User Blocks"])
api_v1_router.include_router(export.router, prefix="/users", tags=["Export"])
api_v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(
    builder_flares.router, prefix="/flare", tags=["Builder's Flare"]
)
api_v1_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_v1_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"]
)
api_v1_router.include_router(followers.router, prefix="/followers", tags=["Followers"])
api_v1_router.include_router(bookmarks.router)
api_v1_router.include_router(bookmark_collections.router)
api_v1_router.include_router(activities.router)
api_v1_router.include_router(conversations.router)
api_v1_router.include_router(issues.router, prefix="/issues", tags=["Issues"])
api_v1_router.include_router(
    profile_summary.router, prefix="/profile-summary", tags=["Profile Summary"]
)
api_v1_router.include_router(
    conversation_starters.router,
    prefix="/conversation-starters",
    tags=["Conversation Starters"],
)
api_v1_router.include_router(
    project_tags.router, prefix="/project-tags", tags=["Project Tags"]
)
api_v1_router.include_router(
    contributor_matching.router,
    prefix="/contributor-matching",
    tags=["Contributor Matching"],
)
api_v1_router.include_router(repositories.router)
api_v1_router.include_router(organizations.router)
api_v1_router.include_router(applications.router)
api_v1_router.include_router(skills.router)
api_v1_router.include_router(websockets.router)
api_v1_router.include_router(recommendations.router)
api_v1_router.include_router(repository_quality.router, tags=["Repository Quality"])
api_v1_router.include_router(health.router)
api_v1_router.include_router(search.router, prefix="/search", tags=["Search"])
api_v1_router.include_router(saved_searches.router)
api_v1_router.include_router(
    hackathons.router, prefix="/hackathons", tags=["Hackathons"]
)
