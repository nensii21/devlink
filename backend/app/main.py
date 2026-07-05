from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """

    print("🚀 DevLink Backend Starting...")

    # Future startup tasks
    # - Connect database
    # - Connect Redis
    # - Load AI models
    # - Warm caches

    yield

    print("🛑 DevLink Backend Stopping...")


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

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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
# Static Files
# ------------------------------------------------------------------

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
async def health():
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

# Uncomment as each router is created.

from app.routers import auth
from app.routers import users
from app.routers import projects
from app.routers import builders
from app.routers import builder_flare
from app.routers import messages
from app.routers import notifications
from app.routers import ai
from app.routers import followers
from app.routers import bookmarks
from app.routers import activities
from app.routers import notifications
from app.routers import conversations
from app.routers import repositories
from app.routers import organizations
from app.routers import applications
from app.routers import skills
from app.routers import users

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(builder_flare.router, prefix="/api/flare", tags=["Builder's Flare"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(
    notifications.router, prefix="/api/notifications", tags=["Notifications"]
)
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(followers.router)
app.include_router(bookmarks.router)
app.include_router(activities.router)
app.include_router(notifications.router)
app.include_router(conversations.router)
app.include_router(repositories.router)
app.include_router(organizations.router)
app.include_router(applications.router)
app.include_router(skills.router)
app.include_router(users.router)
