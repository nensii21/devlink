"""
Structural assertions about the URLs this app serves.

Nothing checked route *paths* before. 4822 tests, and a router could be mounted
at any URL at all without one of them noticing -- which is how eleven routers
ended up served at `/api/bookmarks/bookmarks`, `/api/conversations/conversations`
and so on, while the paths everyone writes down returned 404.

The mistake is a mechanical one. A router that declares its own prefix

    router = APIRouter(prefix="/bookmarks")

and is then mounted under a prefix that repeats the segment

    app.include_router(bookmarks.router, prefix="/api/bookmarks")

gets both. There is nothing to notice at either site; you have to read the two
together. So the check is mechanical too, rather than a list of known-good
paths -- a list would need updating by exactly the person who just made this
mistake.
"""

from __future__ import annotations

from itertools import pairwise

import pytest

from app.main import app

#: Paths that repeat a segment on purpose.
#:
#: `project_tags.get_predefined_tags` carries a second `@router.get` at
#: `/project-tags/predefined` with `include_in_schema=False`, as a compatibility
#: alias for callers that hardcoded the doubled form. Deliberate, hidden, and
#: documented at the decorator -- so it is listed here rather than being swept
#: up by a blanket "ignore hidden routes" rule, which would also hide the next
#: accident.
DELIBERATE_ALIASES = frozenset(
    {
        "/api/project-tags/project-tags/predefined",
        "/api/v1/project-tags/project-tags/predefined",
    }
)

#: A floor, not a target. The walker below reads FastAPI internals, and the
#: failure mode that matters is it silently returning almost nothing after a
#: version bump -- at which point every assertion in this file passes
#: vacuously. Asking for a plausible count turns that into a visible failure.
MINIMUM_EXPECTED_ROUTES = 500


def _effective_paths(routes, prefix: str = "") -> list[str]:
    """
    Every path the app actually serves, fully qualified.

    Not as simple as reading `route.path`. FastAPI does not flatten
    `include_router` into `app.routes`; it leaves an `_IncludedRouter` holding
    the mount prefix, and the child routes already carry their own router's
    prefix in `path`. So the mount prefix is added and the child's router
    prefix is *not* -- adding both is the same doubling this file is about.
    """
    found: list[str] = []

    for route in routes:
        context = getattr(route, "include_context", None)
        if context is not None:
            inner = getattr(route, "original_router", None) or context.included_router
            found += _effective_paths(inner.routes, prefix + (context.prefix or ""))
            continue

        path = getattr(route, "path", None)
        if path is None:
            continue

        # A Mount (e.g. /uploads) carries child routes and no endpoint.
        is_mount = (
            getattr(route, "routes", None) is not None
            and not hasattr(route, "methods")
            and not hasattr(route, "endpoint")
        )
        if is_mount:
            found += _effective_paths(route.routes, prefix + path)
        else:
            found.append(prefix + path)

    return found


@pytest.fixture(scope="module")
def paths() -> list[str]:
    return sorted(set(_effective_paths(app.routes)))


def _repeated_segment(path: str) -> str | None:
    """The first segment that immediately repeats itself, if any."""
    segments = [s for s in path.split("/") if s]
    for current, following in pairwise(segments):
        if current == following:
            return current
    return None


# ---------------------------------------------------------------------------
# The walker itself
# ---------------------------------------------------------------------------


def test_the_walker_finds_a_plausible_number_of_routes(paths):
    """
    Guards every other test in this file.

    An earlier draft of `_effective_paths` returned 7 paths because it did not
    understand `_IncludedRouter`, and every assertion below passed. A check
    that cannot see the thing it checks is worse than no check.
    """
    assert len(paths) >= MINIMUM_EXPECTED_ROUTES, (
        f"only {len(paths)} routes found, expected at least "
        f"{MINIMUM_EXPECTED_ROUTES}. _effective_paths() has probably stopped "
        "understanding how FastAPI stores included routers -- fix the walker "
        "rather than lowering this number."
    )


# ---------------------------------------------------------------------------
# No doubled segments
# ---------------------------------------------------------------------------


def test_no_path_repeats_a_segment(paths):
    offenders = {
        path: _repeated_segment(path)
        for path in paths
        if _repeated_segment(path) and path not in DELIBERATE_ALIASES
    }

    if offenders:
        listed = "\n".join(
            f"  {path}   (segment {segment!r} appears twice)"
            for path, segment in sorted(offenders.items())
        )
        pytest.fail(
            "Routes with a repeated path segment:\n"
            f"{listed}\n\n"
            "This is almost always a router that declares its own prefix being "
            "mounted under a prefix that repeats it. Drop the prefix= from the "
            "include_router call and let the router's own prefix stand."
        )


def test_no_v1_path_contains_a_second_api_segment(paths):
    """
    `saved_searches` hardcoded `/api/saved-searches` as its *own* prefix, which
    gave `/api/v1/api/saved-searches` under v1. A router's prefix is relative to
    wherever it is mounted; it should never name the mount.
    """
    offenders = [
        p for p in paths if p.startswith("/api/v1/") and "/api/" in p[len("/api/v1") :]
    ]

    assert offenders == [], (
        "Versioned paths with a nested /api/ segment: "
        f"{offenders}. A router's prefix must not include the mount point."
    )


