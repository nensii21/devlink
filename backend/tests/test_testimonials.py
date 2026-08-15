"""
Unit & integration tests for peer testimonials (#1044).

The permission rules are the feature here, so most of these tests are about
who may do what rather than about storage.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

# Aliased away from a Test* prefix so pytest does not try to collect the
# model and schema classes as test cases.
from app.models.testimonial import MAX_BODY_LENGTH, MAX_FEATURED, MIN_BODY_LENGTH
from app.models.testimonial import Testimonial as DbTestimonial
from app.models.testimonial import TestimonialStatus as Status
from app.models.user import User
from app.schemas.testimonial import TestimonialCreate as CreatePayload
from app.schemas.testimonial import TestimonialUpdate as UpdatePayload
from app.services.testimonial_service import TestimonialService

GOOD_BODY = (
    "We shipped the ingest pipeline together over three months. Calm under "
    "pressure, wrote the tests nobody wanted to write, and left the codebase "
    "better than they found it."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(username: str = "ada") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    return user


def _make_testimonial(
    subject_id: uuid.UUID,
    author_id: uuid.UUID,
    status: Status = Status.PENDING,
) -> MagicMock:
    item = MagicMock(spec=DbTestimonial)
    item.id = uuid.uuid4()
    item.subject_id = subject_id
    item.author_id = author_id
    item.status = status
    item.is_featured = False
    return item


# ---------------------------------------------------------------------------
# 1. Body validation
# ---------------------------------------------------------------------------


class TestBodyValidation:
    def test_a_real_testimonial_is_accepted(self):
        payload = CreatePayload(
            subject_id=uuid.uuid4(), relationship="collaborator", body=GOOD_BODY
        )
        assert payload.body == GOOD_BODY

    def test_two_words_is_rejected(self):
        # A one-line "great dev!" carries no information and dilutes the
        # testimonials that do.
        with pytest.raises(Exception):
            CreatePayload(
                subject_id=uuid.uuid4(), relationship="mentor", body="Great dev!"
            )

    def test_exactly_the_minimum_is_accepted(self):
        payload = CreatePayload(
            subject_id=uuid.uuid4(), relationship="mentor", body="x" * MIN_BODY_LENGTH
        )
        assert len(payload.body) == MIN_BODY_LENGTH

    def test_whitespace_padding_does_not_buy_length(self):
        padded = "  " + ("x" * (MIN_BODY_LENGTH - 10)) + "  "
        with pytest.raises(Exception):
            CreatePayload(subject_id=uuid.uuid4(), relationship="mentor", body=padded)

    def test_body_is_stripped(self):
        payload = CreatePayload(
            subject_id=uuid.uuid4(), relationship="client", body=f"  {GOOD_BODY}  "
        )
        assert payload.body == GOOD_BODY

    def test_overlong_body_is_rejected(self):
        with pytest.raises(Exception):
            CreatePayload(
                subject_id=uuid.uuid4(),
                relationship="client",
                body="x" * (MAX_BODY_LENGTH + 1),
            )

    def test_unknown_relationship_is_rejected(self):
        with pytest.raises(Exception):
            CreatePayload(
                subject_id=uuid.uuid4(), relationship="nemesis", body=GOOD_BODY
            )

    def test_update_omits_unset_fields(self):
        assert UpdatePayload(body=GOOD_BODY).model_dump(exclude_unset=True) == {
            "body": GOOD_BODY
        }


# ---------------------------------------------------------------------------
# 2. Write guards
# ---------------------------------------------------------------------------


class TestWriteGuards:
    def test_self_testimonial_is_rejected(self):
        db = MagicMock(spec=Session)
        user = _make_user()
        with pytest.raises(HTTPException) as exc:
            TestimonialService.require_writable(db, user, user.id)
        assert exc.value.status_code == 400
        assert "yourself" in exc.value.detail

    def test_blocked_pair_is_rejected(self):
        db = MagicMock(spec=Session)
        author = _make_user("author")
        subject_id = uuid.uuid4()

        with patch(
            "app.services.testimonial_service.BlockService.is_blocked",
            return_value=True,
        ):
            with pytest.raises(HTTPException) as exc:
                TestimonialService.require_writable(db, author, subject_id)
        assert exc.value.status_code == 403

    def test_unblocked_pair_is_allowed(self):
        db = MagicMock(spec=Session)
        author = _make_user("author")
        with patch(
            "app.services.testimonial_service.BlockService.is_blocked",
            return_value=False,
        ):
            TestimonialService.require_writable(db, author, uuid.uuid4())

    def test_self_check_runs_before_the_block_lookup(self):
        # Writing about yourself is always wrong, block or no block.
        db = MagicMock(spec=Session)
        user = _make_user()
        with patch(
            "app.services.testimonial_service.BlockService.is_blocked"
        ) as is_blocked:
            with pytest.raises(HTTPException):
                TestimonialService.require_writable(db, user, user.id)
            is_blocked.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Role guards
# ---------------------------------------------------------------------------


class TestRoleGuards:
    def test_author_may_edit(self):
        author = _make_user("author")
        item = _make_testimonial(uuid.uuid4(), author.id)
        TestimonialService.require_author(item, author)

    def test_subject_may_not_edit(self):
        subject = _make_user("subject")
        item = _make_testimonial(subject.id, uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            TestimonialService.require_author(item, subject)
        assert exc.value.status_code == 403

    def test_subject_may_moderate(self):
        subject = _make_user("subject")
        item = _make_testimonial(subject.id, uuid.uuid4())
        TestimonialService.require_subject(item, subject)

    def test_author_may_not_moderate(self):
        # If the author could approve their own testimonial, approval would
        # mean nothing at all.
        author = _make_user("author")
        item = _make_testimonial(uuid.uuid4(), author.id)
        with pytest.raises(HTTPException) as exc:
            TestimonialService.require_subject(item, author)
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# 4. Visibility
# ---------------------------------------------------------------------------


class TestVisibility:
    def test_approved_is_public(self):
        item = _make_testimonial(uuid.uuid4(), uuid.uuid4(), Status.APPROVED)
        assert TestimonialService.can_view(item, None) is True

    def test_pending_is_not_public(self):
        item = _make_testimonial(uuid.uuid4(), uuid.uuid4(), Status.PENDING)
        assert TestimonialService.can_view(item, None) is False
        assert TestimonialService.can_view(item, _make_user("stranger")) is False

    def test_pending_is_visible_to_both_parties(self):
        subject = _make_user("subject")
        author = _make_user("author")
        item = _make_testimonial(subject.id, author.id, Status.PENDING)

        assert TestimonialService.can_view(item, subject) is True
        assert TestimonialService.can_view(item, author) is True

    def test_hidden_is_not_public(self):
        item = _make_testimonial(uuid.uuid4(), uuid.uuid4(), Status.HIDDEN)
        assert TestimonialService.can_view(item, None) is False


# ---------------------------------------------------------------------------
# 5. HTTP surface (real database)
# ---------------------------------------------------------------------------


class TestTestimonialEndpoints:
    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _write(self, client, token, subject_id, **overrides):
        payload = {
            "subject_id": str(subject_id),
            "relationship": "collaborator",
            "body": GOOD_BODY,
        }
        payload.update(overrides)
        return client.post(
            "/api/v1/testimonials", json=payload, headers=self._auth(token)
        )

    def test_writing_requires_authentication(self, client):
        response = client.post(
            "/api/v1/testimonials",
            json={
                "subject_id": str(uuid.uuid4()),
                "relationship": "mentor",
                "body": GOOD_BODY,
            },
        )
        assert response.status_code in (401, 403)

    def test_unknown_subject_is_404(self, client, register_and_login):
        _, token = register_and_login("ts1@example.com", "tsuser1")
        assert self._write(client, token, uuid.uuid4()).status_code == 404

    def test_self_testimonial_is_400(self, client, register_and_login):
        user_id, token = register_and_login("ts2@example.com", "tsuser2")
        response = self._write(client, token, user_id)
        assert response.status_code == 400
        assert "yourself" in response.json()["detail"]

    def test_new_testimonial_is_pending_and_hidden_from_the_public(
        self, client, register_and_login
    ):
        subject_id, _ = register_and_login("ts3@example.com", "tsuser3")
        _, author_token = register_and_login("ts4@example.com", "tsuser4")

        created = self._write(client, author_token, subject_id)
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "pending"
        assert created.json()["is_featured"] is False

        # Not on the public profile...
        public = client.get("/api/v1/users/tsuser3/testimonials")
        assert public.status_code == 200
        assert public.json()["total"] == 0

        # ...but the author can see their own.
        written = client.get(
            "/api/v1/testimonials/written", headers=self._auth(author_token)
        )
        assert written.json()["total"] == 1

    def test_subject_sees_pending_in_their_queue(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts5@example.com", "tsuser5")
        _, author_token = register_and_login("ts6@example.com", "tsuser6")
        self._write(client, author_token, subject_id)

        received = client.get(
            "/api/v1/testimonials/received", headers=self._auth(subject_token)
        )
        assert received.status_code == 200
        assert received.json()["total"] == 1
        assert received.json()["items"][0]["status"] == "pending"

    def test_approval_publishes_it(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts7@example.com", "tsuser7")
        _, author_token = register_and_login("ts8@example.com", "tsuser8")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        approved = client.post(
            f"/api/v1/testimonials/{testimonial_id}/approve",
            headers=self._auth(subject_token),
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
        assert approved.json()["responded_at"] is not None

        public = client.get("/api/v1/users/tsuser7/testimonials")
        assert public.json()["total"] == 1

    def test_author_cannot_approve_their_own(self, client, register_and_login):
        subject_id, _ = register_and_login("ts9@example.com", "tsuser9")
        _, author_token = register_and_login("ts10@example.com", "tsuser10")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        response = client.post(
            f"/api/v1/testimonials/{testimonial_id}/approve",
            headers=self._auth(author_token),
        )
        assert response.status_code == 403

        # And it is still pending.
        assert client.get("/api/v1/users/tsuser9/testimonials").json()["total"] == 0

    def test_a_stranger_cannot_approve(self, client, register_and_login):
        subject_id, _ = register_and_login("ts11@example.com", "tsuser11")
        _, author_token = register_and_login("ts12@example.com", "tsuser12")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        _, stranger_token = register_and_login("ts13@example.com", "tsuser13")
        response = client.post(
            f"/api/v1/testimonials/{testimonial_id}/approve",
            headers=self._auth(stranger_token),
        )
        assert response.status_code == 403

    def test_second_testimonial_for_the_same_person_is_409(
        self, client, register_and_login
    ):
        subject_id, _ = register_and_login("ts14@example.com", "tsuser14")
        _, author_token = register_and_login("ts15@example.com", "tsuser15")

        assert self._write(client, author_token, subject_id).status_code == 201
        second = self._write(client, author_token, subject_id)
        assert second.status_code == 409
        assert "already written" in second.json()["detail"]

    def test_editing_an_approved_testimonial_resets_it_to_pending(
        self, client, register_and_login
    ):
        # Otherwise approval is a rubber stamp: get something bland approved,
        # then swap the text for anything at all.
        subject_id, subject_token = register_and_login("ts16@example.com", "tsuser16")
        _, author_token = register_and_login("ts17@example.com", "tsuser17")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        client.post(
            f"/api/v1/testimonials/{testimonial_id}/approve",
            headers=self._auth(subject_token),
        )
        client.post(
            f"/api/v1/testimonials/{testimonial_id}/feature",
            headers=self._auth(subject_token),
        )

        edited = client.patch(
            f"/api/v1/testimonials/{testimonial_id}",
            json={"body": GOOD_BODY + " Also shipped the migration single-handed."},
            headers=self._auth(author_token),
        )
        assert edited.status_code == 200
        assert edited.json()["status"] == "pending"
        assert edited.json()["is_featured"] is False

        # And it drops off the public profile again.
        assert client.get("/api/v1/users/tsuser16/testimonials").json()["total"] == 0

    def test_subject_cannot_edit_the_text(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts18@example.com", "tsuser18")
        _, author_token = register_and_login("ts19@example.com", "tsuser19")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        response = client.patch(
            f"/api/v1/testimonials/{testimonial_id}",
            json={"body": "x" * MIN_BODY_LENGTH},
            headers=self._auth(subject_token),
        )
        assert response.status_code == 403

    def test_subject_can_hide_but_not_delete(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts20@example.com", "tsuser20")
        _, author_token = register_and_login("ts21@example.com", "tsuser21")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        client.post(
            f"/api/v1/testimonials/{testimonial_id}/approve",
            headers=self._auth(subject_token),
        )

        hidden = client.post(
            f"/api/v1/testimonials/{testimonial_id}/hide",
            headers=self._auth(subject_token),
        )
        assert hidden.status_code == 200
        assert hidden.json()["status"] == "hidden"

        # Someone else's opinion is not theirs to erase.
        deleted = client.delete(
            f"/api/v1/testimonials/{testimonial_id}", headers=self._auth(subject_token)
        )
        assert deleted.status_code == 403

    def test_author_can_delete_their_own(self, client, register_and_login):
        subject_id, _ = register_and_login("ts22@example.com", "tsuser22")
        _, author_token = register_and_login("ts23@example.com", "tsuser23")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        response = client.delete(
            f"/api/v1/testimonials/{testimonial_id}", headers=self._auth(author_token)
        )
        assert response.status_code == 204

    def test_featuring_requires_approval(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts24@example.com", "tsuser24")
        _, author_token = register_and_login("ts25@example.com", "tsuser25")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        response = client.post(
            f"/api/v1/testimonials/{testimonial_id}/feature",
            headers=self._auth(subject_token),
        )
        assert response.status_code == 400

    def test_featuring_a_fourth_is_rejected(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts26@example.com", "tsuser26")

        ids = []
        for i in range(MAX_FEATURED + 1):
            _, author_token = register_and_login(
                f"ts26a{i}@example.com", f"tsauthor26{i}"
            )
            testimonial_id = self._write(client, author_token, subject_id).json()["id"]
            client.post(
                f"/api/v1/testimonials/{testimonial_id}/approve",
                headers=self._auth(subject_token),
            )
            ids.append(testimonial_id)

        for testimonial_id in ids[:MAX_FEATURED]:
            response = client.post(
                f"/api/v1/testimonials/{testimonial_id}/feature",
                headers=self._auth(subject_token),
            )
            assert response.status_code == 200

        one_too_many = client.post(
            f"/api/v1/testimonials/{ids[MAX_FEATURED]}/feature",
            headers=self._auth(subject_token),
        )
        assert one_too_many.status_code == 400
        assert str(MAX_FEATURED) in one_too_many.json()["detail"]

    def test_un_featuring_frees_a_slot(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts27@example.com", "tsuser27")

        ids = []
        for i in range(MAX_FEATURED + 1):
            _, author_token = register_and_login(
                f"ts27a{i}@example.com", f"tsauthor27{i}"
            )
            testimonial_id = self._write(client, author_token, subject_id).json()["id"]
            client.post(
                f"/api/v1/testimonials/{testimonial_id}/approve",
                headers=self._auth(subject_token),
            )
            ids.append(testimonial_id)

        for testimonial_id in ids[:MAX_FEATURED]:
            client.post(
                f"/api/v1/testimonials/{testimonial_id}/feature",
                headers=self._auth(subject_token),
            )

        client.post(
            f"/api/v1/testimonials/{ids[0]}/feature",
            params={"featured": False},
            headers=self._auth(subject_token),
        )

        response = client.post(
            f"/api/v1/testimonials/{ids[MAX_FEATURED]}/feature",
            headers=self._auth(subject_token),
        )
        assert response.status_code == 200

    def test_hiding_un_features(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts28@example.com", "tsuser28")
        _, author_token = register_and_login("ts29@example.com", "tsuser29")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        client.post(
            f"/api/v1/testimonials/{testimonial_id}/approve",
            headers=self._auth(subject_token),
        )
        client.post(
            f"/api/v1/testimonials/{testimonial_id}/feature",
            headers=self._auth(subject_token),
        )

        hidden = client.post(
            f"/api/v1/testimonials/{testimonial_id}/hide",
            headers=self._auth(subject_token),
        )
        assert hidden.json()["is_featured"] is False

    def test_pending_testimonial_is_404_for_a_stranger(
        self, client, register_and_login
    ):
        subject_id, _ = register_and_login("ts30@example.com", "tsuser30")
        _, author_token = register_and_login("ts31@example.com", "tsuser31")
        testimonial_id = self._write(client, author_token, subject_id).json()["id"]

        # A 403 would confirm an unapproved testimonial about this person
        # exists, which is exactly what moderation is meant to hide.
        assert client.get(f"/api/v1/testimonials/{testimonial_id}").status_code == 404
        assert (
            client.get(
                f"/api/v1/testimonials/{testimonial_id}",
                headers=self._auth(author_token),
            ).status_code
            == 200
        )

    def test_status_filter_is_ignored_for_the_public(self, client, register_and_login):
        subject_id, _ = register_and_login("ts32@example.com", "tsuser32")
        _, author_token = register_and_login("ts33@example.com", "tsuser33")
        self._write(client, author_token, subject_id)

        response = client.get(
            "/api/v1/users/tsuser32/testimonials", params={"status": "pending"}
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_summary_counts_only_approved(self, client, register_and_login):
        subject_id, subject_token = register_and_login("ts34@example.com", "tsuser34")

        _, first_token = register_and_login("ts35@example.com", "tsuser35")
        approved_id = self._write(
            client, first_token, subject_id, relationship="mentor"
        ).json()["id"]
        client.post(
            f"/api/v1/testimonials/{approved_id}/approve",
            headers=self._auth(subject_token),
        )

        _, second_token = register_and_login("ts36@example.com", "tsuser36")
        self._write(client, second_token, subject_id, relationship="client")

        summary = client.get("/api/v1/users/tsuser34/testimonials/summary")
        assert summary.status_code == 200
        body = summary.json()
        assert body["total_approved"] == 1
        assert body["max_featured"] == MAX_FEATURED
        assert [entry["relationship"] for entry in body["by_relationship"]] == [
            "mentor"
        ]
        assert body["featured"] == []

    def test_unknown_username_is_404(self, client):
        assert (
            client.get("/api/v1/users/no-such-person/testimonials").status_code == 404
        )
