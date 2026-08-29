"""
Authorization and validation for reputation adjustments.

`POST /api/reputation/award` authenticated the caller and then did nothing with
that identity except use it as the default target. It took the recipient, the
action and the number of points as given:

    target_user_id = payload.user_id or current_user.id

`points` was an unbounded optional integer and `action` a free `str`, so one
request from a day-old account put it at the top of the leaderboard -- or, with
a minus sign, zeroed out everybody above it, since the service floors the score
at 0.

Also covered: the leaderboard, which counted and ranked deactivated and
soft-deleted accounts.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.reputation import ReputationLog
from app.models.user import User
from app.schemas.reputation import MAX_POINTS_PER_AWARD
from app.services.reputation_service import ACTION_POINTS, ReputationService


def _account(register_and_login, email: str, username: str) -> dict:
    uid, token = register_and_login(email, username)
    return {
        "id": uid,
        "uuid": uuid.UUID(uid),
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def admin(register_and_login, db):
    acct = _account(register_and_login, "repadmin@example.com", "repadmin")
    user = db.get(User, acct["uuid"])
    user.system_role = "admin"
    db.add(user)
    db.commit()
    return acct


@pytest.fixture
def member(register_and_login):
    return _account(register_and_login, "repmember@example.com", "repmember")


@pytest.fixture
def rival(register_and_login):
    return _account(register_and_login, "reprival@example.com", "reprival")


def _score(db, user_uuid) -> int:
    db.expire_all()
    return db.get(User, user_uuid).reputation_score or 0


# ---------------------------------------------------------------------------
# Who may call it
# ---------------------------------------------------------------------------


class TestAwardRequiresAdmin:
    def test_anonymous_caller_is_rejected(self, client: TestClient, member):
        response = client.post(
            "/api/reputation/award",
            json={"user_id": member["id"], "action": "merged_pull_request"},
        )
        assert response.status_code == 401

    def test_ordinary_user_cannot_award_themselves(
        self, client: TestClient, member, db
    ):
        """The reported bug, in its cheapest form."""
        response = client.post(
            "/api/reputation/award",
            headers=member["headers"],
            json={
                "user_id": member["id"],
                "action": "manual_adjustment",
                "points": 999,
            },
        )
        assert response.status_code == 403
        assert _score(db, member["uuid"]) == 0

    def test_ordinary_user_cannot_award_someone_else(
        self, client: TestClient, member, rival, db
    ):
        response = client.post(
            "/api/reputation/award",
            headers=member["headers"],
            json={"user_id": rival["id"], "action": "merged_pull_request"},
        )
        assert response.status_code == 403
        assert _score(db, rival["uuid"]) == 0

    def test_ordinary_user_cannot_deduct_from_a_rival(
        self, client: TestClient, admin, member, rival, db
    ):
        """Deduction was the cheaper attack.

        The service floors the score at 0, so zeroing out everyone above you
        was one request each rather than an arms race of inflation.
        """
        client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": rival["id"], "action": "completed_project"},
        )
        assert _score(db, rival["uuid"]) == 100

        response = client.post(
            "/api/reputation/award",
            headers=member["headers"],
            json={
                "user_id": rival["id"],
                "action": "manual_adjustment",
                "points": -500,
            },
        )
        assert response.status_code == 403
        assert _score(db, rival["uuid"]) == 100

    def test_admin_can_award(self, client: TestClient, admin, member, db):
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": member["id"], "action": "merged_pull_request"},
        )
        assert response.status_code == 201
        assert response.json()["points"] == ACTION_POINTS["merged_pull_request"]
        assert _score(db, member["uuid"]) == 50


# ---------------------------------------------------------------------------
# The target is required
# ---------------------------------------------------------------------------


class TestTargetIsRequired:
    def test_omitting_user_id_is_a_422(self, client: TestClient, admin):
        """It used to mean "me", which is the shape of a self-service score."""
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"action": "merged_pull_request"},
        )
        assert response.status_code == 422

    def test_unknown_user_is_a_404(self, client: TestClient, admin):
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": str(uuid.uuid4()), "action": "merged_pull_request"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Action and points validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_unknown_action_is_rejected(self, client: TestClient, admin, member, db):
        """`ACTION_POINTS.get(action.lower(), 10)` used to award ten for a typo."""
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": member["id"], "action": "definitely_not_an_action"},
        )
        assert response.status_code == 422
        assert _score(db, member["uuid"]) == 0

    def test_points_above_the_ceiling_are_rejected(
        self, client: TestClient, admin, member, db
    ):
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={
                "user_id": member["id"],
                "action": "manual_adjustment",
                "points": MAX_POINTS_PER_AWARD + 1,
            },
        )
        assert response.status_code == 422
        assert _score(db, member["uuid"]) == 0

    def test_points_below_the_floor_are_rejected(
        self, client: TestClient, admin, member
    ):
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={
                "user_id": member["id"],
                "action": "manual_adjustment",
                "points": -(MAX_POINTS_PER_AWARD + 1),
            },
        )
        assert response.status_code == 422

    def test_an_override_at_the_ceiling_is_accepted(
        self, client: TestClient, admin, member, db
    ):
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={
                "user_id": member["id"],
                "action": "manual_adjustment",
                "points": MAX_POINTS_PER_AWARD,
            },
        )
        assert response.status_code == 201
        assert _score(db, member["uuid"]) == MAX_POINTS_PER_AWARD

    def test_an_admin_deduction_still_floors_at_zero(
        self, client: TestClient, admin, member, db
    ):
        client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": member["id"], "action": "helpful_discussion"},
        )
        assert _score(db, member["uuid"]) == 15

        client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={
                "user_id": member["id"],
                "action": "manual_adjustment",
                "points": -100,
            },
        )
        assert _score(db, member["uuid"]) == 0


class TestResolvePoints:
    def test_every_action_has_a_point_value(self):
        """Guards the fallback that used to make a typo worth ten points."""
        from app.schemas.reputation import ReputationAction

        for action in ReputationAction:
            assert action.value in ACTION_POINTS

    def test_resolve_points_rejects_an_unknown_action(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            ReputationService.resolve_points("not_a_real_action", None)
        assert exc.value.status_code == 422

    def test_resolve_points_bounds_an_override(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            ReputationService.resolve_points(
                "manual_adjustment", MAX_POINTS_PER_AWARD * 10
            )
        assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------


class TestAttribution:
    def test_the_log_records_who_granted_the_points(
        self, client: TestClient, admin, member, db
    ):
        """`ReputationLog` recorded who received points and never who granted."""
        response = client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": member["id"], "action": "mentor_recognition"},
        )
        assert response.status_code == 201
        assert response.json()["granted_by_id"] == admin["id"]

        log = db.query(ReputationLog).one()
        assert str(log.user_id) == member["id"]
        assert str(log.granted_by_id) == admin["id"]

    def test_a_service_level_award_may_have_no_actor(self, db, member):
        """The platform awarding points to itself has no human behind it."""
        _, log = ReputationService.award_reputation(
            db=db,
            user_id=member["uuid"],
            action="profile_completion",
        )
        assert log.granted_by_id is None


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------


class TestLeaderboard:
    def test_deactivated_accounts_are_not_ranked(
        self, client: TestClient, admin, member, rival, db
    ):
        """The leaderboard published the username and avatar of disabled accounts."""
        before = client.get("/api/reputation/leaderboard").json()
        assert any(e["username"] == "reprival" for e in before["entries"])

        user = db.get(User, rival["uuid"])
        user.is_active = False
        db.add(user)
        db.commit()

        after = client.get("/api/reputation/leaderboard").json()
        assert not any(e["username"] == "reprival" for e in after["entries"])

    def test_soft_deleted_accounts_are_not_ranked(
        self, client: TestClient, member, rival, db
    ):
        from datetime import datetime, timezone

        user = db.get(User, rival["uuid"])
        user.deleted_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()

        entries = client.get("/api/reputation/leaderboard").json()["entries"]
        assert not any(e["username"] == "reprival" for e in entries)

    def test_total_counts_the_same_set_it_ranks(
        self, client: TestClient, member, rival, db
    ):
        """`total` was `count(User.id)` with no predicate at all, so it counted
        rows the listing would never return, and the client's page count was
        wrong."""
        body = client.get("/api/reputation/leaderboard", params={"limit": 100}).json()
        assert body["total"] == len(body["entries"])

        user = db.get(User, rival["uuid"])
        user.is_active = False
        db.add(user)
        db.commit()

        body = client.get("/api/reputation/leaderboard", params={"limit": 100}).json()
        assert body["total"] == len(body["entries"])

    def test_ranking_is_by_score_descending(
        self, client: TestClient, admin, member, rival, db
    ):
        client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": rival["id"], "action": "completed_project"},
        )
        client.post(
            "/api/reputation/award",
            headers=admin["headers"],
            json={"user_id": member["id"], "action": "helpful_discussion"},
        )

        entries = client.get(
            "/api/reputation/leaderboard", params={"limit": 100}
        ).json()["entries"]
        scores = [e["reputation_score"] for e in entries]
        assert scores == sorted(scores, reverse=True)
        assert entries[0]["username"] == "reprival"