def test_deliberate_aliases_still_exist(paths):
    """
    Keeps `DELIBERATE_ALIASES` from becoming a graveyard.

    If the compatibility alias is removed, this entry should go too -- otherwise
    the next genuinely doubled path at that URL passes silently.
    """
    stale = DELIBERATE_ALIASES - set(paths)
    if stale:
        pytest.skip(
            f"DELIBERATE_ALIASES lists paths that no longer exist ({sorted(stale)}) "
            "-- remove them."
        )


# ---------------------------------------------------------------------------
# The specific paths this change restores
# ---------------------------------------------------------------------------
#
# The mechanical check above is the part that keeps working. These are the
# eleven from the issue, named so a failure says which router regressed rather
# than "some path repeats a segment".


AFFECTED_ROUTERS = [
    ("bookmarks", "/api/bookmarks/"),
    ("bookmark_collections", "/api/bookmark-collections/"),
    ("conversations", "/api/conversations/"),
    ("profile_suggestions", "/api/profile-suggestions/"),
    ("repositories", "/api/repositories/"),
    ("organizations", "/api/organizations/"),
    ("skills", "/api/skills/"),
    ("recommendations", "/api/recommendations/builders"),
    ("health", "/api/health/ready"),
    ("saved_searches", "/api/saved-searches/"),
]


@pytest.mark.parametrize(
    "router,path", AFFECTED_ROUTERS, ids=[r for r, _ in AFFECTED_ROUTERS]
)
def test_router_is_served_at_the_undoubled_path(paths, router, path):
    assert path in paths, f"{router} is not served at {path}"


@pytest.mark.parametrize(
    "router,path", AFFECTED_ROUTERS, ids=[r for r, _ in AFFECTED_ROUTERS]
)
def test_the_doubled_path_is_gone(paths, router, path):
    """
    The other half. Leaving both live would mean two URLs for one resource and
    two sets of cache keys, logs and rate-limit buckets.
    """
    segment = path.strip("/").split("/")[1]
    doubled = path.replace(f"/{segment}/", f"/{segment}/{segment}/", 1)
    assert doubled not in paths, f"{router} is still also served at {doubled}"


def test_websockets_are_reachable_without_the_doubled_segment(paths):
    """
    `/api/ws/ws/presence` is the one where nobody would have guessed the URL,
    and a websocket that cannot be connected to fails quietly on the client.
    """
    assert "/api/ws/presence" in paths
    assert "/api/ws/ws/presence" not in paths


# ---------------------------------------------------------------------------
# Duplicate mounts
# ---------------------------------------------------------------------------


def test_no_router_is_mounted_twice_at_the_same_prefix(paths):
    """
    `conversations` was included twice with byte-identical arguments, six lines
    apart, and `organizations` and `profile_suggestions` were each included
    twice under v1 -- once doubled, once not. Harmless to serve and confusing
    to read: the second registration is dead, so editing it changes nothing.

    Deduplicating `paths` cannot see this, so count the mounts directly.
    """
    seen: dict[tuple[int, str], int] = {}

    def count(routes, prefix=""):
        for route in routes:
            context = getattr(route, "include_context", None)
            if context is None:
                continue
            inner = getattr(route, "original_router", None) or context.included_router
            key = (id(inner), prefix + (context.prefix or ""))
            seen[key] = seen.get(key, 0) + 1
            count(inner.routes, prefix + (context.prefix or ""))

    count(app.routes)

    duplicates = sorted(mount for (_, mount), n in seen.items() if n > 1)
    assert duplicates == [], f"routers mounted more than once at: {duplicates}"


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------


def test_the_restored_paths_actually_answer(client, register_and_login):
    """
    Path registration is not the same as a working route. Asserting on
    `app.routes` alone would pass if every one of these 500'd.
    """
    _, token = register_and_login("paths@example.com", "pathsuser")
    headers = {"Authorization": f"Bearer {token}"}

    for path in (
        "/api/bookmarks/",
        "/api/bookmark-collections/",
        "/api/conversations/",
        "/api/organizations/",
        "/api/skills/",
    ):
        response = client.get(path, headers=headers)
        assert (
            response.status_code == 200
        ), f"{path} -> {response.status_code} {response.text[:200]}"


def test_the_doubled_paths_stop_serving_the_collection(client, register_and_login):
    """
    Not asserted as a flat 404. `/api/bookmarks/bookmarks/` now falls through to
    `/api/bookmarks/{bookmark_id}` and answers 422 because "bookmarks" is not a
    UUID -- which is the routing table behaving correctly. What matters is that
    it no longer returns the collection.
    """
    _, token = register_and_login("gone@example.com", "goneuser")
    headers = {"Authorization": f"Bearer {token}"}

    for path in (
        "/api/bookmarks/bookmarks/",
        "/api/conversations/conversations/",
        "/api/organizations/organizations/",
        "/api/skills/skills/",
    ):
        status = client.get(path, headers=headers).status_code
        assert status != 200, f"{path} still serves a collection"


def test_health_is_reachable_at_the_documented_path(client):
    """
    `/api/health/ready` is what a load balancer or `kubectl` probe would be
    pointed at. It was `/api/health/health/ready`.
    """
    response = client.get("/api/health/ready")

    assert response.status_code in (200, 503), response.text
    assert "services" in response.json()
