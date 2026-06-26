from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    DevLink Application Settings

    Values are loaded from the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    APP_NAME: str = "DevLink API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        min_length=32,
    )

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PASSWORD_HASH_SCHEME: str = "bcrypt"

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:password@localhost:5432/devlink"
    )

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------

    REDIS_URL: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]

    @field_validator("ALLOWED_IMAGE_TYPES", mode="before")
    @classmethod
    def parse_image_types(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",")]
        return value

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@devlink.app"

    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ------------------------------------------------------------------
    # File Uploads
    # ------------------------------------------------------------------

    MAX_UPLOAD_SIZE_MB: int = 10

    ALLOWED_IMAGE_TYPES: list[str] = [
        "image/png",
        "image/jpeg",
        "image/webp",
    ]

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------

    DEFAULT_RATE_LIMIT: str = "100/minute"
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/minute"

    # ------------------------------------------------------------------
    # Security Headers
    # ------------------------------------------------------------------

    ENABLE_HSTS: bool = True
    ENABLE_CSP: bool = True
    ENABLE_X_FRAME_OPTIONS: bool = True
    ENABLE_X_CONTENT_TYPE_OPTIONS: bool = True


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()


settings = get_settings()