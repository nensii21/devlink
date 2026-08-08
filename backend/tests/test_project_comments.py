"""Tests for project discussions (#930).

These run against the real session rather than mocks, because most of what is
worth testing here is relational: who may see a private project's thread, what
happens to replies when their parent is deleted, and whether a comment id from
one project can be used to reach into another.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_comment import ProjectComment
from app.models.project_member import MemberRole, ProjectMember
from app.models.user import User
from app.schemas.project_comment import (
    ProjectCommentCreate,
    ProjectCommentUpdate,
)
from app.services.project_comment_service import ProjectCommentService as Svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_user(db, username: str, *, system_role: str = "user") -> User:
    user = User(
        email=f"{username}@example.com",
        username=username,
        first_name=username.capitalize(),
        last_name="Tester",
        password_hash="fake",
        system_role=system_role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def make_project(
    db,
    owner: User,
    *,
    slug: str = "demo-project",
    visibility: ProjectVisibility = ProjectVisibility.PUBLIC,
) -> Project:
    project = Project(
        owner_id=owner.id,
        title="Demo Project",
        slug=slug,
        description="A project for testing discussions.",
        stage=ProjectStage.MVP,
        visibility=visibility,
    )
    db.add(project)
    db.flush()
    return project


@pytest.fixture
def owner(db):
    return make_user(db, "owner")


@pytest.fixture
def outsider(db):
    return make_user(db, "outsider")


@pytest.fixture
def project(db, owner):
    return make_project(db, owner)


def post(db, project, author, body="A comment.", parent_id=None) -> ProjectComment:
    return Svc.create_comment(
        db,
        project,
        ProjectCommentCreate(body=body, parent_id=parent_id),
        author,
    )


# ---------------------------------------------------------------------------
# Creating
# ---------------------------------------------------------------------------


class TestCreate:
    def test_creates_a_top_level_comment(self, db, project, outsider):
        comment = post(db, project, outsider, "Does this support Postgres 16?")

        assert comment.parent_id is None
        assert comment.author_id == outsider.id
        assert comment.project_id == project.id
        assert comment.is_edited is False
        assert comment.deleted_at is None

    def test_creates_a_reply(self, db, project, owner, outsider):
        parent = post(db, project, outsider, "Question?")
        reply = post(db, project, owner, "Answer.", parent_id=parent.id)

        assert reply.parent_id == parent.id

    def test_reply_to_a_reply_attaches_to_the_top_level_parent(
        self, db, project, owner, outsider
    ):
        """One level deep. Replying to a reply must not nest further."""
        parent = post(db, project, outsider, "Question?")
        reply = post(db, project, owner, "Answer.", parent_id=parent.id)

        nested = post(db, project, outsider, "Follow-up.", parent_id=reply.id)

        assert nested.parent_id == parent.id

    def test_cannot_reply_to_a_comment_on_another_project(self, db, owner, outsider):
        first = make_project(db, owner, slug="first")
        second = make_project(db, owner, slug="second")
        elsewhere = post(db, first, owner, "Over here.")

        with pytest.raises(HTTPException) as exc:
            post(db, second, outsider, "Reply.", parent_id=elsewhere.id)

        assert exc.value.status_code == 404

    def test_cannot_reply_to_a_deleted_comment(self, db, project, owner, outsider):
        parent = post(db, project, outsider, "Question?")
        Svc.delete_comment(db, parent, outsider)

        with pytest.raises(HTTPException) as exc:
            post(db, project, owner, "Reply.", parent_id=parent.id)

        assert exc.value.status_code == 404


class TestBodyValidation:
    @pytest.mark.parametrize("body", ["", "   ", "\n\t  \n"])
    def test_blank_bodies_are_rejected(self, body):
        with pytest.raises(ValueError):
            ProjectCommentCreate(body=body)

    def test_surrounding_whitespace_is_trimmed(self):
        payload = ProjectCommentCreate(body="  hello  ")

        assert payload.body == "hello"

    def test_body_over_the_limit_is_rejected(self):
        with pytest.raises(ValueError):
            ProjectCommentCreate(body="x" * 5001)

    def test_body_at_the_limit_is_accepted(self):
        assert len(ProjectCommentCreate(body="x" * 5000).body) == 5000


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------


class TestVisibility:
    def test_public_project_is_readable_by_anyone(self, db, project):
        assert Svc.can_view_project(db, project, None) is True

    def test_private_project_is_hidden_from_anonymous_visitors(self, db, owner):
        private = make_project(
            db, owner, slug="secret", visibility=ProjectVisibility.PRIVATE
        )

        assert Svc.can_view_project(db, private, None) is False

    def test_private_project_is_hidden_from_a_non_member(self, db, owner, outsider):
        private = make_project(
            db, owner, slug="secret", visibility=ProjectVisibility.PRIVATE
        )

        assert Svc.can_view_project(db, private, outsider) is False

    def test_private_project_is_visible_to_its_owner(self, db, owner):
        private = make_project(
            db, owner, slug="secret", visibility=ProjectVisibility.PRIVATE
        )

        assert Svc.can_view_project(db, private, owner) is True

    def test_private_project_is_visible_to_an_active_member(self, db, owner, outsider):
        private = make_project(
            db, owner, slug="secret", visibility=ProjectVisibility.PRIVATE
        )
        db.add(
            ProjectMember(
                project_id=private.id,
                user_id=outsider.id,
                role=MemberRole.CONTRIBUTOR,
                is_active=True,
            )
        )
        db.flush()

        assert Svc.can_view_project(db, private, outsider) is True

    def test_inactive_member_loses_access(self, db, owner, outsider):
        private = make_project(
            db, owner, slug="secret", visibility=ProjectVisibility.PRIVATE
        )
        db.add(
            ProjectMember(
                project_id=private.id,
                user_id=outsider.id,
                role=MemberRole.CONTRIBUTOR,
                is_active=False,
            )
        )
        db.flush()

        assert Svc.can_view_project(db, private, outsider) is False

    def test_admin_can_view_a_private_project(self, db, owner):
        admin = make_user(db, "sysadmin", system_role="admin")
        private = make_project(
            db, owner, slug="secret", visibility=ProjectVisibility.PRIVATE
        )

        assert Svc.can_view_project(db, private, admin) is True

    def test_denied_access_reports_404_not_403(self, db, owner, outsider):
        """Confirming a private project exists is itself a disclosure."""
        private = make_project(
            db, owner, slug="secret", visibility=ProjectVisibility.PRIVATE
        )

        with pytest.raises(HTTPException) as exc:
            Svc.require_can_view(db, private, outsider)

        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Editing
# ---------------------------------------------------------------------------


class TestEdit:
    def test_author_can_edit_and_the_marker_is_set(self, db, project, outsider):
        comment = post(db, project, outsider, "Original.")

        updated = Svc.update_comment(db, comment, ProjectCommentUpdate(body="Revised."))

        assert updated.body == "Revised."
        assert updated.is_edited is True
        assert updated.edited_at is not None

    def test_editing_to_identical_text_does_not_mark_it_edited(
        self, db, project, outsider
    ):
        comment = post(db, project, outsider, "Same.")

        updated = Svc.update_comment(db, comment, ProjectCommentUpdate(body="Same."))

        assert updated.is_edited is False
        assert updated.edited_at is None

    def test_another_user_cannot_edit(self, db, project, owner, outsider):
        comment = post(db, project, outsider, "Mine.")

        with pytest.raises(HTTPException) as exc:
            Svc.require_can_edit(comment, owner)

        assert exc.value.status_code == 403

    def test_project_owner_cannot_edit_someone_elses_comment(
        self, db, project, owner, outsider
    ):
        """Removing someone's words is moderation; rewriting them is not."""
        comment = post(db, project, outsider, "Mine.")

        with pytest.raises(HTTPException) as exc:
            Svc.require_can_edit(comment, owner)

        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Deleting
