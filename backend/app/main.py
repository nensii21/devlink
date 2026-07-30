from contextlib import asynccontextmanager
import os
from pathlib import Path

# pyrefly: ignore [missing-import]

# pyrefly: ignore [missing-import]

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# pyrefly: ignore [missing-import]

from fastapi.middleware.cors import CORSMiddleware

# pyrefly: ignore [missing-import]

from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.middleware.rate_limit import limiter
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.activity import ActivityTrackingMiddleware
from app.middleware.rate_limit import limiter

# pyrefly: ignore [missing-import]

from slowapi.errors import RateLimitExceeded

# pyrefly: ignore [missing-import]

from slowapi.middleware import SlowAPIMiddleware

# pyrefly: ignore [missing-import]

from slowapi import _rate_limit_exceeded_handler

from app.routers import (
    activities,
    applications,
    auth,
    bookmark_collections,
    bookmarks,
    builder_flares,
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
    projects,
    recommendations,
    repositories,
    repository_quality,
    skills,
    users,
    search,
    saved_searches,
    media,
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
from app.core.error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    rate_limit_exception_handler,
    global_exception_handler,
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_middleware(SlowAPIMiddleware)

# ------------------------------------------------------------------
# Security Middleware
# ------------------------------------------------------------------


app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ActivityTrackingMiddleware)

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
    ],
)

from pathlib import Path

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


from app.api.v1.router import api_v1_router

# Include Versioned API v1 Router (/api/v1)

app.include_router(api_v1_router)

# Include Legacy Unversioned API Routers (/api) for Backward Compatibility

from app.routers import (
    activities,
    analytics,
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
    media,
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

# Router inclusions


app.include_router(media.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(blocks.router, prefix="/api/blocks", tags=["User Blocks"])
app.include_router(export.router, prefix="/api/users", tags=["Export"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(builder_flares.router, prefix="/api/flare", tags=["Builder's Flare"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(
    notifications.router, prefix="/api/notifications", tags=["Notifications"]
)

app.include_router(followers.router, prefix="/api/followers", tags=["Followers"])
app.include_router(bookmarks.router)
app.include_router(bookmark_collections.router)
app.include_router(activities.router)
app.include_router(conversations.router)
app.include_router(issues.router, prefix="/api/issues", tags=["Issues"])
app.include_router(
    profile_summary.router, prefix="/api/profile-summary", tags=["Profile Summary"]
)
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
app.include_router(repositories.router)
app.include_router(organizations.router)
app.include_router(applications.router)
app.include_router(skills.router)
app.include_router(users.router)
app.include_router(websockets.router)
app.include_router(recommendations.router)
app.include_router(
    repository_quality.router, prefix="/api", tags=["Repository Quality"]
)
app.include_router(health.router)
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(saved_searches.router)
app.include_router(hackathons.router, prefix="/api/hackathons", tags=["Hackathons"])
