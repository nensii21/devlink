from fastapi import APIRouter

from app.routers import (
    activities,
    applications,
    auth,
    backup,
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
    messages,
    mfa,
    notifications,
    oauth_linking,
    org_audit_logs,
    organizations,
    plugins,
    profile_summary,
    profile_suggestions,
    project_members,
    project_comments,
    project_milestones,
    project_tags,
    project_documents,
    project_dashboards,
    projects,
    recommendations,
    repositories,
    repository_quality,
    saved_searches,
    search,
    security_dashboard,
    security_events,
    skills,
    users,
    webhooks,
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
api_v1_router.include_router(mfa.router)
api_v1_router.include_router(oauth_linking.router)
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(blocks.router, prefix="/blocks", tags=["User Blocks"])
api_v1_router.include_router(export.router, prefix="/users", tags=["Export"])
api_v1_router.include_router(backup.router)
api_v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(project_members.router)
api_v1_router.include_router(project_documents.router)
api_v1_router.include_router(project_dashboards.router)
api_v1_router.include_router(project_milestones.router)
api_v1_router.include_router(project_comments.router)
api_v1_router.include_router(
    builder_flares.router, prefix="/flare", tags=["Builder's Flare"]
)
api_v1_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_v1_router.include_router(
    organizations.router, prefix="/organizations", tags=["Organizations"]
)
api_v1_router.include_router(org_audit_logs.router)
api_v1_router.include_router(webhooks.router)
api_v1_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"]
)
api_v1_router.include_router(followers.router, prefix="/followers", tags=["Followers"])
api_v1_router.include_router(bookmarks.router)
api_v1_router.include_router(bookmark_collections.router)
api_v1_router.include_router(activities.router)
api_v1_router.include_router(conversations.router)
api_v1_router.include_router(
    profile_summary.router, prefix="/profile-summary", tags=["Profile Summary"]
)
api_v1_router.include_router(
    profile_suggestions.router, prefix="/profile-suggestions", tags=["Profile Suggestions"]
)
api_v1_router.include_router(
    profile_suggestions.router, prefix="/users/me/profile-suggestions", tags=["Profile Suggestions"]
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
api_v1_router.include_router(plugins.router)
api_v1_router.include_router(security_dashboard.router)
api_v1_router.include_router(security_events.router)
api_v1_router.include_router(
    hackathons.router, prefix="/hackathons", tags=["Hackathons"]
)
