"""
Tests for ``app.middleware.idempotency``.

Everything here runs against an in-process fake Redis rather than a real
server, so the suite has no external dependency and can exercise the awkward
cases directly -- a lock that is already held, a read that raises, a write that
raises, a corrupt stored entry.

The fake implements only what the middleware uses (``get``, ``set`` with
``nx``/``ex``, ``setex``, ``eval`` of the release script, ``delete``) and
implements it with the same semantics, including ``SET NX`` returning ``None``
when the key exists.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import pytest
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    _create_token,
)
from app.middleware import idempotency
from app.middleware.idempotency import (
    CACHE_STATUS_HEADER,
    LOCK_TTL_SECONDS,
    NOT_STORED_HEADER,
    RESPONSE_TTL_SECONDS,
    IdempotentRoute,
    build_cache_key,
    build_fingerprint,
    extract_user_id,
    filter_headers,
)

# ---------------------------------------------------------------------------
# Fake Redis
# ---------------------------------------------------------------------------


class FakeRedis:
    """Enough of the async Redis surface for this middleware."""

    def __init__(self) -> None:
        self.store: dict[str, tuple[str, Optional[float]]] = {}
        self.fail_on_get = False
        self.fail_on_set = False
        self.fail_on_setex = False
        self.set_calls: list[dict[str, Any]] = []

    # -- internals ----------------------------------------------------------

    def _live(self, key: str) -> Optional[str]:
        entry = self.store.get(key)
        if entry is None:
            return None

        value, expires_at = entry
        if expires_at is not None and expires_at <= time.monotonic():
            del self.store[key]
            return None

        return value

    def ttl_of(self, key: str) -> Optional[float]:
        entry = self.store.get(key)
        if entry is None or entry[1] is None:
            return None
        return entry[1] - time.monotonic()

    def seed(self, key: str, value: str) -> None:
        self.store[key] = (value, None)

    # -- the surface the middleware uses ------------------------------------

    async def get(self, key: str) -> Optional[str]:
        if self.fail_on_get:
            raise ConnectionError("boom")
        return self._live(key)

    async def set(
        self,
        key: str,
        value: str,
        nx: bool = False,
        ex: Optional[int] = None,
    ) -> Optional[bool]:
        if self.fail_on_set:
            raise ConnectionError("boom")

        self.set_calls.append({"key": key, "nx": nx, "ex": ex})

        if nx and self._live(key) is not None:
            # Real Redis returns None, not False, when NX declines.
            return None

        self.store[key] = (value, time.monotonic() + ex if ex else None)
        return True

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        if self.fail_on_setex:
            raise ConnectionError("boom")
        self.store[key] = (value, time.monotonic() + seconds)
        return True

    async def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0

    async def eval(self, script: str, numkeys: int, *args: str) -> int:
        """Only the compare-and-delete release script is ever evaluated."""
        key, token = args[0], args[1]
        if self._live(key) == token:
            del self.store[key]
            return 1
        return 0

    async def aclose(self) -> None:
        return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    client = FakeRedis()

    async def _get_redis():
        return client

    monkeypatch.setattr(idempotency, "get_redis", _get_redis)
    return client


@pytest.fixture()
def token() -> str:
    return create_access_token("11111111-1111-1111-1111-111111111111")


@pytest.fixture()
def other_token() -> str:
    return create_access_token("22222222-2222-2222-2222-222222222222")


@pytest.fixture()
def app_and_counter():
    """An app whose POST handler counts how many times it actually ran."""
    calls = {"count": 0, "bodies": []}

    router = APIRouter(route_class=IdempotentRoute)

    @router.post("/things")
    async def create_thing(request: Request):
        calls["count"] += 1
        body = await request.body()
        calls["bodies"].append(body)
        return {"id": calls["count"], "echo": body.decode() or None}

    @router.post("/others")
    async def create_other():
        calls["count"] += 1
        return {"where": "others"}

    @router.post("/boom")
    async def boom():
        calls["count"] += 1
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": "nope"}, status_code=500)

    @router.post("/rejected")
    async def rejected():
        calls["count"] += 1
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": "bad input"}, status_code=422)

    @router.post("/stream")
    async def stream():
        calls["count"] += 1

        def chunks():
            yield b"a"
            yield b"b"

        return StreamingResponse(chunks(), media_type="text/plain")

    @router.get("/things")
    async def list_things():
        calls["count"] += 1
        return {"ok": True}

    app = FastAPI()
    app.include_router(router)

    return app, calls


@pytest.fixture()
def client(app_and_counter):
    app, _ = app_and_counter
    return TestClient(app)


@pytest.fixture()
def calls(app_and_counter):
    _, calls = app_and_counter
    return calls


def auth(token: str, key: Optional[str] = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key:
        headers["Idempotency-Key"] = key
    return headers


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def _request_with_auth(header_value: Optional[str]) -> Request:
    headers = []
    if header_value is not None:
        headers.append((b"authorization", header_value.encode()))

    return Request({"type": "http", "headers": headers, "method": "POST", "path": "/"})


def test_extract_user_id_reads_an_access_token(token: str) -> None:
    assert extract_user_id(_request_with_auth(f"Bearer {token}")) == (
        "11111111-1111-1111-1111-111111111111"
    )


def test_extract_user_id_rejects_a_refresh_token() -> None:
    """A refresh token is a valid signature but the wrong kind of token.

    The previous implementation called `jwt.decode` directly, which checks the
    signature and the expiry and nothing else, so any token this service ever
    minted authenticated here.
    """
    refresh = create_refresh_token("11111111-1111-1111-1111-111111111111")
    assert extract_user_id(_request_with_auth(f"Bearer {refresh}")) is None


def test_extract_user_id_rejects_a_password_reset_token() -> None:
    from datetime import timedelta

    reset = _create_token(
        subject="11111111-1111-1111-1111-111111111111",
        expires_delta=timedelta(minutes=10),
        token_type=TokenType.RESET_PASSWORD,
    )
    assert extract_user_id(_request_with_auth(f"Bearer {reset}")) is None


@pytest.mark.parametrize(
    "header",
    [None, "", "Basic abc", "Bearer ", "Bearer not-a-jwt", "bearer lowercase"],
)
def test_extract_user_id_returns_none_without_a_usable_token(header) -> None:
    assert extract_user_id(_request_with_auth(header)) is None


# ---------------------------------------------------------------------------
# Keys and fingerprints
# ---------------------------------------------------------------------------


def test_cache_key_separates_endpoints() -> None:
    """The same key against two paths must not collide."""
    a = build_cache_key("u1", "POST", "/api/projects", "k")
    b = build_cache_key("u1", "POST", "/api/applications", "k")
    assert a != b


def test_cache_key_separates_methods() -> None:
    a = build_cache_key("u1", "POST", "/api/projects", "k")
    b = build_cache_key("u1", "PUT", "/api/projects", "k")
    assert a != b


def test_cache_key_separates_callers() -> None:
    a = build_cache_key("u1", "POST", "/api/projects", "k")
    b = build_cache_key("u2", "POST", "/api/projects", "k")
    assert a != b


def test_cache_key_is_bounded_and_stable() -> None:
    """Long client-supplied keys must not produce unbounded Redis keys."""
    key = build_cache_key("u1", "POST", "/api/projects", "x" * 5000)
    assert len(key) < 128
    assert key == build_cache_key("u1", "POST", "/api/projects", "x" * 5000)


def test_fingerprint_changes_with_the_body() -> None:
    a = build_fingerprint("POST", "/p", b'{"n": 1}')
    b = build_fingerprint("POST", "/p", b'{"n": 2}')
    assert a != b


def test_fingerprint_is_stable_for_an_identical_request() -> None:
    a = build_fingerprint("POST", "/p", b'{"n": 1}')
    b = build_fingerprint("POST", "/p", b'{"n": 1}')
    assert a == b


def test_filter_headers_drops_set_cookie_and_transport_headers() -> None:
    from starlette.datastructures import Headers

    kept = filter_headers(
        Headers(
            {
                "content-type": "application/json",
                "etag": '"abc"',
                "set-cookie": "session=secret",
                "date": "Sat, 16 Aug 2026 00:00:00 GMT",
                "content-length": "42",
                "server": "uvicorn",
            }
        )
    )

    assert kept == {"content-type": "application/json", "etag": '"abc"'}


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def test_a_repeated_request_runs_once(client, calls, fake_redis, token) -> None:
    first = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))
    second = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert calls["count"] == 1


def test_a_replay_is_labelled(client, fake_redis, token) -> None:
    client.post("/things", json={"n": 1}, headers=auth(token, "k1"))
    replayed = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert replayed.headers[CACHE_STATUS_HEADER] == "true"


def test_the_first_response_is_not_labelled_as_a_replay(
    client, fake_redis, token
) -> None:
    first = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))
    assert CACHE_STATUS_HEADER not in first.headers
    assert first.headers[NOT_STORED_HEADER] == "true"


def test_requests_without_a_key_are_never_deduplicated(
    client, calls, fake_redis, token
) -> None:
    client.post("/things", json={"n": 1}, headers=auth(token))
    client.post("/things", json={"n": 1}, headers=auth(token))

    assert calls["count"] == 2
    assert fake_redis.store == {}


def test_get_requests_are_untouched(client, calls, fake_redis, token) -> None:
    client.get("/things", headers=auth(token, "k1"))
    client.get("/things", headers=auth(token, "k1"))

    assert calls["count"] == 2


def test_the_handler_still_receives_the_body(client, calls, fake_redis, token) -> None:
    """The middleware reads the body to fingerprint it; the handler must
    still get it. Starlette caches it on the request, but that is exactly the
    kind of thing that quietly stops being true."""
    client.post("/things", json={"n": 7}, headers=auth(token, "k1"))

    assert len(calls["bodies"]) == 1
    assert json.loads(calls["bodies"][0]) == {"n": 7}


# ---------------------------------------------------------------------------
# Request binding -- the bug this rewrite is about
# ---------------------------------------------------------------------------


def test_reusing_a_key_with_a_different_body_is_rejected(
    client, calls, fake_redis, token
) -> None:
    """The original defect: this used to replay the first response."""
    first = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))
    second = client.post("/things", json={"n": 2}, headers=auth(token, "k1"))

    assert first.status_code == 200
    assert second.status_code == 422
    assert "different request" in second.json()["message"]

    # The second request was rejected, not silently answered with the first
    # request's response, and it did not execute.
    assert calls["count"] == 1


def test_a_key_reused_against_a_different_endpoint_runs(
    client, calls, fake_redis, token
) -> None:
    """Different endpoints do not collide, so both requests execute.

    Previously the second call got the first endpoint's response body.
    """
    first = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))
    second = client.post("/others", headers=auth(token, "k1"))

    assert json.loads(first.json()["echo"]) == {"n": 1}
    assert second.json() == {"where": "others"}
    assert calls["count"] == 2


def test_two_users_with_the_same_key_do_not_share_a_response(
    client, calls, fake_redis, token, other_token
) -> None:
    first = client.post("/things", json={"n": 1}, headers=auth(token, "shared"))
    second = client.post("/things", json={"n": 1}, headers=auth(other_token, "shared"))

    assert calls["count"] == 2
    assert first.json()["id"] != second.json()["id"]


def test_unauthenticated_requests_bypass_idempotency(client, calls, fake_redis) -> None:
    """No identity means no safe way to scope the entry, so no caching.

    The old code bucketed every anonymous caller under the literal string
    "anonymous", so one could read another's cached response.
    """
    client.post("/things", json={"n": 1}, headers={"Idempotency-Key": "k1"})
    client.post("/things", json={"n": 1}, headers={"Idempotency-Key": "k1"})

    assert calls["count"] == 2
    assert fake_redis.store == {}


def test_a_refresh_token_does_not_authenticate_the_cache_entry(
    client, calls, fake_redis
) -> None:
    refresh = create_refresh_token("11111111-1111-1111-1111-111111111111")

    client.post("/things", json={"n": 1}, headers=auth(refresh, "k1"))
    client.post("/things", json={"n": 1}, headers=auth(refresh, "k1"))

    assert calls["count"] == 2
    assert fake_redis.store == {}


# ---------------------------------------------------------------------------
# The lock
# ---------------------------------------------------------------------------


def test_the_lock_is_acquired_atomically_with_its_ttl(
    client, fake_redis, token
) -> None:
    """`SET NX EX` in one command.

    `SETNX` followed by a separate `EXPIRE` left the key without a TTL if the
    process died in between, and that key then answered 409 forever.
    """
    client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    lock_sets = [c for c in fake_redis.set_calls if c["key"].endswith(":lock")]
    assert len(lock_sets) == 1
    assert lock_sets[0]["nx"] is True
    assert lock_sets[0]["ex"] == LOCK_TTL_SECONDS


def test_a_duplicate_in_flight_gets_409_with_retry_after(
    client, calls, fake_redis, token
) -> None:
    cache_key = build_cache_key(
        "11111111-1111-1111-1111-111111111111", "POST", "/things", "k1"
    )
    fake_redis.store[f"{cache_key}:lock"] = ("someone-else", None)

    response = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert response.status_code == 409
    assert response.headers["Retry-After"] == "2"
    assert calls["count"] == 0


def test_the_lock_is_released_after_a_successful_request(
    client, fake_redis, token
) -> None:
    client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert not [k for k in fake_redis.store if k.endswith(":lock")]


def test_the_lock_is_released_when_the_handler_raises(fake_redis, token) -> None:
    router = APIRouter(route_class=IdempotentRoute)

    @router.post("/explode")
    async def explode():
        raise RuntimeError("handler blew up")

    app = FastAPI()
    app.include_router(router)

    with pytest.raises(RuntimeError):
        TestClient(app, raise_server_exceptions=True).post(
            "/explode", headers=auth(token, "k1")
        )

    assert not [k for k in fake_redis.store if k.endswith(":lock")]


def test_releasing_only_removes_our_own_lock(fake_redis) -> None:
    """A handler that overran the TTL must not delete a successor's lock."""
    import asyncio

    from app.middleware.idempotency import release_lock

    fake_redis.store["k:lock"] = ("someone-elses-token", None)

    asyncio.run(release_lock(fake_redis, "k:lock", "our-token"))

    assert fake_redis.store["k:lock"] == ("someone-elses-token", None)