# ---------------------------------------------------------------------------


class TestDelete:
    def test_author_can_delete_their_own(self, db, project, outsider):
        comment = post(db, project, outsider)

        Svc.require_can_delete(db, project, comment, outsider)
        Svc.delete_comment(db, comment, outsider)

        assert comment.deleted_at is not None
        assert comment.deleted_by_id == outsider.id

    def test_project_owner_can_delete_any_comment(self, db, project, owner, outsider):
        comment = post(db, project, outsider)

        Svc.require_can_delete(db, project, comment, owner)  # does not raise

    def test_admin_can_delete_any_comment(self, db, project, outsider):
        admin = make_user(db, "sysadmin", system_role="admin")
        comment = post(db, project, outsider)

        Svc.require_can_delete(db, project, comment, admin)  # does not raise

    def test_unrelated_user_cannot_delete(self, db, project, outsider):
        stranger = make_user(db, "stranger")
        comment = post(db, project, outsider)

        with pytest.raises(HTTPException) as exc:
            Svc.require_can_delete(db, project, comment, stranger)

        assert exc.value.status_code == 403

    def test_delete_is_soft_so_the_row_survives(self, db, project, outsider):
        comment = post(db, project, outsider)
        comment_id = comment.id

        Svc.delete_comment(db, comment, outsider)

        assert db.get(ProjectComment, comment_id) is not None

    def test_deleting_twice_keeps_the_first_timestamp(self, db, project, outsider):
        comment = post(db, project, outsider)

        Svc.delete_comment(db, comment, outsider)
        first = comment.deleted_at

        Svc.delete_comment(db, comment, outsider)

        assert comment.deleted_at == first

    def test_replies_survive_their_parent_being_deleted(
        self, db, project, owner, outsider
    ):
        parent = post(db, project, outsider, "Question?")
        reply = post(db, project, owner, "Answer.", parent_id=parent.id)

        Svc.delete_comment(db, parent, outsider)
        db.flush()

        surviving = db.get(ProjectComment, reply.id)

        assert surviving is not None
        assert surviving.deleted_at is None
        assert surviving.parent_id == parent.id


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


