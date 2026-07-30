from functools import lru_cache

# pyrefly: ignore [missing-import]
from pydantic import Field

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    DevLink Application Settings
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================

    APP_NAME: str = "DevLink API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ==========================================================
    # Server
    # ==========================================================

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ==========================================================
    # Security
    # ==========================================================

    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_A_LONG_RANDOM_SECRET",
        min_length=32,
    )

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    PASSWORD_HASH_SCHEME: str = "bcrypt"

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/devlink"

    # ==========================================================
    # Redis
    # ==========================================================

    REDIS_URL: str = "redis://localhost:6379/0"

    # ==========================================================
    # CORS
    # ==========================================================

    ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://localhost:5174,http://localhost:3000"
    )

    FRONTEND_URL: str = "http://localhost:5173"

    # ==========================================================
    # Email
    # ==========================================================

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587

    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    EMAIL_FROM: str = "noreply@devlink.app"

    # ==========================================================
    # OAuth
    # ==========================================================

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ==========================================================
    # Uploads
    # ==========================================================

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    RESUME_MAX_SIZE_MB: int = 5

    ALLOWED_IMAGE_TYPES: str = "image/png,image/jpeg,image/webp"

    MEDIA_UPLOAD_DIR: str = "uploads/media"
    MEDIA_QUALITY: int = 80
    MEDIA_MAX_DIMENSION: int = 1200
    MEDIA_THUMB_DIMENSION: int = 200
    CDN_BASE_URL: str | None = None

    # ==========================================================
    # AI
    # ==========================================================

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ==========================================================
    # Logging
    # ==========================================================

    LOG_LEVEL: str = "INFO"

    # ==========================================================
    # Rate Limiting
    # ==========================================================

    DEFAULT_RATE_LIMIT: str = "100/minute"
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/hour"
    MESSAGE_RATE_LIMIT: str = "30/minute"
    SEARCH_RATE_LIMIT: str = "60/minute"
    PROJECT_RATE_LIMIT: str = "100/minute"
    PASSWORD_RESET_RATE_LIMIT: str = "3/15minutes"
    COMMENT_RATE_LIMIT: str = "30/minute"
    RECOMMENDATION_RATE_LIMIT: str = "20/minute"

    # ==========================================================
    # Security Headers
    # ==========================================================

    ENABLE_HSTS: bool = True
    HSTS_HEADER_VALUE: str = "max-age=63072000; includeSubDomains; preload"

    ENABLE_CSP: bool = True
    CSP_HEADER_VALUE: str = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https: data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    ENABLE_X_FRAME_OPTIONS: bool = True
    X_FRAME_OPTIONS_VALUE: str = "DENY"

    ENABLE_X_CONTENT_TYPE_OPTIONS: bool = True

    ENABLE_REFERRER_POLICY: bool = True
    REFERRER_POLICY_VALUE: str = "strict-origin-when-cross-origin"

    ENABLE_PERMISSIONS_POLICY: bool = True
    PERMISSIONS_POLICY_VALUE: str = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
    )

    ENABLE_DNS_PREFETCH_CONTROL: bool = True
    ENABLE_CROSS_DOMAIN_POLICIES: bool = True

    ENABLE_COOP: bool = True
    CROSS_ORIGIN_OPENER_POLICY: str = "same-origin"

    ENABLE_CORP: bool = True
    CROSS_ORIGIN_RESOURCE_POLICY: str = "same-origin"

    ENABLE_COEP: bool = True
    CROSS_ORIGIN_EMBEDDER_POLICY: str = "require-corp"

    # ==========================================================
    # Celery
    # ==========================================================

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    CELERY_TASK_ALWAYS_EAGER: bool = False

    # ==========================================================
    # WebSocket
    # ==========================================================

    WEBSOCKET_HEARTBEAT: int = 30

    # ==========================================================
    # Feature Flags
    # ==========================================================

    ENABLE_EMAIL_VERIFICATION: bool = True
    ENABLE_GOOGLE_LOGIN: bool = True
    ENABLE_GITHUB_LOGIN: bool = True
    ENABLE_AI_ASSISTANT: bool = True
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_CHAT: bool = True
    ENABLE_BUILDER_FLARE: bool = True
    ENABLE_PROJECTS: bool = True
    ENABLE_APPLICATIONS: bool = True

    # ==========================================================
    # Helper Properties
    # ==========================================================

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def allowed_image_types(self) -> list[str]:
        return [
            image.strip()
            for image in self.ALLOWED_IMAGE_TYPES.split(",")
            if image.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