def test_releasing_removes_a_lock_we_hold(fake_redis) -> None:
    import asyncio

    from app.middleware.idempotency import release_lock

    fake_redis.store["k:lock"] = ("our-token", None)

    asyncio.run(release_lock(fake_redis, "k:lock", "our-token"))

    assert "k:lock" not in fake_redis.store


def test_a_second_request_succeeds_after_the_first_completes(
    client, calls, fake_redis, token
) -> None:
    """The lock must not outlive the request that took it."""
    client.post("/things", json={"n": 1}, headers=auth(token, "k1"))
    second = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert second.status_code == 200
    assert calls["count"] == 1


# ---------------------------------------------------------------------------
# What gets stored
# ---------------------------------------------------------------------------


def test_a_stored_entry_carries_the_fingerprint_and_a_ttl(
    client, calls, fake_redis, token
) -> None:
    client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    cache_key = build_cache_key(
        "11111111-1111-1111-1111-111111111111", "POST", "/things", "k1"
    )
    stored = json.loads(fake_redis.store[cache_key][0])

    # Fingerprinted over the bytes the handler actually saw, rather than a
    # re-serialisation of the same object -- the client's encoding is not
    # ours to guess.
    assert stored["fingerprint"] == build_fingerprint(
        "POST", "/things", calls["bodies"][0]
    )
    assert stored["status_code"] == 200

    ttl = fake_redis.ttl_of(cache_key)
    assert ttl is not None and 0 < ttl <= RESPONSE_TTL_SECONDS


