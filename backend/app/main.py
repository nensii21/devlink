from contextlib import asynccontextmanager
import os
from pathlib import Path

# pyrefly: ignore [missing-import]

# pyrefly: ignore [missing-import]

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

# pyrefly: ignore [missing-import]

from fastapi.middleware.cors import CORSMiddleware

# pyrefly: ignore [missing-import]

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.middleware.rate_limit import limiter
from app.middleware.structured_logging import StructuredLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.activity import ActivityTrackingMiddleware
from app.middleware.maintenance import MaintenanceMiddleware

# pyrefly: ignore [missing-import]


# pyrefly: ignore [missing-import]


# pyrefly: ignore [missing-import]


from app.routers import (
    activities,
    applications,
    auth,
    bookmark_collections,
    bookmarks,
    builder_flares,
    centralized_analytics,
    conversation_starters,
    contributor_matching,
    conversations,
    export,
    followers,
    health,
    issues,
    messages,
    notifications,
    organizations,
    profile_summary,
    project_tags,
    project_dashboards,
    projects,
    recommendations,
    repositories,
    repository_quality,
    skills,
    users,
    search,
    saved_searches,
    media,
    maintenance,
    message_drafts,
    global_announcements,
    feature_announcements,
    posts,
)


import asyncio


async def check_presence_timeouts():
    """Background task to scan for inactive WebSocket connections and set status to away."""
    from app.routers.websockets import manager

    try:
        while True:
            await asyncio.sleep(15)  # scan every 15 seconds
            await manager.check_timeouts(timeout_seconds=300)  # 5 minutes
    except asyncio.CancelledError:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """

    print("[INFO] DevLink Backend Starting...")

    # Start user presence timeout background task

    presence_task = asyncio.create_task(check_presence_timeouts())

    from app.core.events import event_bus
    from app.core.event_handlers import register_all_handlers

    register_all_handlers(event_bus)

    from app.core.cache import cache_manager

    cache_manager.connect()

    # Future startup tasks
    # - Connect database
    # - Connect Redis
    # - Load AI models
    # - Warm caches

    yield

    print("[INFO] DevLink Backend Stopping...")

    # Cancel user presence timeout background task

    presence_task.cancel()
    try:
        await presence_task
    except asyncio.CancelledError:
        pass
    from app.core.cache import cache_manager

    cache_manager.disconnect()


from fastapi.responses import HTMLResponse

app = FastAPI(
    title="DevLink API",
    description="Backend API for the DevLink Developer Collaboration Platform",
    version="1.0.0",
    docs_url=None,
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_offline_docs():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevLink API - Dashboard & Documentation</title>
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --heading: #f0f6fc;
            --accent: #58a6ff;
            --green: #238636;
            --purple: #8957e5;
            --orange: #d96d00;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 30px;
            line-height: 1.5;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        header {
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 {
            color: var(--heading);
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        .status-badge {
            background-color: rgba(35, 134, 54, 0.2);
            color: #3fb950;
            border: 1px solid rgba(63, 185, 80, 0.4);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        .section {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }
        h2 {
            color: var(--heading);
            font-size: 20px;
            margin-top: 0;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }
        .endpoint {
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .method {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            margin-right: 10px;
        }
        .method.post { background: #238636; color: white; }
        .method.get { background: #1f6feb; color: white; }
        .method.delete { background: #da3633; color: white; }
        .path {
            font-family: monospace;
            font-size: 16px;
            color: var(--heading);
            font-weight: 600;
        }
        .desc {
            color: #8b949e;
            margin-top: 8px;
            font-size: 14px;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }
        .feature-card {
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 16px;
        }
        .feature-card h3 {
            color: var(--accent);
            margin-top: 0;
            font-size: 16px;
        }
        code {
            background: rgba(110, 118, 129, 0.4);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>DevLink API Documentation</h1>
                <div class="desc">Backend API for DevLink Developer Collaboration Platform</div>
            </div>
            <span class="status-badge">● Server Active (v1.0.0)</span>
        </header>

        <div class="section">
            <h2>📷 Issue #535: Image Optimization Pipeline</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>1. Automatic Resizing</h3>
                    <div>Resizes uploaded avatar images down to max <code>400x400</code> using <code>LANCZOS</code> high-quality resampling.</div>
                </div>
                <div class="feature-card">
                    <h3>2. WebP Compression</h3>
                    <div>Converts all image uploads to optimized <code>.webp</code> format at quality <code>85</code> for fast network delivery.</div>
                </div>
                <div class="feature-card">
                    <h3>3. Thumbnail Generation</h3>
                    <div>Automatically generates a <code>150x150</code> WebP thumbnail variant (<code>{file_id}_thumb.webp</code>).</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🚀 Image Optimization Endpoints</h2>

            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/users/me/avatar</span>
                <div class="desc">Uploads, validates, strips EXIF metadata, resizes, compresses, and generates thumbnails for user avatar.</div>
                <div class="desc" style="margin-top: 10px;">
                    <strong>Supported Formats:</strong> <code>PNG</code>, <code>JPEG</code>, <code>WEBP</code>, <code>GIF</code>, <code>TIFF</code>, <code>BMP</code><br>
                    <strong>Returns:</strong> Updated user profile object with relative WebP avatar URL.
                </div>
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/uploads/avatars/{filename}</span>
                <div class="desc">Serves optimized WebP main avatar images and <code>_thumb.webp</code> thumbnail files from disk.</div>
            </div>
        </div>

        <div class="section">
            <h2>🔗 System Endpoints</h2>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/openapi.json</span>
                <div class="desc">Returns raw OpenAPI 3.1.0 JSON schema.</div>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/health</span>
                <div class="desc">System health check endpoint.</div>
            </div>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


# ------------------------------------------------------------------
# Rate Limiting
# ------------------------------------------------------------------


app.state.limiter = limiter

# ------------------------------------------------------------------
# Standardized Exception Handlers
# ------------------------------------------------------------------


from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.core.exceptions import AppException
from app.core.error_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    rate_limit_exception_handler,
    global_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
)

# Registration order does not decide which handler runs -- Starlette walks the
# raised exception's MRO and picks the most specific class registered -- so
# `IntegrityError` keeps its 409 even though `SQLAlchemyError` is also
# registered, and `AppException` keeps its own status even though `Exception`
# is. They are listed most-specific-first anyway, so reading the block tells
# you the same thing.
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_middleware(SlowAPIMiddleware)

# ------------------------------------------------------------------
# Security Middleware
# ------------------------------------------------------------------
from app.middleware.request_id import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

from app.middleware.etag import ETagMiddleware

# Sits outside the security headers middleware so a 304 still carries them.
app.add_middleware(ETagMiddleware)

app.add_middleware(ActivityTrackingMiddleware)
app.add_middleware(MaintenanceMiddleware)

from app.middleware.request_validation import RequestValidationMiddleware

app.add_middleware(RequestValidationMiddleware)

from app.middleware.audit_context import AuditContextMiddleware

app.add_middleware(AuditContextMiddleware)

from app.middleware.org_audit_logging import OrganizationAuditMiddleware

app.add_middleware(OrganizationAuditMiddleware)

from app.middleware.request_logging import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-Request-ID",
        "X-Correlation-ID",
    ],
)


Path("uploads").mkdir(exist_ok=True)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "DevLink API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/api", tags=["Root"])
@app.get("/api/", tags=["Root"])
async def api_root():
    return {
        "name": "DevLink API",
        "version": "v1",
        "current_version": "v1",
        "supported_versions": ["v1"],
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_simple():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# ------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------


from app.routers import connections
from app.api.v1.router import api_v1_router

# Include Versioned API v1 Router (/api/v1)

app.include_router(api_v1_router)

# Include Legacy Unversioned API Routers (/api) for Backward Compatibility

from app.routers import (
    analytics,
    blocks,
    hackathons,
    notification_templates,
    verification,
    websockets,
    graph,
    skill_matrix,
)

# Router inclusions
app.include_router(skill_matrix.router, prefix="/api", tags=["Skill Matrix"])
from app.routers import github

app.include_router(github.router, prefix="/api", tags=["GitHub Insights"])

app.include_router(media.router, prefix="/api", tags=["Media"])
from app.routers import link_previews

app.include_router(link_previews.router, prefix="/api", tags=["Link Previews"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
from app.routers import mfa

app.include_router(mfa.router, prefix="/api")
app.include_router(global_announcements.router, prefix="/api", tags=["Global Announcements"])
app.include_router(feature_announcements.router, prefix="/api", tags=["Feature Announcement Center"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(blocks.router, prefix="/api/blocks", tags=["User Blocks"])
from app.routers import testimonials

app.include_router(testimonials.router, prefix="/api", tags=["Testimonials"])
app.include_router(connections.router, prefix="/api/connections", tags=["Connections"])
app.include_router(export.router, prefix="/api/users", tags=["Export"])
from app.routers import pinned_projects

app.include_router(pinned_projects.router, prefix="/api", tags=["Pinned Projects"])
from app.routers import feedback

app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
from app.routers import project_members

app.include_router(project_members.router, prefix="/api", tags=["Project Members"])
app.include_router(
    project_dashboards.router, prefix="/api", tags=["Project Dashboards"]
)
from app.routers import project_milestones

app.include_router(
    project_milestones.router, prefix="/api", tags=["Project Milestones"]
)
from app.routers import project_time_logs

app.include_router(
    project_time_logs.router, prefix="/api", tags=["Project Time Tracking"]
)
from app.routers import calendar as calendar_router

app.include_router(calendar_router.router, prefix="/api", tags=["Calendar"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
from app.routers import project_releases

app.include_router(project_releases.router, prefix="/api", tags=["Project Releases"])
app.include_router(builder_flares.router, prefix="/api/flare", tags=["Builder's Flare"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(message_drafts.router, prefix="/api", tags=["Message Drafts"])
app.include_router(
    notifications.router, prefix="/api/notifications", tags=["Notifications"]
)
from app.routers import admin_notifications

app.include_router(
    admin_notifications.router, prefix="/api", tags=["Admin Notifications"]
)

app.include_router(followers.router, prefix="/api/followers", tags=["Followers"])
app.include_router(bookmarks.router, prefix="/api", tags=["Bookmarks"])
app.include_router(
    bookmark_collections.router,
    prefix="/api",
    tags=["Bookmark Collections"],
)
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
from app.routers import activity_heatmap

app.include_router(activity_heatmap.router, prefix="/api", tags=["Activity Heatmap"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
from app.routers import moderation

app.include_router(moderation.router, prefix="/api", tags=["Moderation"])
from app.routers import audit

app.include_router(audit.router, prefix="/api", tags=["Audit"])
from app.routers import plugins

app.include_router(plugins.router, prefix="/api", tags=["Plugin & Extension System"])
from app.routers import security_events

app.include_router(
    security_events.router, prefix="/api", tags=["Security Events Monitoring"]
)
app.include_router(issues.router, prefix="/api", tags=["Issues"])
app.include_router(
    profile_summary.router, prefix="/api/profile-summary", tags=["Profile Summary"]
)
from app.routers import profile_suggestions

app.include_router(
    profile_suggestions.router,
    prefix="/api",
    tags=["Profile Suggestions"],
)
app.include_router(
    profile_suggestions.router,
    prefix="/api/users/me",
    tags=["Profile Suggestions"],
)
from app.routers import profile_views

app.include_router(profile_views.router, prefix="/api", tags=["Profile Views"])

app.include_router(
    conversation_starters.router,
    prefix="/api/conversation-starters",
    tags=["Conversation Starters"],
)
app.include_router(
    project_tags.router, prefix="/api/project-tags", tags=["Project Tags"]
)
app.include_router(
    contributor_matching.router,
    prefix="/api/contributor-matching",
    tags=["Contributor Matching"],
)
app.include_router(repositories.router, prefix="/api", tags=["Repositories"])
app.include_router(organizations.router, prefix="/api", tags=["Organizations"])

from app.routers import workspace_api_tokens

app.include_router(
    workspace_api_tokens.router, prefix="/api", tags=["Workspace API Tokens"]
)

app.include_router(
    applications.router, prefix="/api/applications", tags=["Applications"]
)
app.include_router(skills.router, prefix="/api", tags=["Skills"])
# users.router already included above
app.include_router(websockets.router, prefix="/api", tags=["WebSockets"])
app.include_router(graph.router, prefix="/api", tags=["Graph"])
from app.routers import webhooks

app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(
    repository_quality.router, prefix="/api", tags=["Repository Quality"]
)
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(maintenance.router, prefix="/api", tags=["Maintenance"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(saved_searches.router, prefix="/api", tags=["Saved Searches"])
app.include_router(hackathons.router, prefix="/api/hackathons", tags=["Hackathons"])
app.include_router(
    notification_templates.router, prefix="/api", tags=["Notification Templates"]
)
app.include_router(verification.router, prefix="/api", tags=["Verification"])
app.include_router(
    centralized_analytics.router, prefix="/api", tags=["Centralized Analytics"]
)
app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])

from app.routers import project_templates

app.include_router(
    project_templates.router, prefix="/api", tags=["Project Templates Marketplace"]
)

from app.routers import badges

app.include_router(badges.router, prefix="/api", tags=["Badges"])


from app.routers import api_keys

app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(api_keys.org_api_keys_router, prefix="/api/v1")

from app.routers import background_jobs

app.include_router(background_jobs.router, prefix="/api")

from app.routers import feature_flags

app.include_router(feature_flags.router, prefix="/api", tags=["Feature Flags"])

from app.routers import reputation

app.include_router(reputation.router, prefix="/api", tags=["User Reputation System"])

from app.routers import email_templates
app.include_router(email_templates.router, prefix="/api", tags=["Email Notification Templates"])

from app.routers import developer_insights

app.include_router(
    developer_insights.router, prefix="/api", tags=["Developer Insights"]
)

from app.routers import project_collaboration_metrics

app.include_router(
    project_collaboration_metrics.router,
    prefix="/api",
    tags=["Project Collaboration Metrics"],
)
from app.routers import team_activity

app.include_router(team_activity.router, prefix="/api", tags=["Team Activity Timeline"])


# The generated OpenAPI document only lists the responses each handler declares
# explicitly, which leaves the error shapes out of the published schema even
# though every endpoint can return them (they come from the global exception
# handlers, not from the route signatures). Generated SDK clients therefore had
# no error types at all. Filling them in here keeps that knowledge in one place
# instead of repeating a `responses={...}` block on several hundred routes.
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="DevLink API",
        version="1.0.0",
        description="Backend API for the DevLink Developer Collaboration Platform",
        routes=app.routes,
    )

    error_400 = {"description": "Bad Request"}
    error_401 = {"description": "Unauthorized"}
    error_403 = {"description": "Forbidden"}
    error_404 = {"description": "Not Found"}
    error_409 = {"description": "Conflict"}
    error_500 = {"description": "Internal Server Error"}
    shared_responses = {
        "400": {"description": "Bad Request"},
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"},
        "404": {"description": "Not Found"},
        "409": {"description": "Conflict"},
        "500": {"description": "Internal Server Error"},
    }

    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            # A path item also holds non-operation keys such as "parameters",
            # whose value is a list rather than an operation object.
            if not isinstance(method, dict):
                continue
            responses = method.setdefault("responses", {})
            if "400" not in responses:
                responses["400"] = error_400
            if "401" not in responses:
                responses["401"] = error_401
            if "403" not in responses:
                responses["403"] = error_403
            if "404" not in responses:
                responses["404"] = error_404
            if "409" not in responses:
                responses["409"] = error_409
            if "500" not in responses:
                responses["500"] = error_500
            for status_code, description in shared_responses.items():
                responses.setdefault(status_code, description)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
