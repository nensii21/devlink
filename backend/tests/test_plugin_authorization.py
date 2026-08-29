"""
Authorization for the plugin system.

Two holes, which compounded:

1. `POST /api/plugins/dispatch-event` needed no token, and its response listed
   every enabled installation on the platform together with each one's
   `webhook_url` -- and an integration webhook URL is a bearer credential in
   practice, postable by anyone holding the string.
2. `install_plugin`, `uninstall_plugin` and `list_user_installations` took
   `organization_id` straight from the request and never checked the caller
   belonged to that organisation. Since an installation is what
   `dispatch_event` fans out over, that was also how an attacker attached a
   webhook destination of their own choosing to somebody else's event stream.

`update_installation` was the odd one out: it checked, but only the personal
case, so an organisation's own admins could not disable a plugin installed on
them.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.rbac import ORG_MANAGE_PLUGINS, has_org_permission
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrgMemberRole
from app.models.plugin import Plugin, PluginInstallation, PluginStatus, PluginType
from app.models.user import User
from app.services.plugin_service import PluginService

WEBHOOK = "https://hooks.example.com/services/T000/B000/secret-token"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _account(register_and_login, email: str, username: str) -> dict:
    uid, token = register_and_login(email, username)
    return {
        "id": uid,
        "uuid": uuid.UUID(uid),
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def author(register_and_login):
    return _account(register_and_login, "author@example.com", "pluginauthor")


@pytest.fixture
def org_owner(register_and_login):
    return _account(register_and_login, "plugowner@example.com", "plugowner")


@pytest.fixture
def org_member(register_and_login):
    """In the organisation as a plain member -- no `org:manage_plugins`."""
    return _account(register_and_login, "plugmember@example.com", "plugmember")


@pytest.fixture
def stranger(register_and_login):
    return _account(register_and_login, "plugstranger@example.com", "plugstranger")


@pytest.fixture
def admin(register_and_login, db):
    acct = _account(register_and_login, "plugadmin@example.com", "plugadmin")
    user = db.get(User, acct["uuid"])
    user.system_role = "admin"
    db.add(user)
    db.commit()
    return acct


@pytest.fixture
def organization(db, org_owner, org_member) -> Organization:
    org = Organization(
        owner_id=org_owner["uuid"],
        name="Widget Works",
        slug="widget-works",
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    db.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=org_member["uuid"],
            role=OrgMemberRole.MEMBER,
            is_active=True,
        )
    )
    db.commit()
    return org


@pytest.fixture
def plugin(db, author) -> Plugin:
    p = Plugin(
        id=uuid.uuid4(),
        name="Chat Notifier",
        slug="chat-notifier",
        description="Posts project events to a chat channel.",
        version="1.0.0",
        author_id=author["uuid"],
        plugin_type=PluginType.INTEGRATION,
        status=PluginStatus.ACTIVE,
        manifest={
            "extension_points": ["on_project_created"],
            "webhook_url": WEBHOOK,
        },
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def org_installation(db, plugin, organization) -> PluginInstallation:
    inst = PluginInstallation(
        id=uuid.uuid4(),
        plugin_id=plugin.id,
        user_id=None,
        organization_id=organization.id,
        is_enabled=True,
        config={"channel": "#builds"},
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


# ---------------------------------------------------------------------------
# dispatch-event
# ---------------------------------------------------------------------------


class TestDispatchEventRequiresAdmin:
    def test_anonymous_caller_is_rejected(self, client: TestClient, org_installation):
        """The reported bug: this route took no token at all."""
        response = client.post(
            "/api/plugins/dispatch-event",
            json={"event": "on_project_created", "payload": {}},
        )
        assert response.status_code == 401

    def test_ordinary_user_is_rejected(
        self, client: TestClient, org_installation, stranger
    ):
        response = client.post(
            "/api/plugins/dispatch-event",
            json={"event": "on_project_created", "payload": {}},
            headers=stranger["headers"],
        )
        assert response.status_code == 403

    def test_the_plugin_author_is_not_special(
        self, client: TestClient, org_installation, author
    ):
        """Publishing a plugin does not grant the right to fan out events."""
        response = client.post(
            "/api/plugins/dispatch-event",
            json={"event": "on_project_created", "payload": {}},
            headers=author["headers"],
        )
        assert response.status_code == 403

    def test_admin_can_dispatch(self, client: TestClient, org_installation, admin):
        response = client.post(
            "/api/plugins/dispatch-event",
            json={"event": "on_project_created", "payload": {}},
            headers=admin["headers"],
        )
        assert response.status_code == 200
        assert response.json()["matched_plugins_count"] == 1
        assert response.json()["dispatched_installations_count"] == 1


class TestDispatchResponseDoesNotLeakWebhooks:
    def test_the_webhook_url_never_appears_in_the_response(
        self, client: TestClient, org_installation, admin
    ):
        """Defence in depth: even the permitted caller does not get the URL.

        A webhook destination is a bearer credential -- anyone holding the
        string can post as the integration -- and a dispatch result does not
        need to repeat the destination to say what happened.
        """
        response = client.post(
            "/api/plugins/dispatch-event",
            json={"event": "on_project_created", "payload": {}},
            headers=admin["headers"],
        )
        assert response.status_code == 200
        assert WEBHOOK not in response.text
        assert "webhook_url" not in response.text

    def test_a_boolean_reports_whether_one_is_configured(
        self, client: TestClient, org_installation, admin
    ):
        response = client.post(
            "/api/plugins/dispatch-event",
            json={"event": "on_project_created", "payload": {}},
            headers=admin["headers"],
        )
        item = response.json()["dispatches"][0]
        assert item["has_webhook"] is True
        assert item["status"] == "queued"

    def test_a_plugin_without_a_webhook_reports_false(
        self, client: TestClient, db, plugin, organization, admin
    ):
        plugin.manifest = {"extension_points": ["on_project_created"]}
        db.add(plugin)
        db.add(
            PluginInstallation(
                id=uuid.uuid4(),
                plugin_id=plugin.id,
                organization_id=organization.id,
                is_enabled=True,
                config={},
            )
        )
        db.commit()

        response = client.post(
            "/api/plugins/dispatch-event",
            json={"event": "on_project_created", "payload": {}},
            headers=admin["headers"],
        )
        item = response.json()["dispatches"][0]
        assert item["has_webhook"] is False
        assert item["status"] == "no_webhook"


# ---------------------------------------------------------------------------
# Installing into an organisation
# ---------------------------------------------------------------------------


class TestOrganizationInstallRequiresPermission:
    def test_stranger_cannot_install_into_an_organization(
        self, client: TestClient, plugin, organization, stranger, db
    ):
        response = client.post(
            f"/api/plugins/{plugin.id}/install",
            json={"organization_id": str(organization.id), "config": {}},
            headers=stranger["headers"],
        )
        assert response.status_code == 403

        assert (
            db.query(PluginInstallation)
            .filter(PluginInstallation.organization_id == organization.id)
            .count()
            == 0
        )

    def test_plain_member_cannot_install_into_their_own_organization(
        self, client: TestClient, plugin, organization, org_member
    ):
        """`ORG_ROLE_PERMISSIONS[MEMBER]` does not carry `org:manage_plugins`.

        Being in the organisation is not the same as being allowed to attach a
        third-party webhook to its event stream.
        """
        response = client.post(
            f"/api/plugins/{plugin.id}/install",
            json={"organization_id": str(organization.id), "config": {}},
            headers=org_member["headers"],
        )
        assert response.status_code == 403

    def test_org_owner_can_install(
        self, client: TestClient, plugin, organization, org_owner, db
    ):
        response = client.post(
            f"/api/plugins/{plugin.id}/install",
            json={"organization_id": str(organization.id), "config": {}},
            headers=org_owner["headers"],
        )
        assert response.status_code == 201
        assert response.json()["organization_id"] == str(organization.id)

    def test_personal_install_still_works_for_anyone(
        self, client: TestClient, plugin, stranger
    ):
        """The guard must only fire when an organisation is named."""
        response = client.post(
            f"/api/plugins/{plugin.id}/install",
            json={"config": {}},
            headers=stranger["headers"],
        )
        assert response.status_code == 201
        assert response.json()["user_id"] == stranger["id"]
        assert response.json()["organization_id"] is None


class TestOrganizationUninstallRequiresPermission:
    def test_stranger_cannot_remove_an_organizations_integration(
        self, client: TestClient, plugin, organization, org_installation, stranger, db
    ):
        response = client.delete(
            f"/api/plugins/{plugin.id}/install",
            params={"organization_id": str(organization.id)},
            headers=stranger["headers"],
        )
        assert response.status_code == 403

        db.expire_all()
        assert db.get(PluginInstallation, org_installation.id) is not None

    def test_org_owner_can_uninstall(
        self, client: TestClient, plugin, organization, org_installation, org_owner, db
    ):
        # Read the id before the request: after the row is gone, touching an
        # expired attribute on the instance raises ObjectDeletedError.
        installation_id = org_installation.id

        response = client.delete(
            f"/api/plugins/{plugin.id}/install",
            params={"organization_id": str(organization.id)},
            headers=org_owner["headers"],
        )
        assert response.status_code in (200, 204)

        # The delete happened in the request's session, so this one still holds
        # the row in its identity map. Expire before re-reading.
        db.expire_all()
        assert db.get(PluginInstallation, installation_id) is None


class TestOrganizationListingRequiresPermission:
    def test_stranger_cannot_enumerate_an_organizations_installations(
        self, client: TestClient, organization, org_installation, stranger
    ):
        """The listing discloses which integrations an organisation runs, and
        the config they run with."""
        response = client.get(
            "/api/plugins/installed/me",
            params={"organization_id": str(organization.id)},
            headers=stranger["headers"],
        )
        assert response.status_code == 403

    def test_org_owner_can_list(
        self, client: TestClient, organization, org_installation, org_owner
    ):
        response = client.get(
            "/api/plugins/installed/me",
            params={"organization_id": str(organization.id)},
            headers=org_owner["headers"],
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_listing_your_own_installations_needs_nothing(
        self, client: TestClient, stranger
    ):
        response = client.get(
            "/api/plugins/installed/me", headers=stranger["headers"]
        )
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# update_installation
# ---------------------------------------------------------------------------


class TestUpdateInstallation:
    def test_org_owner_can_disable_an_org_installation(
        self, client: TestClient, org_installation, org_owner, db
    ):
        """This used to be refused, which was the mirror-image bug.

        `installation.user_id != user.id` held for everybody on an
        organisation installation, because `user_id` is NULL there -- so the
        organisation's own admins had no way to turn off a plugin somebody
        else had installed on them.
        """
        response = client.patch(
            f"/api/plugins/installations/{org_installation.id}",
            json={"is_enabled": False},
            headers=org_owner["headers"],
        )
        assert response.status_code == 200

        db.refresh(org_installation)
        assert org_installation.is_enabled is False

    def test_stranger_cannot_reconfigure_an_org_installation(
        self, client: TestClient, org_installation, stranger, db
    ):
        response = client.patch(
            f"/api/plugins/installations/{org_installation.id}",
            json={"config": {"channel": "#attacker"}},
            headers=stranger["headers"],
        )
        assert response.status_code == 403

        db.refresh(org_installation)
        assert org_installation.config == {"channel": "#builds"}

    def test_plain_member_cannot_reconfigure(
        self, client: TestClient, org_installation, org_member
    ):
        response = client.patch(
            f"/api/plugins/installations/{org_installation.id}",
            json={"is_enabled": False},
            headers=org_member["headers"],
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# The predicates, directly
# ---------------------------------------------------------------------------


class TestPermissionWiring:
    def test_org_manage_plugins_is_granted_to_owner_and_admin_only(
        self, db, organization, org_owner, org_member, stranger
    ):
        assert has_org_permission(
            db, org_owner["uuid"], organization.id, ORG_MANAGE_PLUGINS
        )
        assert not has_org_permission(
            db, org_member["uuid"], organization.id, ORG_MANAGE_PLUGINS
        )
        assert not has_org_permission(
            db, stranger["uuid"], organization.id, ORG_MANAGE_PLUGINS
        )

    def test_can_manage_installation_handles_both_owner_shapes(
        self, db, plugin, organization, org_installation, org_owner, stranger
    ):
        personal = PluginInstallation(
            id=uuid.uuid4(),
            plugin_id=plugin.id,
            user_id=stranger["uuid"],
            organization_id=None,
            is_enabled=True,
            config={},
        )
        db.add(personal)
        db.commit()

        owner_user = db.get(User, org_owner["uuid"])
        stranger_user = db.get(User, stranger["uuid"])

        # Organisation installation: the org's owner, not the personal owner.
        assert PluginService.can_manage_installation(db, owner_user, org_installation)
        assert not PluginService.can_manage_installation(
            db, stranger_user, org_installation
        )

        # Personal installation: the reverse.
        assert PluginService.can_manage_installation(db, stranger_user, personal)
        assert not PluginService.can_manage_installation(db, owner_user, personal)

    def test_an_ownerless_installation_is_denied(self, db, plugin, stranger):
        orphan = PluginInstallation(
            id=uuid.uuid4(),
            plugin_id=plugin.id,
            user_id=None,
            organization_id=None,
            is_enabled=True,
            config={},
        )
        db.add(orphan)
        db.commit()

        stranger_user = db.get(User, stranger["uuid"])
        assert not PluginService.can_manage_installation(db, stranger_user, orphan)

    def test_permission_is_scoped_to_the_named_organization(
        self, db, organization, org_owner, stranger
    ):
        other = Organization(
            owner_id=stranger["uuid"],
            name="Other Works",
            slug="other-works",
        )
        db.add(other)
        db.commit()
        db.refresh(other)

        assert not has_org_permission(
            db, org_owner["uuid"], other.id, ORG_MANAGE_PLUGINS
        )