class TestListing:
    def test_returns_only_top_level_comments(self, db, project, owner, outsider):
        first = post(db, project, outsider, "One.")
        post(db, project, owner, "Reply.", parent_id=first.id)
        post(db, project, outsider, "Two.")
        db.flush()

        comments, total = Svc.list_thread(db, project.id)

        assert total == 2
        assert all(c.parent_id is None for c in comments)

    def test_newest_first(self, db, project, outsider):
        post(db, project, outsider, "Older.")
        db.flush()
        post(db, project, outsider, "Newer.")
        db.flush()

        comments, _ = Svc.list_thread(db, project.id)
        bodies = [c.body for c in comments]

        assert bodies.index("Newer.") < bodies.index("Older.")

    def test_a_deleted_top_level_comment_stays_in_the_listing(
        self, db, project, outsider
    ):
        """Tombstoned, so its replies keep their context."""
        comment = post(db, project, outsider, "Removed.")
        Svc.delete_comment(db, comment, outsider)
        db.flush()

        _, total = Svc.list_thread(db, project.id)

        assert total == 1

    def test_deleted_replies_are_dropped(self, db, project, owner, outsider):
        parent = post(db, project, outsider, "Question?")
        kept = post(db, project, owner, "Kept.", parent_id=parent.id)
        removed = post(db, project, owner, "Removed.", parent_id=parent.id)
        Svc.delete_comment(db, removed, owner)
        db.flush()
        db.refresh(parent)

        visible = Svc.visible_replies(parent)

        assert [r.id for r in visible] == [kept.id]

    def test_replies_are_oldest_first(self, db, project, owner, outsider):
        parent = post(db, project, outsider, "Question?")
        first = post(db, project, owner, "First.", parent_id=parent.id)
        db.flush()
        second = post(db, project, owner, "Second.", parent_id=parent.id)
        db.flush()
        db.refresh(parent)

        visible = Svc.visible_replies(parent)

        assert [r.id for r in visible] == [first.id, second.id]

    def test_comments_from_other_projects_are_excluded(self, db, owner, outsider):
        mine = make_project(db, owner, slug="mine")
        theirs = make_project(db, owner, slug="theirs")
        post(db, mine, outsider, "Here.")
        post(db, theirs, outsider, "Elsewhere.")
        db.flush()

        comments, total = Svc.list_thread(db, mine.id)

        assert total == 1
        assert comments[0].body == "Here."

    def test_pagination(self, db, project, outsider):
        for index in range(5):
            post(db, project, outsider, f"Comment {index}.")
        db.flush()

        page_one, total = Svc.list_thread(db, project.id, limit=2, offset=0)
        page_two, _ = Svc.list_thread(db, project.id, limit=2, offset=2)

        assert total == 5
        assert len(page_one) == 2
        assert len(page_two) == 2
        assert {c.id for c in page_one}.isdisjoint({c.id for c in page_two})

    def test_limit_is_capped(self, db, project, outsider):
        post(db, project, outsider)
        db.flush()

        # Should clamp rather than raise or attempt an unbounded read.
        comments, _ = Svc.list_thread(db, project.id, limit=10_000)

        assert len(comments) <= 100


class TestCount:
    def test_counts_replies_too(self, db, project, owner, outsider):
        parent = post(db, project, outsider, "Question?")
        post(db, project, owner, "Answer.", parent_id=parent.id)
        db.flush()

        assert Svc.count_comments(db, project.id) == 2

    def test_excludes_deleted(self, db, project, outsider):
        first = post(db, project, outsider, "One.")
        post(db, project, outsider, "Two.")
        Svc.delete_comment(db, first, outsider)
        db.flush()

        assert Svc.count_comments(db, project.id) == 1

    def test_zero_for_a_project_with_no_discussion(self, db, project):
        assert Svc.count_comments(db, project.id) == 0


