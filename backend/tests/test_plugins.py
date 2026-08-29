"""
Unit & Integration Tests for DevLink Plugin & Extension System (#582)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.plugin import (
    Plugin,
    PluginInstallation,
    PluginStatus,
    PluginType,
)
from app.models.user import User
from app.schemas.plugin import (
    PluginCreate,
    PluginEventDispatchResult,
    PluginInstallationCreate,
    PluginManifestSchema,
    PluginUpdate,
)
from app.services.plugin_service import PluginService

# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(username: str = "devuser", system_role: str = "user") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    user.first_name = "Dev"
    user.last_name = "User"
    user.system_role = system_role
    user.role = system_role
    return user


def _make_mock_plugin(
    author_id: uuid.UUID | None = None,
    name: str = "CI/CD Status Widget",
    slug: str = "cicd-status-widget",
    plugin_type: PluginType = PluginType.WIDGET,
    extension_points: list[str] | None = None,
    webhook_url: str | None = "https://example.com/webhook",
) -> MagicMock:
    p = MagicMock(spec=Plugin)
    p.id = uuid.uuid4()
    p.name = name
    p.slug = slug
    p.description = "Displays live CI/CD pipeline build statuses."
    p.version = "1.0.0"
    p.author_id = author_id or uuid.uuid4()
    p.plugin_type = plugin_type
    p.status = PluginStatus.ACTIVE
    p.manifest = {
        "extension_points": extension_points
        or ["on_project_created", "dashboard_widget"],
        "webhook_url": webhook_url,
        "permissions": ["read_projects"],
        "widget_config": {"height": 250},
        "config_schema": {"type": "object"},
    }
    p.api_key_hash = "secret_key"
    p.is_verified = False
    p.is_official = False
    p.install_count = 0
    p.created_at = datetime.now(timezone.utc)
    p.updated_at = datetime.now(timezone.utc)
    return p


def _make_mock_installation(
    plugin: MagicMock,
    user_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    is_enabled: bool = True,
) -> MagicMock:
    inst = MagicMock(spec=PluginInstallation)
    inst.id = uuid.uuid4()
    inst.plugin_id = plugin.id
    inst.plugin = plugin
    inst.user_id = user_id
    inst.organization_id = org_id
    inst.is_enabled = is_enabled
    inst.config = {"theme": "dark"}
    inst.installed_at = datetime.now(timezone.utc)
    inst.updated_at = datetime.now(timezone.utc)
    return inst


# ---------------------------------------------------------------------------
# 1. Plugin Registration & Slug Tests
# ---------------------------------------------------------------------------


class TestPluginRegistration:
    def test_slugify(self):
        assert (
            PluginService._slugify("Slack Integration & Bot!")
            == "slack-integration-bot"
        )
        assert PluginService._slugify("  Custom Workflow  ") == "custom-workflow"

    def test_create_plugin_success(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None  # No existing slug collision

        author = _make_mock_user()
        plugin_in = PluginCreate(
            name="Jira Sync Integration",
            slug="jira-sync",
            description="Synchronize issues with Jira Cloud.",
            version="1.2.0",
            plugin_type=PluginType.INTEGRATION,
            manifest=PluginManifestSchema(
                extension_points=["on_issue_created"],
                webhook_url="https://jira.example.com/events",
            ),
        )

        plugin = PluginService.create_plugin(db, plugin_in, author)

        assert plugin.name == "Jira Sync Integration"
        assert plugin.slug == "jira-sync"
        assert plugin.author_id == author.id
        assert plugin.plugin_type == PluginType.INTEGRATION
        assert plugin.manifest["extension_points"] == ["on_issue_created"]
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_create_plugin_duplicate_slug_raises_400(self):
        db = MagicMock(spec=Session)
        existing = _make_mock_plugin()
        db.scalar.return_value = existing

        author = _make_mock_user()
        plugin_in = PluginCreate(
            name="Existing Plugin",
            slug="cicd-status-widget",
            description="Duplicate test",
            manifest=PluginManifestSchema(),
        )

        with pytest.raises(HTTPException) as exc_info:
            PluginService.create_plugin(db, plugin_in, author)
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# 2. Retrieval, Update & Verification Tests
# ---------------------------------------------------------------------------


class TestPluginManagement:
    def test_get_plugin_or_404_found(self):
        db = MagicMock(spec=Session)
        plugin = _make_mock_plugin()
        db.get.return_value = plugin

        res = PluginService.get_plugin_or_404(db, plugin.id)
        assert res == plugin

    def test_get_plugin_or_404_not_found(self):
        db = MagicMock(spec=Session)
        db.get.return_value = None
        db.scalar.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            PluginService.get_plugin_or_404(db, "unknown-slug")
        assert exc_info.value.status_code == 404

    def test_update_plugin_by_author(self):
        db = MagicMock(spec=Session)
        author = _make_mock_user()
        plugin = _make_mock_plugin(author_id=author.id)
        db.get.return_value = plugin

        update_in = PluginUpdate(name="Updated Widget Name", version="1.1.0")
        updated = PluginService.update_plugin(db, plugin.id, update_in, author)

        assert updated.name == "Updated Widget Name"
        assert updated.version == "1.1.0"

    def test_update_plugin_unauthorized_raises_403(self):
        db = MagicMock(spec=Session)
        author = _make_mock_user()
        other_user = _make_mock_user(system_role="user")
        plugin = _make_mock_plugin(author_id=author.id)
        db.get.return_value = plugin

        update_in = PluginUpdate(name="Hacked Name")
        with pytest.raises(HTTPException) as exc_info:
            PluginService.update_plugin(db, plugin.id, update_in, other_user)
        assert exc_info.value.status_code == 403

    def test_verify_plugin_admin(self):
        db = MagicMock(spec=Session)
        plugin = _make_mock_plugin()
        db.get.return_value = plugin

        res = PluginService.verify_plugin(
            db, plugin.id, is_verified=True, is_official=True
        )
        assert res.is_verified is True
        assert res.is_official is True


# ---------------------------------------------------------------------------
# 3. Installation & Uninstallation Tests
# ---------------------------------------------------------------------------


class TestPluginInstallationService:
    def test_install_plugin_user_success(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        plugin = _make_mock_plugin()
        db.get.return_value = plugin
        db.scalar.return_value = None  # Not installed yet

        inst_in = PluginInstallationCreate(config={"token": "abc"})
        inst = PluginService.install_plugin(db, plugin.id, user, inst_in)

        assert plugin.install_count == 1
        db.add.assert_called()
        db.commit.assert_called()

    def test_install_plugin_already_installed_raises_400(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        plugin = _make_mock_plugin()
        existing_inst = _make_mock_installation(plugin, user_id=user.id)
        db.get.return_value = plugin
        db.scalar.return_value = existing_inst

        with pytest.raises(HTTPException) as exc_info:
            PluginService.install_plugin(
                db, plugin.id, user, PluginInstallationCreate()
            )
        assert exc_info.value.status_code == 400

    def test_uninstall_plugin_success(self):
        db = MagicMock(spec=Session)
        user = _make_mock_user()
        plugin = _make_mock_plugin()
        plugin.install_count = 1
        inst = _make_mock_installation(plugin, user_id=user.id)

        db.get.return_value = plugin
        db.scalar.return_value = inst

        PluginService.uninstall_plugin(db, plugin.id, user)
        assert plugin.install_count == 0
        db.delete.assert_called_once_with(inst)
        db.commit.assert_called()


# ---------------------------------------------------------------------------
# 4. Event Dispatch & Workflow Hooks Tests
# ---------------------------------------------------------------------------


class TestPluginEventDispatch:
    def test_dispatch_event_matches_and_queues_webhook(self):
        db = MagicMock(spec=Session)
        plugin = _make_mock_plugin(extension_points=["on_project_created"])
        inst = _make_mock_installation(plugin, is_enabled=True)

        db.scalars.return_value.all.side_effect = [
            [plugin],  # Active plugins matching
            [inst],  # Enabled installations
        ]

        result = PluginService.dispatch_event(
            db, event="on_project_created", payload={"project_id": str(uuid.uuid4())}
        )

        assert isinstance(result, PluginEventDispatchResult)
        assert result.event == "on_project_created"
        assert result.matched_plugins_count == 1
        assert result.dispatched_installations_count == 1
        assert result.dispatches[0].plugin_slug == plugin.slug
        assert result.dispatches[0].status == "queued"
        # The manifest declares a webhook, so the flag is set -- but the URL
        # itself must not come back in the response.
        assert result.dispatches[0].has_webhook is True
        assert not hasattr(result.dispatches[0], "webhook_url")