def test_a_client_error_is_stored_and_replayed(
    client, calls, fake_redis, token
) -> None:
    """A rejection is a real outcome; replaying it keeps the retry consistent."""
    first = client.post("/rejected", headers=auth(token, "k1"))
    second = client.post("/rejected", headers=auth(token, "k1"))

    assert first.status_code == 422
    assert second.status_code == 422
    assert second.headers[CACHE_STATUS_HEADER] == "true"
    assert calls["count"] == 1


def test_a_server_error_is_not_stored(client, calls, fake_redis, token) -> None:
    """A 500 should not be made permanent for 24 hours."""
    first = client.post("/boom", headers=auth(token, "k1"))
    second = client.post("/boom", headers=auth(token, "k1"))

    assert first.status_code == 500
    assert first.headers[NOT_STORED_HEADER] == "false"
    assert second.status_code == 500
    assert calls["count"] == 2


def test_a_streaming_response_is_passed_through_unstored(
    client, calls, fake_redis, token
) -> None:
    """Consuming the iterator to cache it would break streaming."""
    first = client.post("/stream", headers=auth(token, "k1"))

    assert first.status_code == 200
    assert first.text == "ab"
    assert first.headers[NOT_STORED_HEADER] == "false"

    second = client.post("/stream", headers=auth(token, "k1"))
    assert second.text == "ab"
    assert calls["count"] == 2


