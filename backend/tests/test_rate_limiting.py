from __future__ import annotations

import pytest
from app.core.config import Settings, settings
from app.middleware.rate_limit import (
    COMMENT_LIMIT,
    AUTH_LIMIT,
    MESSAGE_LIMIT,
    PASSWORD_RESET_LIMIT,
    SEARCH_LIMIT,
    limiter,
)


def test_rate_limit_settings_defined():
    """The rate-limit defaults declared in `app/core/config.py`.

    Built from a Settings subclass with `env_file` disabled, deliberately.
    pydantic-settings loads `backend/.env` automatically, so asserting against
    the module-level `settings` singleton tests whatever the machine happens to
    have configured rather than what the code declares.

    That is not hypothetical: this test asserted SEARCH_RATE_LIMIT == "60/minute"
    and passed everywhere, because the committed `backend/.env` set that value
    and silently overrode the "30/minute" in config.py. Untracking the .env
    made the discrepancy visible. Reading the defaults directly means the test
    means the same thing on CI and on a contributor's machine, whatever they
    have in their own .env.
    """

    class DeclaredDefaults(Settings):
        model_config = {**Settings.model_config, "env_file": None}

    defaults = DeclaredDefaults()

    assert defaults.PASSWORD_RESET_RATE_LIMIT == "3/15minutes"
    assert defaults.MESSAGE_RATE_LIMIT == "30/minute"
    assert defaults.COMMENT_RATE_LIMIT == "30/minute"
    assert defaults.SEARCH_RATE_LIMIT == "30/minute"


def test_rate_limit_settings_are_readable_from_the_active_config():
    """Whatever the environment supplies, the settings must exist and parse."""
    for name in (
        "PASSWORD_RESET_RATE_LIMIT",
        "MESSAGE_RATE_LIMIT",
        "COMMENT_RATE_LIMIT",
        "SEARCH_RATE_LIMIT",
    ):
        value = getattr(settings, name)

        assert isinstance(value, str) and "/" in value, f"{name} is not a limit"


def test_rate_limit_constants_exported():
    """Verify exported rate limit constants exist and are usable by routers."""
    assert AUTH_LIMIT is not None
    assert PASSWORD_RESET_LIMIT is not None
    assert MESSAGE_LIMIT is not None
    assert COMMENT_LIMIT is not None
    assert SEARCH_LIMIT is not None


def test_limiter_instance_configured():
    """Verify global Limiter instance is initialized."""
    assert limiter is not None
