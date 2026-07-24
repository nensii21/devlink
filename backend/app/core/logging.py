import logging
import logging.config
from pathlib import Path

from app.core.config import settings

# ---------------------------------------------------------------------
# Create logs directory
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "devlink.log"

# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": ("[%(asctime)s] " "[%(levelname)s] " "[%(name)s] " "%(message)s"),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "format": (
                "%(asctime)s | "
                "%(levelname)s | "
                "%(clientip)s | "
                "%(request)s | "
                "%(status)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": settings.LOG_LEVEL,
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_FILE),
            "formatter": "default",
            "encoding": "utf-8",
            "level": settings.LOG_LEVEL,
        },
    },
    "root": {
        "handlers": [
            "console",
            "file",
        ],
        "level": settings.LOG_LEVEL,
    },
}


# ---------------------------------------------------------------------
# Configure Logging
# ---------------------------------------------------------------------

logging.config.dictConfig(LOGGING_CONFIG)


# ---------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger.

    Example:
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------
# Application Logger
# ---------------------------------------------------------------------

logger = get_logger("devlink")


# ---------------------------------------------------------------------
# Startup Logs
# ---------------------------------------------------------------------


def log_startup() -> None:
    logger.info("=" * 60)
    logger.info("Starting DevLink Backend")
    logger.info(f"Environment : {settings.ENVIRONMENT}")
    logger.info(f"Debug       : {settings.DEBUG}")
    logger.info(f"Version     : {settings.APP_VERSION}")
    logger.info("=" * 60)


# ---------------------------------------------------------------------
# Shutdown Logs
# ---------------------------------------------------------------------


def log_shutdown() -> None:
    logger.info("=" * 60)
    logger.info("Stopping DevLink Backend")
    logger.info("=" * 60)


# ---------------------------------------------------------------------
# Security Logging
# ---------------------------------------------------------------------


def log_security_event(
    event: str,
    user: str | None = None,
    ip: str | None = None,
) -> None:
    """
    Log security-related events.

    Examples:
        Failed login
        Password reset
        Token refresh
        Account lock
    """

    logger.warning(
        f"[SECURITY] {event} | user={user or 'anonymous'} | ip={ip or 'unknown'}"
    )


# ---------------------------------------------------------------------
# API Logging
# ---------------------------------------------------------------------


def log_request(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> None:
    logger.info(
        f"[{request_id}] "
        f"{method} {path} "
        f"status={status_code} "
        f"time={duration_ms:.2f}ms"
    )


# ---------------------------------------------------------------------
# Exception Logging
# ---------------------------------------------------------------------


def log_exception(exc: Exception) -> None:
    logger.exception(str(exc))
