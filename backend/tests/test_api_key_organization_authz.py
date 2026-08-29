"""
Ownership checks for API keys, for both owner shapes.

An `ApiKey` belongs either to a user (`user_id` set, `organization_id` NULL) or
to an organisation (the reverse). Every ownership check was written as::

    if key.user_id and key.user_id != actor.id and not actor.is_superuser:

For an organisation key `key.user_id` is `None`, the `and` short-circuits on
the first operand, and no check runs at all. There are no organisation-scoped
read/update/regenerate/revoke routes, so organisation keys are managed through
the personal `/api/v1/api-keys/{key_id}` routes -- which meant any authenticated
user could regenerate an organisation's key and be handed the new plaintext in
the response.

These tests are integration tests against a real session rather than the
`MagicMock` style of `test_api_key_management.py`, because the bug is about
which *row* is being authorised against, and a mock will happily agree with
whatever the code asks it.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrgMemberRole
from app.models.user import User
from app.services.api_key_service import ApiKeyService


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
def org_owner(register_and_login):
    return _account(register_and_login, "orgowner@example.com", "orgowner")


@pytest.fixture
def org_member(register_and_login):
    """In the organisation, but as a plain member -- no `org:manage_tokens`."""
    return _account(register_and_login, "orgmember@example.com", "orgmember")


@pytest.fixture
def org_admin(register_and_login):
    """In the organisation as an admin, which does carry `org:manage_tokens`."""
    return _account(register_and_login, "orgadmin@example.com", "orgadmin")


@pytest.fixture
def stranger(register_and_login):
    """Authenticated, and has nothing to do with the organisation."""
    return _account(register_and_login, "stranger@example.com", "strangeruser")


@pytest.fixture
def organization(db, org_owner, org_member, org_admin) -> Organization:
    org = Organization(
        owner_id=org_owner["uuid"],
        name="Acme Robotics",
        slug="acme-robotics",
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    db.add_all(
        [
            OrganizationMember(
                organization_id=org.id,
                user_id=org_member["uuid"],
                role=OrgMemberRole.MEMBER,
                is_active=True,
            ),
            OrganizationMember(
                organization_id=org.id,
                user_id=org_admin["uuid"],
                role=OrgMemberRole.ADMIN,
                is_active=True,
            ),
        ]
    )
    db.commit()
    return org


@pytest.fixture
def org_key(db, organization, org_owner) -> ApiKey:
    """An organisation key: `user_id` NULL, `organization_id` set.

    Built directly rather than through the create route so the test does not
    depend on that route's own guard being correct.
    """
    raw, prefix, hashed = ApiKeyService.generate_raw_key()
    key = ApiKey(
        id=uuid.uuid4(),
        user_id=None,
        organization_id=organization.id,
        created_by_id=org_owner["uuid"],
        name="CI deploy key",
        prefix=prefix,
        hashed_key=hashed,
        scopes=["read:projects"],
        is_active=True,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


@pytest.fixture
def personal_key(db, org_owner) -> ApiKey:
    raw, prefix, hashed = ApiKeyService.generate_raw_key()
    key = ApiKey(
        id=uuid.uuid4(),
        user_id=org_owner["uuid"],
        organization_id=None,
        created_by_id=org_owner["uuid"],
        name="Laptop key",
        prefix=prefix,
        hashed_key=hashed,
        scopes=["read:projects"],
        is_active=True,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


def _routes(key_id) -> list[tuple[str, str]]:
    return [
        ("GET", f"/api/v1/api-keys/{key_id}"),
        ("PATCH", f"/api/v1/api-keys/{key_id}"),
        ("POST", f"/api/v1/api-keys/{key_id}/regenerate"),
        ("POST", f"/api/v1/api-keys/{key_id}/revoke"),
        ("DELETE", f"/api/v1/api-keys/{key_id}"),
    ]


def _call(client: TestClient, method: str, path: str, headers: dict | None = None):
    kwargs = {"headers": headers} if headers else {}
    if method == "PATCH":
        kwargs["json"] = {"name": "renamed"}
    return client.request(method, path, **kwargs)


# ---------------------------------------------------------------------------
# The reported bug
# ---------------------------------------------------------------------------


class TestOrganizationKeyIsNotOpenToEveryone:
    def test_stranger_is_refused_on_every_management_route(
        self, client: TestClient, org_key, stranger
    ):
        for method, path in _routes(org_key.id):
            response = _call(client, method, path, stranger["headers"])
            assert response.status_code == 403, (
                f"{method} {path} returned {response.status_code}"
            )

    def test_stranger_cannot_regenerate_and_be_handed_the_secret(
        self, client: TestClient, org_key, stranger, db
    ):
        """The sharpest form of the bug.

        `regenerate` writes a fresh `hashed_key` and returns the plaintext, so
        the attacker did not read an existing secret -- they replaced it with
        one they knew and were given it, breaking the organisation's real
        integrations in the same request.
        """
        before = org_key.hashed_key

        response = client.post(
            f"/api/v1/api-keys/{org_key.id}/regenerate",
            headers=stranger["headers"],
        )
        assert response.status_code == 403
        assert "raw_key" not in response.text

        db.refresh(org_key)
        assert org_key.hashed_key == before

    def test_stranger_cannot_widen_the_scopes(
        self, client: TestClient, org_key, stranger, db
    ):
        """`full_access` validates, and `authenticate_api_key` treats it as a
        wildcard, so a successful PATCH here was a full privilege escalation."""
        response = client.patch(
            f"/api/v1/api-keys/{org_key.id}",
            headers=stranger["headers"],
            json={"scopes": ["full_access"]},
        )
        assert response.status_code == 403

        db.refresh(org_key)
        assert org_key.scopes == ["read:projects"]

    def test_stranger_cannot_revoke_the_key(
        self, client: TestClient, org_key, stranger, db
    ):
        """Revocation is the denial-of-service form: one request per key."""
        response = client.post(
            f"/api/v1/api-keys/{org_key.id}/revoke", headers=stranger["headers"]
        )
        assert response.status_code == 403

        db.refresh(org_key)
        assert org_key.is_active is True

    def test_stranger_cannot_read_the_metadata(
        self, client: TestClient, org_key, stranger
    ):
        """The read route is how you pick a target worth regenerating."""
        response = client.get(
            f"/api/v1/api-keys/{org_key.id}", headers=stranger["headers"]
        )
        assert response.status_code == 403

    def test_anonymous_caller_is_refused(self, client: TestClient, org_key):
        for method, path in _routes(org_key.id):
            response = _call(client, method, path)
            assert response.status_code == 401


# ---------------------------------------------------------------------------
# Membership is not enough; the permission is
# ---------------------------------------------------------------------------


class TestOrganizationMembershipIsNotEnough:
    def test_plain_member_is_refused(self, client: TestClient, org_key, org_member):
        """`ORG_ROLE_PERMISSIONS[MEMBER]` does not include `org:manage_tokens`.

        Being in the organisation is not the same as being allowed to manage
        its credentials -- which is exactly the distinction the create and list
        routes already draw with `require_org_permission(ORG_MANAGE_TOKENS)`.
        """
        for method, path in _routes(org_key.id):
            response = _call(client, method, path, org_member["headers"])
            assert response.status_code == 403


class TestPermittedCallers:
    def test_org_owner_can_read(self, client: TestClient, org_key, org_owner):
        response = client.get(
            f"/api/v1/api-keys/{org_key.id}", headers=org_owner["headers"]
        )
        assert response.status_code == 200
        assert response.json()["name"] == "CI deploy key"

    def test_org_owner_can_regenerate(
        self, client: TestClient, org_key, org_owner, db
    ):
        before = org_key.hashed_key

        response = client.post(
            f"/api/v1/api-keys/{org_key.id}/regenerate", headers=org_owner["headers"]
        )
        assert response.status_code == 200
        assert response.json()["raw_key"].startswith("dlk_live_")

        db.refresh(org_key)
        assert org_key.hashed_key != before

    def test_org_admin_can_manage(self, client: TestClient, org_key, org_admin, db):
        """`ADMIN` carries `org:manage_tokens`, so it passes."""
        renamed = client.patch(
            f"/api/v1/api-keys/{org_key.id}",
            headers=org_admin["headers"],
            json={"name": "CI deploy key v2"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["name"] == "CI deploy key v2"

    def test_org_admin_can_revoke(self, client: TestClient, org_key, org_admin, db):
        response = client.post(
            f"/api/v1/api-keys/{org_key.id}/revoke", headers=org_admin["headers"]
        )
        assert response.status_code == 200

        db.refresh(org_key)
        assert org_key.is_active is False


# ---------------------------------------------------------------------------
# Personal keys must still behave exactly as before
# ---------------------------------------------------------------------------


class TestPersonalKeysUnchanged:
    def test_owner_can_manage_their_own_key(
        self, client: TestClient, personal_key, org_owner
    ):
        response = client.get(
            f"/api/v1/api-keys/{personal_key.id}", headers=org_owner["headers"]
        )
        assert response.status_code == 200

    def test_someone_else_cannot(self, client: TestClient, personal_key, stranger):
        for method, path in _routes(personal_key.id):
            response = _call(client, method, path, stranger["headers"])
            assert response.status_code == 403

    def test_an_org_admin_has_no_claim_on_a_personal_key(
        self, client: TestClient, personal_key, org_admin
    ):
        """Holding `org:manage_tokens` must not reach across into personal keys."""
        response = client.get(
            f"/api/v1/api-keys/{personal_key.id}", headers=org_admin["headers"]
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# The service predicate, directly
# ---------------------------------------------------------------------------


class TestCanManage:
    def test_ownerless_key_is_denied(self, db, organization, org_owner, stranger):
        """A key with neither owner column set is a data error, not a free-for-all.

        The old expression treated it as unowned and therefore unguarded --
        precisely backwards for an unattributable credential.
        """
        raw, prefix, hashed = ApiKeyService.generate_raw_key()
        orphan = ApiKey(
            id=uuid.uuid4(),
            user_id=None,
            organization_id=None,
            created_by_id=org_owner["uuid"],
            name="Orphan",
            prefix=prefix,
            hashed_key=hashed,
            scopes=[],
            is_active=True,
        )
        db.add(orphan)
        db.commit()

        actor = db.get(User, stranger["uuid"])
        assert ApiKeyService.can_manage(db, orphan, actor) is False

    def test_superuser_can_manage_anything(self, db, org_key, stranger):
        actor = db.get(User, stranger["uuid"])
        actor.is_superuser = True
        db.add(actor)
        db.commit()

        assert ApiKeyService.can_manage(db, org_key, actor) is True

    def test_org_permission_is_scoped_to_the_right_organization(
        self, db, org_key, org_admin, org_owner
    ):
        """Admin of *another* organisation gets nothing.

        A permission check that ignored `key.organization_id` would pass here.
        """
        other = Organization(
            owner_id=org_admin["uuid"],
            name="Other Corp",
            slug="other-corp",
        )
        db.add(other)
        db.commit()
        db.refresh(other)

        raw, prefix, hashed = ApiKeyService.generate_raw_key()
        other_key = ApiKey(
            id=uuid.uuid4(),
            user_id=None,
            organization_id=other.id,
            created_by_id=org_admin["uuid"],
            name="Other key",
            prefix=prefix,
            hashed_key=hashed,
            scopes=[],
            is_active=True,
        )
        db.add(other_key)
        db.commit()

        owner_actor = db.get(User, org_owner["uuid"])
        assert ApiKeyService.can_manage(db, other_key, owner_actor) is False
        assert ApiKeyService.can_manage(db, org_key, owner_actor) is True


# ---------------------------------------------------------------------------
# Revoked keys are not listed
# ---------------------------------------------------------------------------


class TestRevokedKeysAreExcluded:
    def test_revoked_key_is_not_listed_by_default(
        self, client: TestClient, personal_key, org_owner, db
    ):
        """The filter was a comment and an unrelated `order_by`.

        A revoked key stayed in the list looking much like a live one, and the
        pagination total counted it.
        """
        listed = client.get("/api/v1/api-keys/", headers=org_owner["headers"])
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        personal_key.is_active = False
        db.add(personal_key)
        db.commit()

        listed = client.get("/api/v1/api-keys/", headers=org_owner["headers"])
        assert listed.json()["total"] == 0
        assert listed.json()["items"] == []

    def test_include_revoked_brings_it_back(
        self, client: TestClient, personal_key, org_owner, db
    ):
        personal_key.is_active = False
        db.add(personal_key)
        db.commit()

        listed = client.get(
            "/api/v1/api-keys/",
            params={"include_revoked": True},
            headers=org_owner["headers"],
        )
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["name"] == "Laptop key"

    def test_org_listing_excludes_revoked_too(
        self, client: TestClient, organization, org_key, org_owner, db
    ):
        base = f"/api/v1/organizations/{organization.id}/api-keys/"

        listed = client.get(base, headers=org_owner["headers"])
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        org_key.is_active = False
        db.add(org_key)
        db.commit()

        listed = client.get(base, headers=org_owner["headers"])
        assert listed.json()["total"] == 0