class TestLookup:
    def test_missing_comment_is_404(self, db, project):
        with pytest.raises(HTTPException) as exc:
            Svc.get_comment_or_404(db, project.id, uuid.uuid4())

        assert exc.value.status_code == 404

    def test_missing_project_is_404(self, db):
        with pytest.raises(HTTPException) as exc:
            Svc.get_project_or_404(db, uuid.uuid4())

        assert exc.value.status_code == 404

    def test_soft_deleted_project_is_404(self, db, owner):
        from datetime import datetime, timezone

        gone = make_project(db, owner, slug="gone")
        gone.deleted_at = datetime.now(timezone.utc)
        db.flush()

        with pytest.raises(HTTPException) as exc:
            Svc.get_project_or_404(db, gone.id)

        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------


class TestEndpoints:
    """Router wiring: auth requirements, status codes, response shape."""

    @staticmethod
    def _project_for(db, owner_id: uuid.UUID) -> Project:
        project = Project(
            owner_id=owner_id,
            title="API Project",
            slug="api-project",
            description="For endpoint tests.",
            stage=ProjectStage.MVP,
            visibility=ProjectVisibility.PUBLIC,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def test_anonymous_can_read_a_public_thread(self, client, db, register_and_login):
        user_id, _ = register_and_login("reader@example.com", "reader")
        project = self._project_for(db, uuid.UUID(user_id))

        response = client.get(f"/api/v1/projects/{project.id}/comments")

        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_anonymous_cannot_post(self, client, db, register_and_login):
        user_id, _ = register_and_login("poster@example.com", "poster")
        project = self._project_for(db, uuid.UUID(user_id))

        response = client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "Sneaking in."},
        )

        assert response.status_code in (401, 403)

    def test_post_returns_201_and_the_comment(self, client, db, register_and_login):
        user_id, token = register_and_login("author@example.com", "author")
        project = self._project_for(db, uuid.UUID(user_id))

        response = client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "First!"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["body"] == "First!"
        assert body["parent_id"] is None
        assert body["is_deleted"] is False
        assert body["author"]["username"] == "author"

    def test_unknown_project_is_404(self, client, register_and_login):
        _, token = register_and_login("nobody@example.com", "nobody")

        response = client.post(
            f"/api/v1/projects/{uuid.uuid4()}/comments",
            json={"body": "Hello?"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_blank_body_is_422(self, client, db, register_and_login):
        user_id, token = register_and_login("blank@example.com", "blank")
        project = self._project_for(db, uuid.UUID(user_id))

        response = client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "   "},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    def test_editing_someone_elses_comment_is_403(self, client, db, register_and_login):
        owner_id, owner_token = register_and_login("owner2@example.com", "owner2")
        _, other_token = register_and_login("other2@example.com", "other2")
        project = self._project_for(db, uuid.UUID(owner_id))

        created = client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "Mine."},
            headers={"Authorization": f"Bearer {owner_token}"},
        ).json()

        response = client.patch(
            f"/api/v1/projects/{project.id}/comments/{created['id']}",
            json={"body": "Not yours."},
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 403

    def test_delete_returns_204_and_tombstones_the_body(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("deleter@example.com", "deleter")
        project = self._project_for(db, uuid.UUID(user_id))
        auth = {"Authorization": f"Bearer {token}"}

        created = client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "Say something regrettable."},
            headers=auth,
        ).json()

        deleted = client.delete(
            f"/api/v1/projects/{project.id}/comments/{created['id']}",
            headers=auth,
        )
        assert deleted.status_code == 204

        listing = client.get(f"/api/v1/projects/{project.id}/comments").json()
        item = listing["items"][0]

        assert item["is_deleted"] is True
        assert item["body"] == "[deleted]"
        assert item["author"] is None
        assert "regrettable" not in listing_text(listing)

    def test_count_endpoint(self, client, db, register_and_login):
        user_id, token = register_and_login("counter@example.com", "counter")
        project = self._project_for(db, uuid.UUID(user_id))
        auth = {"Authorization": f"Bearer {token}"}

        parent = client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "One."},
            headers=auth,
        ).json()
        client.post(
            f"/api/v1/projects/{project.id}/comments",
            json={"body": "Two.", "parent_id": parent["id"]},
            headers=auth,
        )

        response = client.get(f"/api/v1/projects/{project.id}/comments/count")

        assert response.status_code == 200
        assert response.json() == {"count": 2}


def listing_text(payload: dict) -> str:
    """Flatten a listing to a string, for 'must not appear anywhere' checks."""
    import json

    return json.dumps(payload)
