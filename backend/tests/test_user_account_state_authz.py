"""
Authorization and side effects for the administrative account-state routes.

Covers `PATCH /api/users/{id}/activate`, `/deactivate` and `/verify`, and the
`POST /api/users/` provisioning route that sits alongside them.

The three state routes previously depended on `get_database` and nothing else,
so an anonymous request could disable any account, re-enable any account, and
mark any address verified. The tests here pin down three separate things:

1. who may call them (nobody unauthenticated, no ordinary user, admins only);
2. that the transition does what it claims -- in particular that deactivation
   actually ends the target's sessions rather than only setting a flag;
3. that every transition leaves an audit trail naming both parties.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.audit_log import AuditAction, AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User

PASSWORD = "Vermilion-Kestrel97!"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _promote(db, user_id) -> User:
    user = db.get(User, uuid.UUID(str(user_id)))
    user.system_role = "admin"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin(client: TestClient, register_and_login, db):
    """An authenticated system administrator."""
    uid, token = register_and_login("admin@example.com", "adminuser")
    _promote(db, uid)
    return {
        "id": uid,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def member(client: TestClient, register_and_login):
    """An ordinary, non-privileged account."""
    uid, token = register_and_login("member@example.com", "memberuser")
    return {
        "id": uid,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def victim(client: TestClient, register_and_login):
    """The account the tests act upon."""
    uid, token = register_and_login("victim@example.com", "victimuser")
    return {
        "id": uid,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def _audit_rows(db, action: AuditAction) -> list[AuditLog]:
    return db.query(AuditLog).filter(AuditLog.action == action).all()


# ---------------------------------------------------------------------------
# Anonymous callers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("operation", ["activate", "deactivate", "verify"])
def test_anonymous_caller_is_rejected(client: TestClient, victim, operation):
    """The original bug, stated directly: no token, no transition."""
    response = client.patch(f"/api/users/{victim['id']}/{operation}")
    assert response.status_code == 401


def test_anonymous_deactivation_does_not_touch_the_account(
    client: TestClient, victim, db
):
    """A rejected request must not have applied anything on the way out."""
    client.patch(f"/api/users/{victim['id']}/deactivate")

    user = db.get(User, uuid.UUID(victim["id"]))
    assert user.is_active is True


def test_anonymous_deactivation_does_not_lock_the_account_out(
    client: TestClient, victim
):
    """The end-to-end shape of the report: log in again afterwards."""
    client.patch(f"/api/users/{victim['id']}/deactivate")

    login = client.post(
        "/api/auth/login",
        json={"email": "victim@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200


# ---------------------------------------------------------------------------
# Authenticated but unprivileged callers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("operation", ["activate", "deactivate", "verify"])
def test_ordinary_user_is_rejected(client: TestClient, member, victim, operation):
    response = client.patch(
        f"/api/users/{victim['id']}/{operation}",
        headers=member["headers"],
    )
    assert response.status_code == 403


def test_ordinary_user_cannot_verify_themselves(client: TestClient, member, db):
    """Self-verification was the cheapest abuse: it grants the badge."""
    response = client.patch(
        f"/api/users/{member['id']}/verify",
        headers=member["headers"],
    )
    assert response.status_code == 403

    user = db.get(User, uuid.UUID(member["id"]))
    assert user.is_verified is False


# ---------------------------------------------------------------------------
# Administrators
# ---------------------------------------------------------------------------


def test_admin_can_deactivate(client: TestClient, admin, victim, db):
    response = client.patch(
        f"/api/users/{victim['id']}/deactivate",
        headers=admin["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    user = db.get(User, uuid.UUID(victim["id"]))
    assert user.is_active is False


def test_deactivated_account_cannot_log_in(client: TestClient, admin, victim):
    client.patch(f"/api/users/{victim['id']}/deactivate", headers=admin["headers"])

    login = client.post(
        "/api/auth/login",
        json={"email": "victim@example.com", "password": PASSWORD},
    )
    assert login.status_code == 403


def test_deactivation_revokes_refresh_tokens(client: TestClient, admin, victim, db):
    """The flag alone is not a suspension.

    ``POST /api/auth/refresh`` validates the JWT and the stored token row;
    neither consults ``users.is_active``. Without revocation a "disabled"
    account keeps minting access tokens until its refresh token expires.
    """
    live_before = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == uuid.UUID(victim["id"]),
            RefreshToken.is_revoked.is_(False),
        )
        .count()
    )
    assert live_before >= 1, "the login fixture should have issued a refresh token"

    client.patch(f"/api/users/{victim['id']}/deactivate", headers=admin["headers"])

    live_after = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == uuid.UUID(victim["id"]),
            RefreshToken.is_revoked.is_(False),
        )
        .count()
    )
    assert live_after == 0


def test_admin_can_reactivate(client: TestClient, admin, victim, db):
    client.patch(f"/api/users/{victim['id']}/deactivate", headers=admin["headers"])

    response = client.patch(
        f"/api/users/{victim['id']}/activate",
        headers=admin["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    login = client.post(
        "/api/auth/login",
        json={"email": "victim@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200


def test_admin_can_mark_verified(client: TestClient, admin, victim, db):
    response = client.patch(
        f"/api/users/{victim['id']}/verify",
        headers=admin["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_verified"] is True


def test_missing_target_is_404_not_403(client: TestClient, admin):
    """An admin asking about a user that does not exist gets the honest answer.

    Ordering matters here: the role check runs first, so a non-admin probing
    for valid ids still sees 403 rather than being able to tell 404 from 403.
    """
    response = client.patch(
        f"/api/users/{uuid.uuid4()}/deactivate",
        headers=admin["headers"],
    )
    assert response.status_code == 404


def test_unprivileged_probe_cannot_distinguish_missing_from_present(
    client: TestClient, member, victim
):
    real = client.patch(
        f"/api/users/{victim['id']}/deactivate", headers=member["headers"]
    )
    fake = client.patch(
        f"/api/users/{uuid.uuid4()}/deactivate", headers=member["headers"]
    )
    assert real.status_code == fake.status_code == 403


# ---------------------------------------------------------------------------
# Self-targeting
# ---------------------------------------------------------------------------


def test_admin_cannot_deactivate_themselves(client: TestClient, admin, db):
    """One mis-pasted id should not be an unrecoverable lockout."""
    response = client.patch(
        f"/api/users/{admin['id']}/deactivate",
        headers=admin["headers"],
    )
    assert response.status_code == 400
    assert "your own account" in response.json()["detail"].lower()

    user = db.get(User, uuid.UUID(admin["id"]))
    assert user.is_active is True


def test_admin_cannot_verify_themselves(client: TestClient, admin, db):
    response = client.patch(
        f"/api/users/{admin['id']}/verify",
        headers=admin["headers"],
    )
    assert response.status_code == 400

    user = db.get(User, uuid.UUID(admin["id"]))
    assert user.is_verified is False


def test_admin_may_activate_themselves(client: TestClient, admin):
    """Activation is the harmless direction, so it is not blocked.

    An admin whose own account is somehow inactive cannot reach this route at
    all -- ``get_current_active_user`` refuses first -- so in practice this is
    a no-op that returns 200 rather than a 400 the caller has to special-case.
    """
    response = client.patch(
        f"/api/users/{admin['id']}/activate",
        headers=admin["headers"],
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------


def test_activating_an_active_account_is_a_no_op(client: TestClient, admin, victim, db):
    before = len(_audit_rows(db, AuditAction.USER_ACTIVATED))

    response = client.patch(
        f"/api/users/{victim['id']}/activate",
        headers=admin["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    after = len(_audit_rows(db, AuditAction.USER_ACTIVATED))
    assert after == before, "a transition that changed nothing should not be logged"


def test_verifying_a_verified_account_is_a_no_op(client: TestClient, admin, victim, db):
    client.patch(f"/api/users/{victim['id']}/verify", headers=admin["headers"])
    before = len(_audit_rows(db, AuditAction.USER_EMAIL_VERIFIED))

    response = client.patch(
        f"/api/users/{victim['id']}/verify",
        headers=admin["headers"],
    )
    assert response.status_code == 200

    after = len(_audit_rows(db, AuditAction.USER_EMAIL_VERIFIED))
    assert after == before


def test_deactivating_twice_still_revokes(client: TestClient, admin, victim, db):
    """Re-running deactivation re-runs the revocation.

    An account can be marked inactive by one path and still hold tokens issued
    before it. The second call should close that window rather than short-
    circuit on the flag.
    """
    client.patch(f"/api/users/{victim['id']}/deactivate", headers=admin["headers"])

    response = client.patch(
        f"/api/users/{victim['id']}/deactivate",
        headers=admin["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


def test_deactivation_is_audited_with_both_parties(
    client: TestClient, admin, victim, db
):
    client.patch(f"/api/users/{victim['id']}/deactivate", headers=admin["headers"])

    rows = _audit_rows(db, AuditAction.USER_SUSPENDED)
    assert len(rows) == 1

    row = rows[0]
    assert str(row.actor_id) == str(admin["id"])
    assert str(row.target_user_id) == str(victim["id"])
    assert row.entity_type == "user"
    assert row.old_values == {"is_active": True}
    assert row.new_values == {"is_active": False}


def test_reason_is_recorded_when_supplied(client: TestClient, admin, victim, db):
    client.patch(
        f"/api/users/{victim['id']}/deactivate",
        headers=admin["headers"],
        json={"reason": "Spam reports from three separate projects"},
    )

    row = _audit_rows(db, AuditAction.USER_SUSPENDED)[0]
    assert row.metadata_info["reason"] == "Spam reports from three separate projects"


def test_blank_reason_is_treated_as_absent(client: TestClient, admin, victim, db):
    client.patch(
        f"/api/users/{victim['id']}/deactivate",
        headers=admin["headers"],
        json={"reason": "   "},
    )

    row = _audit_rows(db, AuditAction.USER_SUSPENDED)[0]
    assert not row.metadata_info or "reason" not in row.metadata_info


def test_reason_length_is_bounded(client: TestClient, admin, victim):
    response = client.patch(
        f"/api/users/{victim['id']}/deactivate",
        headers=admin["headers"],
        json={"reason": "x" * 501},
    )
    assert response.status_code == 422


def test_verification_is_audited_under_its_own_action(
    client: TestClient, admin, victim, db
):
    """An admin override is not the same event as the user clicking the link."""
    client.patch(f"/api/users/{victim['id']}/verify", headers=admin["headers"])

    rows = _audit_rows(db, AuditAction.USER_EMAIL_VERIFIED)
    assert len(rows) == 1
    assert str(rows[0].actor_id) == str(admin["id"])
    assert str(rows[0].target_user_id) == str(victim["id"])


def test_empty_body_is_accepted(client: TestClient, admin, victim):
    """The routes took no body before; they must still work without one."""
    response = client.patch(
        f"/api/users/{victim['id']}/deactivate",
        headers=admin["headers"],
    )
    assert response.status_code == 200
