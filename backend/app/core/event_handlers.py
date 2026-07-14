from typing import Any
import logging
from app.core.logging import log_security_event

logger = logging.getLogger(__name__)


def on_user_registered(email: str, user_id: str, **kwargs: Any) -> None:
    """Handler for USER_REGISTERED event."""
    log_security_event(
        event="New user registration",
        user=email,
    )


def on_user_login(email: str, **kwargs: Any) -> None:
    """Handler for USER_LOGIN event."""
    log_security_event(
        event="Successful login",
        user=email,
    )


def on_user_logout(email: str, **kwargs: Any) -> None:
    """Handler for USER_LOGOUT event."""
    log_security_event(
        event="Logout",
        user=email,
    )


def on_password_changed(email: str, **kwargs: Any) -> None:
    """Handler for PASSWORD_CHANGED event."""
    log_security_event(
        event="Password changed",
        user=email,
    )


def on_password_reset_requested(email: str, **kwargs: Any) -> None:
    """Handler for PASSWORD_RESET_REQUESTED event."""
    log_security_event(
        event="Password reset requested",
        user=email,
    )


def on_password_reset_completed(email: str, **kwargs: Any) -> None:
    """Handler for PASSWORD_RESET_COMPLETED event."""
    log_security_event(
        event="Password reset completed",
        user=email,
    )


def on_email_verified(email: str, **kwargs: Any) -> None:
    """Handler for EMAIL_VERIFIED event."""
    log_security_event(
        event="Email verified",
        user=email,
    )


def on_access_token_refreshed(email: str, **kwargs: Any) -> None:
    """Handler for ACCESS_TOKEN_REFRESHED event."""
    log_security_event(
        event="Access token refreshed",
        user=email,
    )


def register_all_handlers(event_bus) -> None:
    """Register all event handlers to the provided event bus."""
    event_bus.subscribe("USER_REGISTERED", on_user_registered)
    event_bus.subscribe("USER_LOGIN", on_user_login)
    event_bus.subscribe("USER_LOGOUT", on_user_logout)
    event_bus.subscribe("PASSWORD_CHANGED", on_password_changed)
    event_bus.subscribe("PASSWORD_RESET_REQUESTED", on_password_reset_requested)
    event_bus.subscribe("PASSWORD_RESET_COMPLETED", on_password_reset_completed)
    event_bus.subscribe("EMAIL_VERIFIED", on_email_verified)
    event_bus.subscribe("ACCESS_TOKEN_REFRESHED", on_access_token_refreshed)
    logger.info("All event handlers successfully registered.")
