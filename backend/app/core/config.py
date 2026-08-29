import os
import sys
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

    # ----------------------------------------------------------
    # Password screening
    # ----------------------------------------------------------

    # Offline blocklist of common/guessable passwords, plus the check that a
    # password does not simply repeat the user's own username or email.
    ENABLE_PASSWORD_BLOCKLIST: bool = True

    # Have I Been Pwned range lookup. Off during tests so the suite never
    # touches the network; the behaviour itself is covered with a mocked
    # transport.
    ENABLE_HIBP_CHECK: bool = Field(
        default_factory=lambda: (
            not (os.getenv("TESTING") == "true" or "pytest" in sys.modules)
        )
    )
    HIBP_API_URL: str = "https://api.pwnedpasswords.com/range"
    HIBP_TIMEOUT_SECONDS: float = 3.0

    # A password is rejected once it has been seen at least this many times.
    # A count of 1 is often a corpus artefact rather than a password in active
    # circulation on stuffing lists.
    HIBP_MIN_BREACH_COUNT: int = 5

    # Range responses are effectively static, so they cache well.
    HIBP_CACHE_TTL_SECONDS: int = 60 * 60 * 24

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str = Field(
        default_factory=lambda: (
            "sqlite:///:memory:"
            if os.getenv("TESTING") == "true" or "pytest" in sys.modules
            else "postgresql+psycopg://postgres:password@localhost:5432/devlink"
        )
    )

    # ==========================================================
    # Redis
    # ==========================================================

    REDIS_URL: str = "redis://localhost:6379/0"

    # ----------------------------------------------------------
    # In-process (L1) response cache
    # ----------------------------------------------------------
    #
    # The tier in front of Redis. It used to be an unbounded dict, which on a
    # worker that runs for weeks is a leak: the keys `@cached` builds are
    # per-caller and per-argument, so the key space is the product of every
    # user id and every set of query arguments the decorated routes see
    # (#1402).
    #
    # A ceiling on entries rather than on bytes -- measuring an arbitrary
    # decoded JSON structure costs more than the cache saves. Raise it if
    # `cache_manager.stats()["evictions"]` climbs steadily, which means the
    # working set is larger than the ceiling.
    CACHE_L1_MAX_ENTRIES: int = 1000

    # How often expired entries are reclaimed. Eviction handles a cache that
    # fills up; the sweep handles the other shape -- entries that expire and
    # are never read again, which nothing else would ever remove.
    CACHE_L1_SWEEP_SECONDS: float = 60.0

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
    GOOGLE_REDIRECT_URI: str = ""

    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""

    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"
    MICROSOFT_REDIRECT_URI: str = ""

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

    # Cloud Storage (S3 / R2)
    STORAGE_PROVIDER: str = "local"  # local, s3, r2
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_BUCKET_NAME: str | None = None
    R2_ACCOUNT_ID: str | None = None

    # ==========================================================
    # AI
    # ==========================================================

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ==========================================================
    # External Integrations
    # ==========================================================

    GITHUB_API_TOKEN: str | None = None

    # ==========================================================
    # Logging
    # ==========================================================

    LOG_LEVEL: str = "INFO"

    # ==========================================================
    # Rate Limiting
    # ==========================================================

    ENABLE_RATE_LIMIT: bool = True
    DEFAULT_RATE_LIMIT: str = "100/minute"
    RATE_LIMIT_ANONYMOUS: str = "60/minute"
    RATE_LIMIT_AUTHENTICATED: str = "300/minute"
    RATE_LIMIT_PREMIUM: str = "1000/minute"
    RATE_LIMIT_ADMIN: str = "5000/minute"
    RATE_LIMIT_BYPASS_IPS: str = "127.0.0.1,::1"
    RATE_LIMIT_BYPASS_TOKEN: str = ""
    RATE_LIMIT_ALGORITHM: str = "sliding_window"
    AUTH_RATE_LIMIT: str = "5/minute"
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/hour"
    SEARCH_RATE_LIMIT: str = "30/minute"
    UPLOAD_RATE_LIMIT: str = "10/minute"
    MESSAGE_RATE_LIMIT: str = "30/minute"
    PROJECT_RATE_LIMIT: str = "100/minute"
    PASSWORD_RESET_RATE_LIMIT: str = "3/15minutes"
    VERIFY_EMAIL_RATE_LIMIT: str = "5/minute"
    MFA_RATE_LIMIT: str = "5/minute"
    COMMENT_RATE_LIMIT: str = "30/minute"
    RECOMMENDATION_RATE_LIMIT: str = "20/minute"

    #: Where the limiter keeps its counters. Empty means in-memory, which is
    #: per worker process -- with N workers the effective limit is N times what
    #: is configured, and every counter resets on deploy. Point this at Redis
    #: in any deployment running more than one process.
    #:
    #: Left empty rather than defaulting to REDIS_URL so that a developer
    #: without Redis running gets working limits rather than a boot failure.
    RATE_LIMIT_STORAGE_URI: str = ""

    @property
    def rate_limit_bypass_ip_list(self) -> list[str]:
        """`RATE_LIMIT_BYPASS_IPS` split into individual IP strings."""
        return [ip.strip() for ip in self.RATE_LIMIT_BYPASS_IPS.split(",") if ip.strip()]

    #: Comma-separated CIDRs for the proxies in front of this application.
    #: `X-Forwarded-For` is honoured only for requests whose immediate peer
    #: falls inside one of these; from anywhere else the header is ignored,
    #: because a client can send one and claim any address it likes.
    #:
    #: Empty by default: trusting nothing is the safe end of this setting, and
    #: it matches the behaviour before the setting existed.
    #:
    #: Typical values -- Kubernetes ingress: the pod CIDR, e.g.
    #: "10.42.0.0/16". Docker Compose: the bridge network, e.g.
    #: "172.16.0.0/12". A single host proxy: "10.0.0.7".
    TRUSTED_PROXY_CIDRS: str = ""

    @property
    def trusted_proxy_cidr_list(self) -> list[str]:
        """`TRUSTED_PROXY_CIDRS` split into entries."""
        return [
            part.strip() for part in self.TRUSTED_PROXY_CIDRS.split(",") if part.strip()
        ]

    # ==========================================================
    # Request Tracing / Correlation IDs
    # ==========================================================

    CORRELATION_ID_HEADER: str = "X-Correlation-ID"
    REQUEST_ID_HEADER: str = "X-Request-ID"
    ENABLE_REQUEST_TRACING: bool = True

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
    # HTTP Caching (ETag / conditional requests)
    # ==========================================================

    ENABLE_ETAG: bool = True

    # Responses larger than this are streamed through without a validator
    # rather than buffered in memory to be hashed. 1 MiB comfortably covers
    # every JSON payload the API produces today.
    ETAG_MAX_BODY_SIZE: int = 1024 * 1024

    # "no-cache" means "revalidate before reuse", not "do not store", so the
    # client keeps the body and we get to answer with a 304.
    ETAG_CACHE_CONTROL: str = "private, no-cache"

    # ==========================================================
    # Calendar Feeds
    # ==========================================================

    # Mixed into the feed-token signing key. Changing it invalidates every
    # issued feed URL at once, which is the blunt revocation lever available
    # while tokens are stateless.
    CALENDAR_FEED_TOKEN_SALT: str = "devlink-calendar-feed"

    # A year. Long enough that a subscription is genuinely set-and-forget,
    # short enough that a URL abandoned in a browser history stops working.
    CALENDAR_FEED_TOKEN_MAX_AGE_DAYS: int = 365

    # Advertised to clients via REFRESH-INTERVAL and X-PUBLISHED-TTL. Without
    # a hint, clients pick their own interval, often an hour for a feed that
    # changes daily.
    CALENDAR_FEED_REFRESH_MINUTES: int = 360

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
    ENABLE_MICROSOFT_LOGIN: bool = True
    ENABLE_AI_ASSISTANT: bool = True
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_CHAT: bool = True
    ENABLE_BUILDER_FLARE: bool = True
    ENABLE_PROJECTS: bool = True
    ENABLE_APPLICATIONS: bool = True

    # ==========================================================
    # Link Previews
    # ==========================================================

    # Short, because a preview is a nice-to-have sitting in front of a user
    # waiting for a message to send. A slow site gets no card rather than a
    # slow card.
    LINK_PREVIEW_TIMEOUT_SECONDS: float = 5.0

    # Everything we want lives in <head>. 512 KiB is generous for that and
    # bounds what a hostile server can make us buffer.
    LINK_PREVIEW_MAX_BYTES: int = 512 * 1024

    # Each hop is re-validated against the SSRF rules, so this is a cost
    # ceiling rather than a safety one.
    LINK_PREVIEW_MAX_REDIRECTS: int = 3

    # A day: Open Graph tags change rarely, and a stale title is a much smaller
    # problem than re-fetching a popular link for every reader.
    LINK_PREVIEW_CACHE_TTL_SECONDS: int = 86400

    # Failures are cached far more briefly, so a site that was down for five
    # minutes is not written off for a day.
    LINK_PREVIEW_FAILURE_CACHE_TTL_SECONDS: int = 300

    # Identifying ourselves honestly, with a contact URL, is what lets a site
    # owner rate-limit us instead of silently blackholing us.
    LINK_PREVIEW_USER_AGENT: str = (
        "DevLinkBot/1.0 (+https://github.com/nensii21/devlink)"
    )

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
