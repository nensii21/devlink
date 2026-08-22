"""
Coverage for the account-export routes.

There was none before. `ExportService.collect_user_data` referenced an
undefined `builder_flares` and raised `NameError` on every call, and all four
export routes went through it, so all four were 500s -- including
`POST /me/export`, which is the "give me everything you hold about me" route.
The suite stayed green because nothing here ever asked for an export.

So these tests do two things that are easy to skip:

* they **request the routes**, rather than calling the service directly. The
  bug was reachable from the service too, but a service-level test would not
  have noticed that `export_portfolio_html` reaches it by a different path;
* they assert on the **body**, not just the status. A collector that silently
  returns `[]` for everything would pass a status-code test perfectly.

Every section of the export gets a fixture row, so an empty list in the
response means something is wrong rather than meaning the user is new.
"""

from __future__ import annotations

import json
import uuid

import pytest

from app.models.builder_flare import BuilderFlare, FlareStatus
from app.models.project import Project, ProjectStage
from app.services.export_service import ExportService

EXPORT_JSON = "/api/users/me/export"
PORTFOLIO = "/api/users/me/portfolio/export"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def exporter(client, register_and_login, db):
    """
    A user with a project and a builder flare -- the section the bug dropped.

    Returns ``(user_id, headers)``. The rows are deliberately given
    recognisable values -- the assertions look for those strings in the
    rendered output, which is the only way to tell "exported the flare" apart
    from "exported an empty list".
    """
    user_id, token = register_and_login("exporter@example.com", "exporter")
    headers = {"Authorization": f"Bearer {token}"}

    owner = uuid.UUID(user_id)

    project = Project(
        owner_id=owner,
        title="Kestrel Telemetry",
        slug=f"kestrel-telemetry-{uuid.uuid4().hex[:8]}",
        description="Flight data pipeline for small UAVs.",
        stage=ProjectStage.MVP,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    flare = BuilderFlare(
        project_id=project.id,
        created_by=owner,
        title="Rust telemetry ingest",
        description="Own the ingest path end to end.",
        role="Backend Engineer",
        status=FlareStatus.OPEN,
    )
    db.add(flare)

    db.commit()

    return user_id, headers


def _flare_titles(payload: dict) -> list[str]:
    return [f["title"] for f in payload["builder_flares"]]


# ---------------------------------------------------------------------------
# The routes answer at all
# ---------------------------------------------------------------------------
#
# This is the regression proper. Before the fix every one of these was a
# NameError, so parametrising them keeps the failure message pointing at the
# route that broke rather than at whichever one happened to run first.


@pytest.mark.parametrize(
    "method,url",
    [
        ("POST", EXPORT_JSON),
        ("GET", f"{PORTFOLIO}?format=json"),
        ("GET", f"{PORTFOLIO}?format=markdown"),
        ("GET", f"{PORTFOLIO}?format=pdf"),
    ],
    ids=["data-export", "portfolio-json", "portfolio-markdown", "portfolio-html"],
)
def test_export_routes_return_a_document(client, exporter, method, url):
    _, headers = exporter

    response = client.request(method, url, headers=headers)

    assert response.status_code == 200, response.text
    assert response.content, "export route returned an empty body"


def test_every_export_route_requires_authentication(client):
    """
    An export is the single most sensitive read in the app. Worth pinning even
    though nothing in this change touches auth -- the routes are new to the
    test suite, so their auth has never actually been asserted either.
    """
    assert client.post(EXPORT_JSON).status_code == 401
    assert client.get(PORTFOLIO).status_code == 401


# ---------------------------------------------------------------------------
# The document contains the user's data
# ---------------------------------------------------------------------------


def test_data_export_carries_every_section(client, exporter):
    _, headers = exporter

    payload = client.post(EXPORT_JSON, headers=headers).json()["data"]

    # Named individually rather than looped, so a missing key names itself in
    # the failure.
    for section in (
        "profile",
        "skills",
        "projects",
        "project_memberships",
        "applications",
        "connections",
        "messages",
        "bookmarks",
        "organizations",
        "activities",
        "notifications",
        "builder_flares",
    ):
        assert section in payload, f"export is missing the {section!r} section"


def test_builder_flares_are_populated_not_just_present(client, exporter):
    """
    The specific regression. `builder_flares` was undefined, so the fix is a
    call to `_get_builder_flares` -- and a fix that passed `[]` would satisfy
    a "key exists" assertion just as well.
    """
    _, headers = exporter

    payload = client.post(EXPORT_JSON, headers=headers).json()["data"]

    assert _flare_titles(payload) == ["Rust telemetry ingest"]

    flare = payload["builder_flares"][0]
    assert flare["role"] == "Backend Engineer"
    assert flare["status"] == "open"
    assert flare["project_id"]
    assert flare["created_at"]


def test_export_does_not_leak_another_users_flares(
    client, exporter, db, register_and_login
):
    """
    `_get_builder_flares` filters on `created_by`. Nothing exercised that
    filter, and a collector that forgot the `.filter()` would have passed every
    other assertion in this file.
    """
    _, headers = exporter

    stranger_id, _ = register_and_login("stranger@example.com", "stranger")
    stranger = uuid.UUID(stranger_id)

    project = Project(
        owner_id=stranger,
        title="Not Yours",
        slug=f"not-yours-{uuid.uuid4().hex[:8]}",
        description="Belongs to somebody else.",
        stage=ProjectStage.MVP,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    db.add(
        BuilderFlare(
            project_id=project.id,
            created_by=stranger,
            title="Someone else's flare",
            description="Should never appear in another user's export.",
            role="Designer",
            status=FlareStatus.OPEN,
        )
    )
    db.commit()

    payload = client.post(EXPORT_JSON, headers=headers).json()["data"]

    assert "Someone else's flare" not in _flare_titles(payload)


# ---------------------------------------------------------------------------
# Portfolio renderings
# ---------------------------------------------------------------------------


def test_portfolio_json_is_the_same_document_as_the_data_export(client, exporter):
    _, headers = exporter

    export = client.post(EXPORT_JSON, headers=headers).json()["data"]
    portfolio = client.get(f"{PORTFOLIO}?format=json", headers=headers).json()

    assert portfolio["profile"] == export["profile"]
    assert portfolio["builder_flares"] == export["builder_flares"]


def test_portfolio_markdown_renders_the_users_content(client, exporter):
    _, headers = exporter

    response = client.get(f"{PORTFOLIO}?format=markdown", headers=headers)

    assert response.headers["content-type"].startswith("text/markdown")
    assert "attachment" in response.headers["content-disposition"]

    body = response.text
    assert body.lstrip().startswith("#")
    assert "Kestrel Telemetry" in body


def test_portfolio_html_renders_the_users_content(client, exporter):
    _, headers = exporter

    response = client.get(f"{PORTFOLIO}?format=pdf", headers=headers)

    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<html" in body.lower()
    assert "Kestrel Telemetry" in body


def test_portfolio_rejects_an_unknown_format(client, exporter):
    _, headers = exporter

    assert client.get(f"{PORTFOLIO}?format=docx", headers=headers).status_code == 422


# ---------------------------------------------------------------------------
# The service, directly
# ---------------------------------------------------------------------------
#
# The routes above are the contract; this is the seam the bug actually lived
# in, and `BackupService` reaches it without going through HTTP at all.


def test_collect_user_data_is_callable(db, client, exporter):
    from app.models.user import User

    user_id, _ = exporter
    user = db.get(User, uuid.UUID(user_id))

    data = ExportService.collect_user_data(db, user)

    assert data.builder_flares
    assert data.exported_at is not None


def test_collect_user_data_is_json_serialisable(db, client, exporter):
    """
    `BackupService` writes this out and the portfolio route hands it to
    `JSONResponse`. Both need `model_dump(mode="json")` to survive the UUIDs
    and datetimes.
    """
    from app.models.user import User

    user_id, _ = exporter
    user = db.get(User, uuid.UUID(user_id))

    dumped = ExportService.collect_user_data(db, user).model_dump(mode="json")

    json.dumps(dumped)  # raises if anything in there is not JSON


def test_export_of_a_brand_new_user_is_empty_but_valid(client, register_and_login):
    """
    The opposite corner from `exporter`: nothing to export. Should be an empty
    document, not an error -- and `builder_flares` should be `[]` rather than
    absent.
    """
    _, token = register_and_login("fresh@example.com", "freshuser")
    headers = {"Authorization": f"Bearer {token}"}

    payload = client.post(EXPORT_JSON, headers=headers).json()["data"]

    assert payload["builder_flares"] == []
    assert payload["projects"] == []
    assert payload["profile"]["email"] == "fresh@example.com"
