from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi.routing import APIRoute

# pyrefly: ignore [missing-import]
from fastapi import FastAPI

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

from app.core.config import settings
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
    conversations,
    followers,
    health,
    messages,
    notifications,
    organizations,
    projects,
    recommendations,
    repositories,
    repository_quality,
    skills,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """

    print("🚀 DevLink Backend Starting...")

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

    print("🛑 DevLink Backend Stopping...")

    from app.core.cache import cache_manager

    cache_manager.disconnect()


app = FastAPI(
    title="DevLink API",
    description="Backend API for the DevLink Developer Collaboration Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# Rate Limiting
# ------------------------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)
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


@app.get("/health", tags=["Health"])
async def health_simple():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# ------------------------------------------------------------------
# Global Exception Handler
# ------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
        },
    )


# ------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------

# Router inclusions

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
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
app.include_router(repositories.router)
app.include_router(organizations.router)
app.include_router(applications.router)
app.include_router(skills.router)
app.include_router(recommendations.router)
app.include_router(repository_quality.router, prefix="/api", tags=["Repository Quality"])
app.include_router(health.router)
