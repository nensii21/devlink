"""The OpenAPI document has to be buildable.

`app.openapi()` was never called anywhere in the suite, so a route whose
signature could not be resolved was invisible: the app imported, every
endpoint test passed, and `/openapi.json` returned a 500 in the browser.

That is exactly the failure mode `from __future__ import annotations` invites.
Annotations become strings at import time, so an unimported name in a route
signature is not a `NameError` when the module loads -- it is a
`PydanticUserError` much later, when FastAPI finally tries to resolve the
forward reference to build a schema for it.

These tests build the document once and then assert things about it, so any
route that cannot describe itself fails here rather than in a client
generator or a docs page.
"""

from __future__ import annotations

from collections import Counter

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def schema() -> dict:
    """The generated document.

    Built once per module: generation walks every route and is the expensive
    part of these tests. `app.openapi_schema` is cleared first so a document
    cached by an earlier test cannot mask a regression here.
    """
    app.openapi_schema = None
    return app.openapi()


def test_openapi_schema_can_be_generated(schema: dict) -> None:
    """The headline check: building the document does not raise.

    A route signature that references a name the module never imported only
    fails at this point, which is why this assertion is worth its own test
    even though every other test in the file depends on the same fixture.
    """
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "DevLink API"


def test_openapi_endpoint_returns_200() -> None:
    """`/openapi.json` is what `/docs` and `/redoc` actually fetch.

    Generation succeeding in-process is not quite the same claim as the
    endpoint returning 200 -- the response also has to serialise -- so this
    goes through the app.
    """
    app.openapi_schema = None
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200, response.text
    body = response.json()
    assert "paths" in body
    assert body["paths"], "schema has no paths at all"


def test_docs_pages_are_served() -> None:
    """The two documentation shells render.

    They only serve HTML that points at `/openapi.json`, so this is a
    thinner check than the one above -- but a 500 here means the docs are
    gone for a different reason, and it is cheap to notice.
    """
    client = TestClient(app)

    for path in ("/docs", "/redoc"):
        response = client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"


def test_schema_documents_the_whole_api(schema: dict) -> None:
    """The document is not quietly truncated.

    `get_openapi` walks the routes it is handed; a router that failed to be
    included at all produces a document that generates cleanly and is simply
    missing a chunk of the API. Anchor on a handful of paths from different
    routers so that kind of loss is visible.
    """
    documented = set(schema["paths"])

    assert len(documented) > 500, f"only {len(documented)} paths documented"

    for path in (
        "/api/auth/login",
        "/api/projects/",
        "/api/messages/",
        "/api/users/me",
    ):
        assert path in documented, f"{path} missing from the OpenAPI document"


def test_operation_ids_are_unique(schema: dict) -> None:
    """Duplicate operation ids break generated clients.

    Two routers registering the same handler under different prefixes -- which
    this app does deliberately in a couple of places for path compatibility --
    produce colliding ids unless one of them is excluded from the schema.
    Generated SDKs then either overwrite one method with the other or refuse
    to build, depending on the generator.
    """
    operation_ids: list[str] = []

    for path_item in schema["paths"].values():
        for method, operation in path_item.items():
            if method in {"parameters", "servers", "summary", "description"}:
                continue
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if operation_id:
                operation_ids.append(operation_id)

    duplicates = sorted(
        operation_id
        for operation_id, count in Counter(operation_ids).items()
        if count > 1
    )

    assert not duplicates, f"duplicate operationId values: {duplicates[:20]}"


def test_no_route_signature_uses_an_unimported_name() -> None:
    """Resolve every route's annotations directly.

    The schema tests above catch this transitively, but the failure they
    report is a wall of Pydantic internals. Resolving the annotations here
    names the offending module, function and parameter, which is the
    information someone actually needs to fix it.
    """
    import typing

    unresolved: list[str] = []

    for route in _api_routes():
        endpoint = route.endpoint
        try:
            typing.get_type_hints(endpoint, include_extras=True)
        except NameError as exc:
            unresolved.append(
                f"{endpoint.__module__}.{endpoint.__qualname__}: {exc}"
            )

    assert not unresolved, "route signatures reference names their module never imported:\n" + "\n".join(
        unresolved
    )


def _api_routes() -> list[APIRoute]:
    """Every `APIRoute` reachable from the app.

    Newer FastAPI does not flatten `include_router` eagerly. `app.routes`
    holds `_IncludedRouter` placeholders that keep the original router on
    `original_router` and only resolve it while matching a request, so a
    naive walk over `.routes` finds five routes for an app with several
    hundred. Follow `original_router` as well, and deduplicate: the same
    router is deliberately included under more than one prefix in places.
    """
    collected: dict[int, APIRoute] = {}

    def walk(routes) -> None:
        for route in routes:
            if isinstance(route, APIRoute):
                collected[id(route)] = route
                continue

            nested = getattr(route, "routes", None)
            if nested:
                walk(nested)

            included = getattr(route, "original_router", None)
            if included is not None and getattr(included, "routes", None):
                walk(included.routes)

    walk(app.routes)
    return list(collected.values())
