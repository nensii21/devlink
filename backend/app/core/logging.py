from __future__ import annotations

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict

from app.core.config import settings

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "devlink.log"

SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "authorization",
    "cookie",
    "refreshtoken",
    "apikey",
    "access_token",
    "refresh_token",
}

# ---------------------------------------------------------------------
# Processors
# ---------------------------------------------------------------------


def redact_sensitive_data(
    logger: logging.Logger, name: str, event_dict: EventDict
) -> EventDict:
    """
    Recursively redact sensitive keys from log payload.
    """

    def redact(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else redact(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [redact(item) for item in obj]
        return obj

    # Redact event_dict in place
    for k, v in list(event_dict.items()):
        if k.lower() in SENSITIVE_KEYS:
            event_dict[k] = "[REDACTED]"
        elif isinstance(v, (dict, list)):
            event_dict[k] = redact(v)

    return event_dict


shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    redact_sensitive_data,
]

# ---------------------------------------------------------------------
# Setup Logging
# ---------------------------------------------------------------------


def configure_logging() -> None:
    # Setup structlog
    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Output renderer based on env
    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.ENVIRONMENT == "development"
        else structlog.processors.JSONRenderer()
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Standard logging setup
    handler_console = logging.StreamHandler(sys.stdout)
    handler_console.setFormatter(formatter)

    handler_file = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler_file.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []  # Clear default handlers

    # Set log level based on env
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    root_logger.setLevel(level)

    root_logger.addHandler(handler_console)
    root_logger.addHandler(handler_file)

    # Mute noisy loggers
    logging.getLogger("uvicorn.access").handlers = [handler_console, handler_file]
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").handlers = [handler_console, handler_file]
    logging.getLogger("uvicorn.error").propagate = False


# Call immediately
configure_logging()

# ---------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger configured for the application."""
    return structlog.get_logger(name)


logger = get_logger("devlink")

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def log_startup() -> None:
    logger.info(
        "starting_devlink_backend",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        version=settings.APP_VERSION,
    )


def log_shutdown() -> None:
    logger.info("stopping_devlink_backend")


def log_security_event(
    event: str, user: str | None = None, ip: str | None = None
) -> None:
    logger.warning("security_event", event=event, target_user=user, ip_address=ip)


def log_exception(exc: Exception) -> None:
    logger.exception("unhandled_exception", exc_info=exc)


def log_request(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> None:
    logger.info(
        "http_request",
        request_id=request_id,
        correlation_id=request_id,
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
    )
