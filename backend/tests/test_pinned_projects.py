"""
Unit & integration tests for pinned profile projects (#1042).
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.pinned_project import MAX_PINNED_PROJECTS
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.pinned_project import PinnedProjectReorder
from app.services.pinned_project_service import PinnedProjectService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(username: str = "ada") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    user.is_private = False
    return user


def _make_project(
    owner_id: uuid.UUID | None = None,
    visibility: ProjectVisibility = ProjectVisibility.PUBLIC,
    is_archived: bool = False,
) -> MagicMock:
    project = MagicMock(spec=Project)
    project.id = uuid.uuid4()
    project.owner_id = owner_id or uuid.uuid4()
    project.title = "Deploy Radar"
    project.visibility = visibility
    project.is_archived = is_archived
    project.deleted_at = None
    return project


def _make_membership() -> MagicMock:
    member = MagicMock(spec=ProjectMember)
    member.is_active = True
    return member


# ---------------------------------------------------------------------------
# 1. Eligibility rules
# ---------------------------------------------------------------------------


class TestPinnable:
    def test_owner_may_pin_their_public_project(self):
        db = MagicMock(spec=Session)
        user = _make_user()
        PinnedProjectService.require_pinnable(db, _make_project(owner_id=user.id), user)

    def test_active_member_may_pin(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = _make_membership()
        PinnedProjectService.require_pinnable(db, _make_project(), _make_user())

    def test_stranger_may_not_pin(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None
        with pytest.raises(HTTPException) as exc:
            PinnedProjectService.require_pinnable(db, _make_project(), _make_user())
        assert exc.value.status_code == 403

    def test_private_project_may_not_be_pinned_even_by_its_owner(self):
        # A pin a visitor cannot open is a dead link, not a showcase.
        db = MagicMock(spec=Session)
        user = _make_user()
        project = _make_project(owner_id=user.id, visibility=ProjectVisibility.PRIVATE)

        with pytest.raises(HTTPException) as exc:
            PinnedProjectService.require_pinnable(db, project, user)
        assert exc.value.status_code == 400
        assert "Private" in exc.value.detail

    def test_archived_project_may_not_be_pinned(self):
        db = MagicMock(spec=Session)
        user = _make_user()
        project = _make_project(owner_id=user.id, is_archived=True)

        with pytest.raises(HTTPException) as exc:
            PinnedProjectService.require_pinnable(db, project, user)
        assert exc.value.status_code == 400
        assert "Archived" in exc.value.detail

    def test_ownership_is_checked_before_visibility(self):
        # A stranger probing private project ids should get "not yours", not a
        # message that confirms the project exists and is private.
        db = MagicMock(spec=Session)
        db.scalar.return_value = None
        project = _make_project(visibility=ProjectVisibility.PRIVATE)

        with pytest.raises(HTTPException) as exc:
            PinnedProjectService.require_pinnable(db, project, _make_user())
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# 2. Reorder payload validation
# ---------------------------------------------------------------------------


class TestReorderSchema:
    def test_empty_list_is_valid(self):
        assert PinnedProjectReorder(project_ids=[]).project_ids == []

    def test_at_the_limit_is_valid(self):
        ids = [uuid.uuid4() for _ in range(MAX_PINNED_PROJECTS)]
        assert (
            len(PinnedProjectReorder(project_ids=ids).project_ids)
            == MAX_PINNED_PROJECTS
        )

    def test_over_the_limit_is_rejected(self):
        ids = [uuid.uuid4() for _ in range(MAX_PINNED_PROJECTS + 1)]
        with pytest.raises(Exception):
            PinnedProjectReorder(project_ids=ids)


# ---------------------------------------------------------------------------
# 3. HTTP surface (real database)
# ---------------------------------------------------------------------------


class TestPinnedProjectEndpoints:
    @staticmethod
    def _project_for(
        db,
        owner_id: uuid.UUID,
        slug: str,
        visibility: ProjectVisibility = ProjectVisibility.PUBLIC,
        is_archived: bool = False,
    ) -> Project:
        project = Project(
            owner_id=owner_id,
            title=f"Project {slug}",
            slug=slug,
            description="A project worth showing off.",
            stage=ProjectStage.MVP,
            visibility=visibility,
            is_archived=is_archived,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _pin(self, client, token: str, project_id):
        return client.post(
            "/api/v1/users/me/pinned-projects",
            json={"project_id": str(project_id)},
            headers=self._auth(token),
        )

    def test_pinning_requires_authentication(self, client):
        response = client.post(
            "/api/v1/users/me/pinned-projects",
            json={"project_id": str(uuid.uuid4())},
        )
        assert response.status_code in (401, 403)

    def test_unknown_project_is_404(self, client, register_and_login):
        _, token = register_and_login("pin1@example.com", "pinuser1")
        assert self._pin(client, token, uuid.uuid4()).status_code == 404

    def test_pin_and_read_back_publicly(self, client, db, register_and_login):
        user_id, token = register_and_login("pin2@example.com", "pinuser2")
        project = self._project_for(db, uuid.UUID(user_id), "pin-p2")

        created = self._pin(client, token, project.id)
        assert created.status_code == 201, created.text
        assert created.json()["position"] == 0

        public = client.get("/api/v1/users/pinuser2/pinned-projects")
        assert public.status_code == 200
        body = public.json()
        assert body["total"] == 1
        assert body["max_pins"] == MAX_PINNED_PROJECTS
        assert body["items"][0]["project"]["slug"] == "pin-p2"

    def test_unknown_username_is_404(self, client):
        assert (
            client.get("/api/v1/users/nobody-at-all/pinned-projects").status_code == 404
        )

    def test_pinning_twice_is_409(self, client, db, register_and_login):
        user_id, token = register_and_login("pin3@example.com", "pinuser3")
        project = self._project_for(db, uuid.UUID(user_id), "pin-p3")

        assert self._pin(client, token, project.id).status_code == 201
        second = self._pin(client, token, project.id)
        assert second.status_code == 409

        # And no duplicate row was created.
        assert client.get("/api/v1/users/pinuser3/pinned-projects").json()["total"] == 1

    def test_seventh_pin_is_rejected(self, client, db, register_and_login):
        user_id, token = register_and_login("pin4@example.com", "pinuser4")

        for i in range(MAX_PINNED_PROJECTS):
            project = self._project_for(db, uuid.UUID(user_id), f"pin-p4-{i}")
            assert self._pin(client, token, project.id).status_code == 201

        one_too_many = self._project_for(db, uuid.UUID(user_id), "pin-p4-extra")
        response = self._pin(client, token, one_too_many.id)
        assert response.status_code == 400
        assert str(MAX_PINNED_PROJECTS) in response.json()["detail"]

    def test_positions_are_assigned_in_pin_order(self, client, db, register_and_login):
        user_id, token = register_and_login("pin5@example.com", "pinuser5")

        slugs = ["pin-p5-a", "pin-p5-b", "pin-p5-c"]
        for slug in slugs:
            project = self._project_for(db, uuid.UUID(user_id), slug)
            self._pin(client, token, project.id)

        items = client.get("/api/v1/users/pinuser5/pinned-projects").json()["items"]
        assert [item["position"] for item in items] == [0, 1, 2]
        assert [item["project"]["slug"] for item in items] == slugs

    def test_unpinning_the_middle_compacts_positions(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("pin6@example.com", "pinuser6")

        projects = [
            self._project_for(db, uuid.UUID(user_id), f"pin-p6-{i}") for i in range(3)
        ]
        for project in projects:
            self._pin(client, token, project.id)

        removed = client.delete(
            f"/api/v1/users/me/pinned-projects/{projects[1].id}",
            headers=self._auth(token),
        )
        assert removed.status_code == 204

        items = client.get("/api/v1/users/pinuser6/pinned-projects").json()["items"]
        assert [item["position"] for item in items] == [0, 1]
        assert [item["project"]["slug"] for item in items] == ["pin-p6-0", "pin-p6-2"]

    def test_unpinning_something_not_pinned_is_404(self, client, register_and_login):
        _, token = register_and_login("pin7@example.com", "pinuser7")
        response = client.delete(
            f"/api/v1/users/me/pinned-projects/{uuid.uuid4()}",
            headers=self._auth(token),
        )
        assert response.status_code == 404

    def test_private_project_cannot_be_pinned(self, client, db, register_and_login):
        user_id, token = register_and_login("pin8@example.com", "pinuser8")
        project = self._project_for(
            db, uuid.UUID(user_id), "pin-p8", visibility=ProjectVisibility.PRIVATE
        )

        response = self._pin(client, token, project.id)
        assert response.status_code == 400

    def test_archived_project_cannot_be_pinned(self, client, db, register_and_login):
        user_id, token = register_and_login("pin9@example.com", "pinuser9")
        project = self._project_for(db, uuid.UUID(user_id), "pin-p9", is_archived=True)

        assert self._pin(client, token, project.id).status_code == 400

    def test_cannot_pin_someone_elses_project(self, client, db, register_and_login):
        owner_id, _ = register_and_login("pin10@example.com", "pinuser10")
        project = self._project_for(db, uuid.UUID(owner_id), "pin-p10")

        _, outsider_token = register_and_login("pin11@example.com", "pinuser11")
        assert self._pin(client, outsider_token, project.id).status_code == 403

    def test_replace_sets_the_exact_order(self, client, db, register_and_login):
        user_id, token = register_and_login("pin12@example.com", "pinuser12")
        projects = [
            self._project_for(db, uuid.UUID(user_id), f"pin-p12-{i}") for i in range(3)
        ]

        for project in projects:
            self._pin(client, token, project.id)

        reordered = [projects[2].id, projects[0].id, projects[1].id]
        response = client.put(
            "/api/v1/users/me/pinned-projects",
            json={"project_ids": [str(p) for p in reordered]},
            headers=self._auth(token),
        )
        assert response.status_code == 200

        items = response.json()["items"]
        assert [item["position"] for item in items] == [0, 1, 2]
        assert [item["project_id"] for item in items] == [str(p) for p in reordered]

    def test_replace_rejects_the_whole_batch_on_one_bad_project(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("pin13@example.com", "pinuser13")
        mine = self._project_for(db, uuid.UUID(user_id), "pin-p13-mine")
        self._pin(client, token, mine.id)

        other_id, _ = register_and_login("pin14@example.com", "pinuser14")
        theirs = self._project_for(db, uuid.UUID(other_id), "pin-p13-theirs")

        response = client.put(
            "/api/v1/users/me/pinned-projects",
            json={"project_ids": [str(mine.id), str(theirs.id)]},
            headers=self._auth(token),
        )
        assert response.status_code == 403

        # Nothing was written: the original pin is untouched.
        items = client.get("/api/v1/users/pinuser13/pinned-projects").json()["items"]
        assert len(items) == 1
        assert items[0]["project_id"] == str(mine.id)

    def test_replace_rejects_duplicates(self, client, db, register_and_login):
        user_id, token = register_and_login("pin15@example.com", "pinuser15")
        project = self._project_for(db, uuid.UUID(user_id), "pin-p15")

        response = client.put(
            "/api/v1/users/me/pinned-projects",
            json={"project_ids": [str(project.id), str(project.id)]},
            headers=self._auth(token),
        )
        assert response.status_code == 400
        assert "more than once" in response.json()["detail"]

    def test_replace_with_an_empty_list_clears_pins(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("pin16@example.com", "pinuser16")
        project = self._project_for(db, uuid.UUID(user_id), "pin-p16")
        self._pin(client, token, project.id)

        response = client.put(
            "/api/v1/users/me/pinned-projects",
            json={"project_ids": []},
            headers=self._auth(token),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_replace_over_the_limit_is_rejected(self, client, db, register_and_login):
        user_id, token = register_and_login("pin17@example.com", "pinuser17")
        ids = [str(uuid.uuid4()) for _ in range(MAX_PINNED_PROJECTS + 1)]

        response = client.put(
            "/api/v1/users/me/pinned-projects",
            json={"project_ids": ids},
            headers=self._auth(token),
        )
        assert response.status_code == 422

    def test_me_endpoint_returns_your_pins(self, client, db, register_and_login):
        user_id, token = register_and_login("pin18@example.com", "pinuser18")
        project = self._project_for(db, uuid.UUID(user_id), "pin-p18")
        self._pin(client, token, project.id)

        response = client.get(
            "/api/v1/users/me/pinned-projects", headers=self._auth(token)
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_a_user_with_no_pins_returns_an_empty_list(
        self, client, register_and_login
    ):
        register_and_login("pin19@example.com", "pinuser19")
        response = client.get("/api/v1/users/pinuser19/pinned-projects")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "max_pins": MAX_PINNED_PROJECTS,
        }
