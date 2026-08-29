"""
Unit & integration tests for project release notes (#1043).
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.activity import Activity, ActivityType
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_member import MemberRole, ProjectMember
from app.models.project_release import (
    MAX_HIGHLIGHTS,
    MAX_HIGHLIGHT_LENGTH,
    ProjectRelease,
    ReleaseStatus,
    ReleaseType,
)
from app.models.user import User
from app.schemas.project_release import ReleaseCreate, ReleaseUpdate
from app.services.project_release_service import ProjectReleaseService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(username: str = "maintainer", system_role: str = "user") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    user.system_role = system_role
    user.role = "user"
    return user


def _make_project(owner_id: uuid.UUID | None = None) -> MagicMock:
    project = MagicMock(spec=Project)
    project.id = uuid.uuid4()
    project.owner_id = owner_id or uuid.uuid4()
    project.title = "Deploy Radar"
    project.deleted_at = None
    return project


def _make_member(role: MemberRole = MemberRole.MAINTAINER) -> MagicMock:
    member = MagicMock(spec=ProjectMember)
    member.role = role
    member.is_active = True
    return member


def _make_release(status: ReleaseStatus = ReleaseStatus.PUBLISHED) -> MagicMock:
    release = MagicMock(spec=ProjectRelease)
    release.id = uuid.uuid4()
    release.status = status
    return release


# ---------------------------------------------------------------------------
# 1. Schema validation
# ---------------------------------------------------------------------------


class TestReleaseSchema:
    def test_defaults_to_draft(self):
        # Writing a changelog entry and announcing it are two decisions.
        payload = ReleaseCreate(version="v1.0.0", title="First cut")
        assert payload.status == ReleaseStatus.DRAFT
        assert payload.release_type == ReleaseType.MINOR

    def test_version_and_title_are_stripped(self):
        payload = ReleaseCreate(version="  v1.0.0  ", title="  Ship it  ")
        assert payload.version == "v1.0.0"
        assert payload.title == "Ship it"

    def test_blank_version_is_rejected(self):
        with pytest.raises(Exception):
            ReleaseCreate(version="   ", title="Ship it")

    def test_blank_highlights_are_dropped(self):
        payload = ReleaseCreate(
            version="v1", title="t", highlights=["Faster search", "  ", "", "Dark mode"]
        )
        assert payload.highlights == ["Faster search", "Dark mode"]

    def test_highlights_are_stripped(self):
        payload = ReleaseCreate(
            version="v1", title="t", highlights=["  Faster search  "]
        )
        assert payload.highlights == ["Faster search"]

    def test_too_many_highlights_rejected(self):
        with pytest.raises(Exception):
            ReleaseCreate(
                version="v1",
                title="t",
                highlights=[f"item {i}" for i in range(MAX_HIGHLIGHTS + 1)],
            )

    def test_exactly_the_highlight_limit_is_allowed(self):
        payload = ReleaseCreate(
            version="v1",
            title="t",
            highlights=[f"item {i}" for i in range(MAX_HIGHLIGHTS)],
        )
        assert len(payload.highlights) == MAX_HIGHLIGHTS

    def test_overlong_highlight_rejected(self):
        with pytest.raises(Exception):
            ReleaseCreate(
                version="v1", title="t", highlights=["x" * (MAX_HIGHLIGHT_LENGTH + 1)]
            )

    def test_update_omits_unset_fields(self):
        assert ReleaseUpdate(title="New title").model_dump(exclude_unset=True) == {
            "title": "New title"
        }

    def test_update_cannot_blank_the_title(self):
        with pytest.raises(Exception):
            ReleaseUpdate(title="   ")


# ---------------------------------------------------------------------------
# 2. Maintainer checks
# ---------------------------------------------------------------------------


class TestMaintainerChecks:
    def test_owner_is_a_maintainer(self):
        db = MagicMock(spec=Session)
        user = _make_user()
        assert (
            ProjectReleaseService.is_maintainer(
                db, _make_project(owner_id=user.id), user
            )
            is True
        )

    def test_anonymous_is_not(self):
        db = MagicMock(spec=Session)
        assert ProjectReleaseService.is_maintainer(db, _make_project(), None) is False

    def test_platform_admin_is(self):
        db = MagicMock(spec=Session)
        assert (
            ProjectReleaseService.is_maintainer(
                db, _make_project(), _make_user(system_role="admin")
            )
            is True
        )

    def test_maintainer_role_qualifies(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = _make_member(MemberRole.MAINTAINER)
        assert (
            ProjectReleaseService.is_maintainer(db, _make_project(), _make_user())
            is True
        )

    def test_contributor_role_does_not(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = _make_member(MemberRole.CONTRIBUTOR)
        assert (
            ProjectReleaseService.is_maintainer(db, _make_project(), _make_user())
            is False
        )

    def test_require_maintainer_raises_403(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None
        with pytest.raises(HTTPException) as exc:
            ProjectReleaseService.require_maintainer(db, _make_project(), _make_user())
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# 3. Draft visibility
# ---------------------------------------------------------------------------


class TestDraftVisibility:
    def _db_returning(self, release):
        db = MagicMock(spec=Session)
        db.scalar.return_value = release
        return db

    def test_missing_release_is_404(self):
        with pytest.raises(HTTPException) as exc:
            ProjectReleaseService.get_release_or_404(
                self._db_returning(None), uuid.uuid4(), uuid.uuid4()
            )
        assert exc.value.status_code == 404

    def test_draft_is_404_for_the_public_not_403(self):
        # A 403 would confirm the draft exists, and hand over its id.
        draft = _make_release(ReleaseStatus.DRAFT)
        with pytest.raises(HTTPException) as exc:
            ProjectReleaseService.get_release_or_404(
                self._db_returning(draft),
                uuid.uuid4(),
                draft.id,
                viewer_is_maintainer=False,
            )
        assert exc.value.status_code == 404

    def test_draft_is_visible_to_a_maintainer(self):
        draft = _make_release(ReleaseStatus.DRAFT)
        found = ProjectReleaseService.get_release_or_404(
            self._db_returning(draft), uuid.uuid4(), draft.id, viewer_is_maintainer=True
        )
        assert found is draft

    def test_published_is_visible_to_the_public(self):
        published = _make_release(ReleaseStatus.PUBLISHED)
        found = ProjectReleaseService.get_release_or_404(
            self._db_returning(published), uuid.uuid4(), published.id
        )
        assert found is published


# ---------------------------------------------------------------------------
# 4. HTTP surface (real database)
# ---------------------------------------------------------------------------


class TestReleaseEndpoints:
    @staticmethod
    def _project_for(db, owner_id: uuid.UUID, slug: str) -> Project:
        project = Project(
            owner_id=owner_id,
            title="Deploy Radar",
            slug=slug,
            description="Ships things and tells you about it.",
            stage=ProjectStage.MVP,
            visibility=ProjectVisibility.PUBLIC,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _create(self, client, token, project_id, **overrides):
        payload = {"version": "v1.0.0", "title": "First release"}
        payload.update(overrides)
        return client.post(
            f"/api/v1/projects/{project_id}/releases",
            json=payload,
            headers=self._auth(token),
        )

    def test_creating_requires_authentication(self, client):
        response = client.post(
            f"/api/v1/projects/{uuid.uuid4()}/releases",
            json={"version": "v1", "title": "t"},
        )
        assert response.status_code in (401, 403)

    def test_unknown_project_is_404(self, client, register_and_login):
        _, token = register_and_login("rel1@example.com", "reluser1")
        assert self._create(client, token, uuid.uuid4()).status_code == 404

    def test_create_defaults_to_draft(self, client, db, register_and_login):
        user_id, token = register_and_login("rel2@example.com", "reluser2")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p2")

        response = self._create(client, token, project.id)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "draft"
        assert body["published_at"] is None
        assert body["is_pinned"] is False

    def test_drafts_are_hidden_from_the_public_listing(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("rel3@example.com", "reluser3")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p3")
        self._create(client, token, project.id)

        public = client.get(f"/api/v1/projects/{project.id}/releases")
        assert public.status_code == 200
        assert public.json()["total"] == 0

        maintainer = client.get(
            f"/api/v1/projects/{project.id}/releases",
            params={"include_drafts": True},
            headers=self._auth(token),
        )
        assert maintainer.json()["total"] == 1

    def test_include_drafts_is_ignored_for_the_public(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("rel4@example.com", "reluser4")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p4")
        self._create(client, token, project.id)

        response = client.get(
            f"/api/v1/projects/{project.id}/releases", params={"include_drafts": True}
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_anonymous_get_of_a_draft_is_404(self, client, db, register_and_login):
        user_id, token = register_and_login("rel5@example.com", "reluser5")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p5")
        release_id = self._create(client, token, project.id).json()["id"]

        assert (
            client.get(
                f"/api/v1/projects/{project.id}/releases/{release_id}"
            ).status_code
            == 404
        )
        # But its own maintainer can read it.
        assert (
            client.get(
                f"/api/v1/projects/{project.id}/releases/{release_id}",
                headers=self._auth(token),
            ).status_code
            == 200
        )

    def test_duplicate_version_is_409_case_insensitively(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("rel6@example.com", "reluser6")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p6")

        assert (
            self._create(client, token, project.id, version="v1.0.0").status_code == 201
        )

        clash = self._create(client, token, project.id, version="V1.0.0")
        assert clash.status_code == 409
        assert "already exists" in clash.json()["detail"]

    def test_same_version_in_two_projects_is_fine(self, client, db, register_and_login):
        user_id, token = register_and_login("rel7@example.com", "reluser7")
        first = self._project_for(db, uuid.UUID(user_id), "rel-p7-a")
        second = self._project_for(db, uuid.UUID(user_id), "rel-p7-b")

        assert (
            self._create(client, token, first.id, version="v1.0.0").status_code == 201
        )
        assert (
            self._create(client, token, second.id, version="v1.0.0").status_code == 201
        )

    def test_publishing_sets_the_date_and_is_idempotent(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("rel8@example.com", "reluser8")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p8")
        release_id = self._create(client, token, project.id).json()["id"]

        first = client.post(
            f"/api/v1/projects/{project.id}/releases/{release_id}/publish",
            headers=self._auth(token),
        )
        assert first.status_code == 200
        assert first.json()["status"] == "published"
        published_at = first.json()["published_at"]
        assert published_at is not None

        second = client.post(
            f"/api/v1/projects/{project.id}/releases/{release_id}/publish",
            headers=self._auth(token),
        )
        assert second.status_code == 200
        # A double-clicked button must not rewrite the release date.
        assert second.json()["published_at"] == published_at

    def test_activity_is_written_on_publish_not_on_create(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("rel9@example.com", "reluser9")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p9")

        def announcement_count() -> int:
            return (
                db.query(Activity)
                .filter(Activity.activity_type == ActivityType.PROJECT_ANNOUNCEMENT)
                .count()
            )

        before = announcement_count()
        release_id = self._create(client, token, project.id).json()["id"]
        assert announcement_count() == before, "a draft is not news yet"

        client.post(
            f"/api/v1/projects/{project.id}/releases/{release_id}/publish",
            headers=self._auth(token),
        )
        assert announcement_count() == before + 1

    def test_creating_as_published_announces_immediately(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("rel10@example.com", "reluser10")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p10")

        response = self._create(client, token, project.id, status="published")
        assert response.status_code == 201
        assert response.json()["status"] == "published"
        assert response.json()["published_at"] is not None

    def test_pinning_moves_the_pin(self, client, db, register_and_login):
        user_id, token = register_and_login("rel11@example.com", "reluser11")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p11")

        first = self._create(
            client, token, project.id, version="v1.0.0", status="published"
        ).json()
        second = self._create(
            client, token, project.id, version="v2.0.0", status="published"
        ).json()

        client.post(
            f"/api/v1/projects/{project.id}/releases/{first['id']}/pin",
            headers=self._auth(token),
        )
        client.post(
            f"/api/v1/projects/{project.id}/releases/{second['id']}/pin",
            headers=self._auth(token),
        )

        items = client.get(f"/api/v1/projects/{project.id}/releases").json()["items"]
        pinned = [item for item in items if item["is_pinned"]]
        assert len(pinned) == 1
        assert pinned[0]["id"] == second["id"]
        # And the pinned one sorts to the top.
        assert items[0]["id"] == second["id"]

    def test_a_draft_cannot_be_pinned(self, client, db, register_and_login):
        user_id, token = register_and_login("rel12@example.com", "reluser12")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p12")
        release_id = self._create(client, token, project.id).json()["id"]

        response = client.post(
            f"/api/v1/projects/{project.id}/releases/{release_id}/pin",
            headers=self._auth(token),
        )
        assert response.status_code == 400

    def test_latest_returns_the_newest_published(self, client, db, register_and_login):
        user_id, token = register_and_login("rel13@example.com", "reluser13")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p13")

        assert (
            client.get(f"/api/v1/projects/{project.id}/releases/latest").status_code
            == 404
        )

        self._create(client, token, project.id, version="v1.0.0", status="published")
        newest = self._create(
            client, token, project.id, version="v1.1.0", status="published"
        ).json()

        response = client.get(f"/api/v1/projects/{project.id}/releases/latest")
        assert response.status_code == 200
        assert response.json()["id"] == newest["id"]

    def test_latest_ignores_drafts(self, client, db, register_and_login):
        user_id, token = register_and_login("rel14@example.com", "reluser14")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p14")

        published = self._create(
            client, token, project.id, version="v1.0.0", status="published"
        ).json()
        self._create(client, token, project.id, version="v2.0.0-rc1")

        response = client.get(f"/api/v1/projects/{project.id}/releases/latest")
        assert response.json()["id"] == published["id"]

    def test_non_maintainer_cannot_create(self, client, db, register_and_login):
        owner_id, _ = register_and_login("rel15@example.com", "reluser15")
        project = self._project_for(db, uuid.UUID(owner_id), "rel-p15")

        _, outsider_token = register_and_login("rel16@example.com", "reluser16")
        assert self._create(client, outsider_token, project.id).status_code == 403

    def test_edit_and_delete(self, client, db, register_and_login):
        user_id, token = register_and_login("rel17@example.com", "reluser17")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p17")
        release_id = self._create(client, token, project.id).json()["id"]

        updated = client.patch(
            f"/api/v1/projects/{project.id}/releases/{release_id}",
            json={"title": "Renamed", "highlights": ["Faster boot"]},
            headers=self._auth(token),
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "Renamed"
        assert updated.json()["highlights"] == ["Faster boot"]

        deleted = client.delete(
            f"/api/v1/projects/{project.id}/releases/{release_id}",
            headers=self._auth(token),
        )
        assert deleted.status_code == 204

    def test_editing_to_a_taken_version_is_409(self, client, db, register_and_login):
        user_id, token = register_and_login("rel18@example.com", "reluser18")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p18")

        self._create(client, token, project.id, version="v1.0.0")
        second_id = self._create(client, token, project.id, version="v2.0.0").json()[
            "id"
        ]

        response = client.patch(
            f"/api/v1/projects/{project.id}/releases/{second_id}",
            json={"version": "v1.0.0"},
            headers=self._auth(token),
        )
        assert response.status_code == 409

    def test_editing_a_release_to_its_own_version_is_allowed(
        self, client, db, register_and_login
    ):
        # The uniqueness check must exclude the row being edited, or saving a
        # form without touching the version field would fail.
        user_id, token = register_and_login("rel19@example.com", "reluser19")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p19")
        release_id = self._create(client, token, project.id, version="v1.0.0").json()[
            "id"
        ]

        response = client.patch(
            f"/api/v1/projects/{project.id}/releases/{release_id}",
            json={"version": "v1.0.0", "title": "Same version, new title"},
            headers=self._auth(token),
        )
        assert response.status_code == 200

    def test_published_listing_is_newest_first(self, client, db, register_and_login):
        user_id, token = register_and_login("rel20@example.com", "reluser20")
        project = self._project_for(db, uuid.UUID(user_id), "rel-p20")

        for version in ("v1.0.0", "v1.1.0", "v1.2.0"):
            self._create(client, token, project.id, version=version, status="published")

        items = client.get(f"/api/v1/projects/{project.id}/releases").json()["items"]
        assert [item["version"] for item in items] == ["v1.2.0", "v1.1.0", "v1.0.0"]
