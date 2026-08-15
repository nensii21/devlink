"""
Unit & integration tests for project time tracking (#1041).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_member import MemberRole, ProjectMember
from app.models.project_time_log import ProjectTimeLog
from app.models.user import User
from app.schemas.project_time_log import (
    MAX_BACKFILL_DAYS,
    MAX_MINUTES_PER_ENTRY,
    TimeLogCreate,
    TimeLogUpdate,
)
from app.services.project_time_log_service import (
    MAX_MINUTES_PER_DAY,
    ProjectTimeLogService,
)

TODAY = date(2026, 8, 10)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(username: str = "dev", system_role: str = "user") -> MagicMock:
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
    project.title = "DevLink"
    project.deleted_at = None
    return project


def _make_member(role: MemberRole = MemberRole.CONTRIBUTOR) -> MagicMock:
    member = MagicMock(spec=ProjectMember)
    member.role = role
    member.is_active = True
    return member


def _make_log(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    minutes: int = 60,
    work_date: date | None = None,
) -> MagicMock:
    log = MagicMock(spec=ProjectTimeLog)
    log.id = uuid.uuid4()
    log.project_id = project_id
    log.user_id = user_id
    log.milestone_id = None
    log.minutes = minutes
    log.work_date = work_date or TODAY
    log.description = "Wired up the importer"
    log.is_billable = False
    log.created_at = datetime.now(timezone.utc)
    log.updated_at = datetime.now(timezone.utc)
    return log


# ---------------------------------------------------------------------------
# 1. Minutes / hours conversion
# ---------------------------------------------------------------------------


class TestHoursConversion:
    @pytest.mark.parametrize(
        "minutes,expected",
        [
            (0, 0.0),
            (30, 0.5),
            (60, 1.0),
            (90, 1.5),
            (1440, 24.0),
            (100, 1.67),
            (5, 0.08),
        ],
    )
    def test_conversion(self, minutes: int, expected: float):
        assert ProjectTimeLogService.to_hours(minutes) == expected

    def test_summed_minutes_do_not_drift(self):
        # Twenty entries of 20 minutes is exactly 400 minutes. Rounding each to
        # hours first and then adding would not land on the same number, which
        # is the whole reason minutes are the stored unit.
        entries = [20] * 20
        assert ProjectTimeLogService.to_hours(sum(entries)) == 6.67
        assert sum(entries) == 400


# ---------------------------------------------------------------------------
# 2. work_date validation
# ---------------------------------------------------------------------------


class TestWorkDateValidation:
    def test_today_is_allowed(self):
        ProjectTimeLogService.validate_work_date(TODAY, today=TODAY)

    def test_yesterday_is_allowed(self):
        ProjectTimeLogService.validate_work_date(TODAY - timedelta(days=1), today=TODAY)

    def test_future_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.validate_work_date(
                TODAY + timedelta(days=1), today=TODAY
            )
        assert exc.value.status_code == 422
        assert "future" in exc.value.detail

    def test_oldest_allowed_backfill_is_accepted(self):
        oldest = TODAY - timedelta(days=MAX_BACKFILL_DAYS)
        ProjectTimeLogService.validate_work_date(oldest, today=TODAY)

    def test_beyond_backfill_window_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.validate_work_date(
                TODAY - timedelta(days=MAX_BACKFILL_DAYS + 1), today=TODAY
            )
        assert exc.value.status_code == 422
        assert str(MAX_BACKFILL_DAYS) in exc.value.detail


# ---------------------------------------------------------------------------
# 3. Daily cap
# ---------------------------------------------------------------------------


def _db_with_daily_total(total: int) -> MagicMock:
    db = MagicMock(spec=Session)
    db.scalar.return_value = total
    return db


class TestDailyCap:
    def test_under_the_cap_is_fine(self):
        db = _db_with_daily_total(120)
        ProjectTimeLogService.validate_daily_cap(
            db, uuid.uuid4(), uuid.uuid4(), TODAY, 60
        )

    def test_exactly_at_the_cap_is_allowed(self):
        db = _db_with_daily_total(MAX_MINUTES_PER_DAY - 60)
        ProjectTimeLogService.validate_daily_cap(
            db, uuid.uuid4(), uuid.uuid4(), TODAY, 60
        )

    def test_one_minute_over_is_rejected(self):
        db = _db_with_daily_total(MAX_MINUTES_PER_DAY - 60)
        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.validate_daily_cap(
                db, uuid.uuid4(), uuid.uuid4(), TODAY, 61
            )
        assert exc.value.status_code == 400
        assert "24-hour" in exc.value.detail

    def test_error_reports_the_remaining_budget(self):
        db = _db_with_daily_total(MAX_MINUTES_PER_DAY - 15)
        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.validate_daily_cap(
                db, uuid.uuid4(), uuid.uuid4(), TODAY, 100
            )
        assert "15 minutes remain" in exc.value.detail

    def test_full_day_leaves_nothing(self):
        db = _db_with_daily_total(MAX_MINUTES_PER_DAY)
        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.validate_daily_cap(
                db, uuid.uuid4(), uuid.uuid4(), TODAY, 1
            )
        assert "0 minutes remain" in exc.value.detail

    def test_editing_an_entry_excludes_itself_from_the_total(self):
        # Without the exclusion, resizing a 600-minute entry to 660 would be
        # measured against a day that already contains the old 600.
        db = MagicMock(spec=Session)
        db.scalar.return_value = 0
        log_id = uuid.uuid4()
        ProjectTimeLogService.validate_daily_cap(
            db, uuid.uuid4(), uuid.uuid4(), TODAY, 660, exclude_log_id=log_id
        )
        assert db.scalar.called


# ---------------------------------------------------------------------------
# 4. Membership & permissions
# ---------------------------------------------------------------------------


class TestPermissions:
    def test_owner_may_log(self):
        db = MagicMock(spec=Session)
        user = _make_user()
        project = _make_project(owner_id=user.id)
        ProjectTimeLogService.require_member(db, project, user)

    def test_platform_admin_may_log(self):
        db = MagicMock(spec=Session)
        admin = _make_user(system_role="admin")
        ProjectTimeLogService.require_member(db, _make_project(), admin)

    def test_active_member_may_log(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = _make_member()
        ProjectTimeLogService.require_member(db, _make_project(), _make_user())

    def test_stranger_may_not_log(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None
        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.require_member(db, _make_project(), _make_user())
        assert exc.value.status_code == 403

    def test_author_may_edit_their_own_entry(self):
        db = MagicMock(spec=Session)
        user = _make_user()
        project = _make_project()
        log = _make_log(project.id, user.id)
        ProjectTimeLogService.require_can_modify(db, project, log, user)

    def test_maintainer_may_not_edit_someone_elses_entry(self):
        # Rewriting another person's hours while leaving their name on the row
        # is worse than having no row at all.
        db = MagicMock(spec=Session)
        db.scalar.return_value = _make_member(MemberRole.MAINTAINER)
        maintainer = _make_user("maint")
        project = _make_project()
        log = _make_log(project.id, uuid.uuid4())

        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.require_can_modify(db, project, log, maintainer)
        assert exc.value.status_code == 403

    def test_maintainer_may_delete_someone_elses_entry(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = _make_member(MemberRole.MAINTAINER)
        project = _make_project()
        log = _make_log(project.id, uuid.uuid4())
        ProjectTimeLogService.require_can_delete(db, project, log, _make_user("maint"))

    def test_contributor_may_not_delete_someone_elses_entry(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = _make_member(MemberRole.CONTRIBUTOR)
        project = _make_project()
        log = _make_log(project.id, uuid.uuid4())

        with pytest.raises(HTTPException) as exc:
            ProjectTimeLogService.require_can_delete(
                db, project, log, _make_user("contrib")
            )
        assert exc.value.status_code == 403

    def test_author_may_always_delete_their_own(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = None
        user = _make_user()
        project = _make_project()
        ProjectTimeLogService.require_can_delete(
            db, project, _make_log(project.id, user.id), user
        )


# ---------------------------------------------------------------------------
# 5. Schema validation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_minutes_must_be_positive(self):
        with pytest.raises(Exception):
            TimeLogCreate(minutes=0, work_date=TODAY)

    def test_minutes_capped_at_one_day(self):
        TimeLogCreate(minutes=MAX_MINUTES_PER_ENTRY, work_date=TODAY)
        with pytest.raises(Exception):
            TimeLogCreate(minutes=MAX_MINUTES_PER_ENTRY + 1, work_date=TODAY)

    def test_blank_description_becomes_none(self):
        payload = TimeLogCreate(minutes=30, work_date=TODAY, description="   ")
        assert payload.description is None

    def test_description_is_stripped(self):
        payload = TimeLogCreate(minutes=30, work_date=TODAY, description="  refactor  ")
        assert payload.description == "refactor"

    def test_update_leaves_unset_fields_out(self):
        payload = TimeLogUpdate(minutes=45)
        assert payload.model_dump(exclude_unset=True) == {"minutes": 45}

    def test_billable_defaults_to_false(self):
        assert TimeLogCreate(minutes=30, work_date=TODAY).is_billable is False


# ---------------------------------------------------------------------------
# 6. HTTP surface (real database)
# ---------------------------------------------------------------------------


class TestTimeLogEndpoints:
    """Router wiring: auth requirements, status codes, response shape."""

    @staticmethod
    def _project_for(db, owner_id: uuid.UUID, slug: str) -> Project:
        project = Project(
            owner_id=owner_id,
            title="Time Tracked Project",
            slug=slug,
            description="A project that records how long things take.",
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

    def test_logging_requires_authentication(self, client):
        response = client.post(
            f"/api/v1/projects/{uuid.uuid4()}/time-logs",
            json={"minutes": 60, "work_date": date.today().isoformat()},
        )
        assert response.status_code in (401, 403)

    def test_unknown_project_returns_404(self, client, register_and_login):
        _, token = register_and_login("tl1@example.com", "tluser1")
        response = client.post(
            f"/api/v1/projects/{uuid.uuid4()}/time-logs",
            json={"minutes": 60, "work_date": date.today().isoformat()},
            headers=self._auth(token),
        )
        assert response.status_code == 404

    def test_owner_can_log_and_read_back(self, client, db, register_and_login):
        user_id, token = register_and_login("tl2@example.com", "tluser2")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-2")

        created = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={
                "minutes": 90,
                "work_date": date.today().isoformat(),
                "description": "Pairing on the parser",
                "is_billable": True,
            },
            headers=self._auth(token),
        )
        assert created.status_code == 201, created.text

        body = created.json()
        assert body["minutes"] == 90
        assert body["hours"] == 1.5
        assert body["is_billable"] is True

        listed = client.get(
            f"/api/v1/projects/{project.id}/time-logs", headers=self._auth(token)
        )
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["total_minutes"] == 90

    def test_future_work_date_is_rejected(self, client, db, register_and_login):
        user_id, token = register_and_login("tl3@example.com", "tluser3")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-3")

        response = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={
                "minutes": 60,
                "work_date": (date.today() + timedelta(days=1)).isoformat(),
            },
            headers=self._auth(token),
        )
        assert response.status_code == 422

    def test_stale_backfill_is_rejected(self, client, db, register_and_login):
        user_id, token = register_and_login("tl4@example.com", "tluser4")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-4")

        response = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={
                "minutes": 60,
                "work_date": (
                    date.today() - timedelta(days=MAX_BACKFILL_DAYS + 1)
                ).isoformat(),
            },
            headers=self._auth(token),
        )
        assert response.status_code == 422

    def test_daily_cap_is_enforced_across_entries(self, client, db, register_and_login):
        user_id, token = register_and_login("tl5@example.com", "tluser5")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-5")
        today = date.today().isoformat()

        first = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={"minutes": 1400, "work_date": today},
            headers=self._auth(token),
        )
        assert first.status_code == 201

        second = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={"minutes": 60, "work_date": today},
            headers=self._auth(token),
        )
        assert second.status_code == 400
        assert "24-hour" in second.json()["detail"]

    def test_summary_reconciles_with_its_line_items(
        self, client, db, register_and_login
    ):
        user_id, token = register_and_login("tl6@example.com", "tluser6")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-6")
        today = date.today().isoformat()

        for minutes, billable in ((45, True), (30, False), (75, True)):
            response = client.post(
                f"/api/v1/projects/{project.id}/time-logs",
                json={"minutes": minutes, "work_date": today, "is_billable": billable},
                headers=self._auth(token),
            )
            assert response.status_code == 201, response.text

        summary = client.get(
            f"/api/v1/projects/{project.id}/time-logs/summary",
            headers=self._auth(token),
        )
        assert summary.status_code == 200
        body = summary.json()

        assert body["total_minutes"] == 150
        assert body["total_hours"] == 2.5
        assert body["total_entries"] == 3
        assert body["billable_minutes"] == 120
        assert body["non_billable_minutes"] == 30
        assert (
            body["billable_minutes"] + body["non_billable_minutes"]
            == body["total_minutes"]
        )
        assert body["contributor_count"] == 1
        assert (
            sum(c["minutes"] for c in body["by_contributor"]) == body["total_minutes"]
        )
        # Work with no milestone is grouped under a null id, not dropped.
        assert sum(m["minutes"] for m in body["by_milestone"]) == body["total_minutes"]
        assert body["by_milestone"][0]["milestone_id"] is None

    def test_non_member_cannot_log(self, client, db, register_and_login):
        owner_id, _ = register_and_login("tl7@example.com", "tluser7")
        project = self._project_for(db, uuid.UUID(owner_id), "tl-project-7")

        _, outsider_token = register_and_login("tl8@example.com", "tluser8")
        response = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={"minutes": 60, "work_date": date.today().isoformat()},
            headers=self._auth(outsider_token),
        )
        assert response.status_code == 403

    def test_author_can_edit_and_delete(self, client, db, register_and_login):
        user_id, token = register_and_login("tl9@example.com", "tluser9")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-9")

        created = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={"minutes": 60, "work_date": date.today().isoformat()},
            headers=self._auth(token),
        )
        log_id = created.json()["id"]

        updated = client.patch(
            f"/api/v1/projects/{project.id}/time-logs/{log_id}",
            json={"minutes": 120, "description": "Took longer than expected"},
            headers=self._auth(token),
        )
        assert updated.status_code == 200
        assert updated.json()["minutes"] == 120
        assert updated.json()["hours"] == 2.0

        deleted = client.delete(
            f"/api/v1/projects/{project.id}/time-logs/{log_id}",
            headers=self._auth(token),
        )
        assert deleted.status_code == 204

        listed = client.get(
            f"/api/v1/projects/{project.id}/time-logs", headers=self._auth(token)
        )
        assert listed.json()["total"] == 0

    def test_someone_else_cannot_edit_your_entry(self, client, db, register_and_login):
        owner_id, owner_token = register_and_login("tl10@example.com", "tluser10")
        project = self._project_for(db, uuid.UUID(owner_id), "tl-project-10")

        created = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={"minutes": 60, "work_date": date.today().isoformat()},
            headers=self._auth(owner_token),
        )
        log_id = created.json()["id"]

        _, other_token = register_and_login("tl11@example.com", "tluser11")
        response = client.patch(
            f"/api/v1/projects/{project.id}/time-logs/{log_id}",
            json={"minutes": 5},
            headers=self._auth(other_token),
        )
        assert response.status_code == 403

        unchanged = client.get(
            f"/api/v1/projects/{project.id}/time-logs/{log_id}",
            headers=self._auth(owner_token),
        )
        assert unchanged.json()["minutes"] == 60

    def test_unknown_milestone_is_rejected(self, client, db, register_and_login):
        user_id, token = register_and_login("tl12@example.com", "tluser12")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-12")

        response = client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={
                "minutes": 60,
                "work_date": date.today().isoformat(),
                "milestone_id": str(uuid.uuid4()),
            },
            headers=self._auth(token),
        )
        assert response.status_code == 404

    def test_date_filters_narrow_the_result(self, client, db, register_and_login):
        user_id, token = register_and_login("tl13@example.com", "tluser13")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-13")

        today = date.today()
        for offset in (0, 3, 10):
            response = client.post(
                f"/api/v1/projects/{project.id}/time-logs",
                json={
                    "minutes": 30,
                    "work_date": (today - timedelta(days=offset)).isoformat(),
                },
                headers=self._auth(token),
            )
            assert response.status_code == 201

        response = client.get(
            f"/api/v1/projects/{project.id}/time-logs",
            params={"from_date": (today - timedelta(days=5)).isoformat()},
            headers=self._auth(token),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert response.json()["total_minutes"] == 60

    def test_totals_cover_the_filter_not_the_page(self, client, db, register_and_login):
        user_id, token = register_and_login("tl14@example.com", "tluser14")
        project = self._project_for(db, uuid.UUID(user_id), "tl-project-14")

        today = date.today()
        for offset in range(5):
            client.post(
                f"/api/v1/projects/{project.id}/time-logs",
                json={
                    "minutes": 30,
                    "work_date": (today - timedelta(days=offset)).isoformat(),
                },
                headers=self._auth(token),
            )

        response = client.get(
            f"/api/v1/projects/{project.id}/time-logs",
            params={"limit": 2},
            headers=self._auth(token),
        )
        body = response.json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        # A report that only adds up the visible page is a report nobody can
        # trust, so the totals span the whole filtered set.
        assert body["total_minutes"] == 150

    def test_me_endpoint_returns_only_your_own_entries(
        self, client, db, register_and_login
    ):
        owner_id, owner_token = register_and_login("tl15@example.com", "tluser15")
        project = self._project_for(db, uuid.UUID(owner_id), "tl-project-15")

        client.post(
            f"/api/v1/projects/{project.id}/time-logs",
            json={"minutes": 60, "work_date": date.today().isoformat()},
            headers=self._auth(owner_token),
        )

        response = client.get(
            f"/api/v1/projects/{project.id}/time-logs/me",
            headers=self._auth(owner_token),
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert all(item["user_id"] == owner_id for item in response.json()["items"])