def test_set_cookie_is_not_replayed(fake_redis, token) -> None:
    router = APIRouter(route_class=IdempotentRoute)

    @router.post("/login-ish")
    async def login_ish():
        from fastapi.responses import JSONResponse

        response = JSONResponse({"ok": True})
        response.set_cookie("session", "supersecret")
        return response

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    first = client.post("/login-ish", headers=auth(token, "k1"))
    assert "set-cookie" in {k.lower() for k in first.headers}

    second = client.post("/login-ish", headers=auth(token, "k1"))
    assert second.headers[CACHE_STATUS_HEADER] == "true"
    assert "set-cookie" not in {k.lower() for k in second.headers}


# ---------------------------------------------------------------------------
# Failure posture
# ---------------------------------------------------------------------------


def test_redis_unavailable_bypasses_cleanly(client, calls, monkeypatch, token) -> None:
    async def _no_redis():
        return None

    monkeypatch.setattr(idempotency, "get_redis", _no_redis)

    first = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))
    second = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["count"] == 2


def test_a_failing_read_bypasses_rather_than_500s(
    client, calls, fake_redis, token
) -> None:
    fake_redis.fail_on_get = True

    response = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert response.status_code == 200
    assert calls["count"] == 1


def test_a_failing_lock_bypasses_rather_than_500s(
    client, calls, fake_redis, token
) -> None:
    fake_redis.fail_on_set = True

    response = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert response.status_code == 200
    assert calls["count"] == 1


def test_a_failing_write_does_not_turn_a_success_into_a_500(
    client, calls, fake_redis, token
) -> None:
    """The handler already committed. A cache failure must not tell the
    client the operation failed and invite them to retry it."""
    fake_redis.fail_on_setex = True

    response = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.headers[NOT_STORED_HEADER] == "false"
    assert calls["count"] == 1


def test_a_corrupt_stored_entry_does_not_wedge_the_endpoint(
    client, calls, fake_redis, token
) -> None:
    cache_key = build_cache_key(
        "11111111-1111-1111-1111-111111111111", "POST", "/things", "k1"
    )
    fake_redis.seed(cache_key, "{not json")

    response = client.post("/things", json={"n": 1}, headers=auth(token, "k1"))

    assert response.status_code == 200
    assert calls["count"] == 1
