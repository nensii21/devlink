"""
Idempotency for unsafe requests.

The contract
------------

A client that is about to make a request it cannot safely repeat sends an
``Idempotency-Key`` header. If it never hears back -- a timeout, a dropped
connection, a crashed tab -- it retries with the same key, and gets the
*original* response rather than a second execution.

What makes that safe is that the key is bound to the request. A stored
response is only replayed for a request that is byte-for-byte the same one
that produced it:

    key + method + path + body  ->  response

Previously only the key was in the cache key::

    cache_key = f"idempotent:{user_id}:{idempotency_key}"

so a client that reused a key across two genuinely different requests -- a
mobile app deriving the key from a screen-level UUID, or anything retrying a
batch under one key -- got the first response replayed for the second, and the
second request never ran. Silent data loss, and the shape of client that hits
it is exactly the shape of client that needs idempotency in the first place.

Requests whose fingerprint disagrees with the stored one now get ``422``. That
is what Stripe and the IETF ``Idempotency-Key`` draft both do, and a loud
rejection is much easier to debug than a wrong response body.

Failure posture
---------------

This layer is an optimisation on top of a correct API, so it fails *open*
everywhere it can:

* Redis unreachable at startup or mid-request -> the request runs normally.
* A cache *write* fails after the handler committed -> logged, swallowed. The
  work already happened; turning that into a 500 would make the client retry
  an operation that succeeded.

The one place it fails closed is the concurrency lock: if another request is
already in flight under this key, the duplicate gets ``409`` with a
``Retry-After`` rather than being allowed to run alongside it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any, Callable, Optional

import redis.asyncio as aioredis
from fastapi import Request, Response
from fastapi.routing import APIRoute

from app.core.config import settings
from app.core.security import InvalidTokenType, TokenType, decode_token

logger = logging.getLogger(__name__)

#: Methods that can carry an idempotency key. GET/HEAD/OPTIONS are already
#: safe and DELETE is already idempotent by definition.
IDEMPOTENT_METHODS = frozenset({"POST", "PUT", "PATCH"})

#: How long a stored response is replayable.
RESPONSE_TTL_SECONDS = 24 * 60 * 60

#: How long the in-flight lock lives. Sized above the request timeout: if the
#: lock expires while the handler is still running, a retry proceeds
#: concurrently and produces the duplicate this middleware exists to prevent.
LOCK_TTL_SECONDS = 120

#: What a duplicate-in-flight response tells the client to wait.
RETRY_AFTER_SECONDS = 2

#: Response headers worth replaying. Everything else -- `Date`, `Server`,
#: `Content-Length`, and in particular any `Set-Cookie` -- describes the
#: original exchange, not the payload, and replaying a day-old `Set-Cookie` is
#: not something a cache should do. `Content-Length` is recomputed by Starlette
#: from the body we hand it.
REPLAYABLE_HEADERS = frozenset(
    {
        "content-type",
        "content-language",
        "location",
        "etag",
        "cache-control",
    }
)

#: Marks a replayed response, so a client (or a test) can tell the difference.
CACHE_STATUS_HEADER = "X-Idempotent-Replay"

#: Set when a handler's response could not be stored, so the caller knows a
#: retry with the same key will re-execute rather than replay.
NOT_STORED_HEADER = "X-Idempotent-Stored"


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------
#
# The client is created lazily rather than at import. Building it at import
# time means a Redis that is merely slow to start takes the whole application
# down with it, and it makes the module impossible to import in a test that
# does not care about idempotency at all.

_redis_client: Optional[aioredis.Redis] = None
_redis_unavailable = False


async def get_redis() -> Optional[aioredis.Redis]:
    """The shared async Redis client, or ``None`` if Redis is not reachable.

    ``None`` is a normal answer, not an error: every caller treats it as
    "skip idempotency and run the request".
    """
    global _redis_client, _redis_unavailable

    if _redis_unavailable:
        return None

    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        except Exception as exc:  # pragma: no cover - configuration error
            logger.error("Idempotency: could not create Redis client: %s", exc)
            _redis_unavailable = True
            return None

    return _redis_client


async def reset_redis_client() -> None:
    """Drop the cached client. For tests, and for a clean shutdown."""
    global _redis_client, _redis_unavailable

    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:  # pragma: no cover - best effort
            logger.debug("Idempotency: error closing Redis client", exc_info=True)

    _redis_client = None
    _redis_unavailable = False


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def extract_user_id(request: Request) -> Optional[str]:
    """The authenticated subject, or ``None``.

    Two things this does that the previous version did not.

    It **verifies the token type**. `jwt.decode` on its own checks the
    signature and the expiry but nothing else, so a refresh, verification or
    password-reset token was accepted as identity here. ``decode_token`` with
    an expected type folds all three checks into one pass.

    It returns ``None`` rather than the string ``"anonymous"``. Every
    unauthenticated caller previously shared the ``idempotent:anonymous:<key>``
    namespace, so one anonymous client could read another's cached response
    body by reusing a guessable key. There is no safe way to scope a cache
    entry to an unidentified caller, so unauthenticated requests skip
    idempotency entirely.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    try:
        payload = decode_token(
            auth_header[7:],
            expected_type=TokenType.ACCESS,
        )
    except (InvalidTokenType, ValueError):
        return None

    subject = payload.get("sub")

    return str(subject) if subject else None


# ---------------------------------------------------------------------------
# Keys and fingerprints
# ---------------------------------------------------------------------------


def build_cache_key(user_id: str, method: str, path: str, key: str) -> str:
    """The Redis key for one (caller, endpoint, idempotency key) triple.

    The method and path are in the key rather than only in the fingerprint so
    that the same key used against two different endpoints does not even
    collide -- both requests run, which is what the client meant, instead of
    one being rejected with a fingerprint mismatch.

    Hashed because an idempotency key is client-supplied and a path can be
    long; this keeps every Redis key the same bounded size.
    """
    digest = hashlib.sha256(
        "\x00".join((method.upper(), path, key)).encode("utf-8")
    ).hexdigest()

    return f"idempotent:v2:{user_id}:{digest}"


def build_fingerprint(method: str, path: str, body: bytes) -> str:
    """A digest of everything about the request that must not change.

    Compared against the stored fingerprint on a cache hit. A mismatch means
    the client reused a key for a different request, which is a client error
    rather than something to paper over.

    Headers are deliberately out of scope: a retry legitimately carries a
    different `User-Agent`, trace id or `Authorization` (a refreshed token),
    and rejecting on those would make idempotency unusable.
    """
    hasher = hashlib.sha256()
    hasher.update(method.upper().encode("utf-8"))
    hasher.update(b"\x00")
    hasher.update(path.encode("utf-8"))
    hasher.update(b"\x00")
    hasher.update(body)

    return hasher.hexdigest()


def filter_headers(headers: Any) -> dict[str, str]:
    """Keep only the response headers that describe the payload."""
    return {
        name: value
        for name, value in headers.items()
        if name.lower() in REPLAYABLE_HEADERS
    }


# ---------------------------------------------------------------------------
# Stored payloads
# ---------------------------------------------------------------------------


def serialise_response(
    response: Response,
    body: bytes,
    fingerprint: str,
) -> str:
    """Encode a response for storage."""
    return json.dumps(
        {
            "fingerprint": fingerprint,
            "status_code": response.status_code,
            "headers": filter_headers(response.headers),
            "body": body.decode("utf-8", errors="replace"),
            "media_type": getattr(response, "media_type", None)
            or response.headers.get("content-type")
            or "application/json",
        }
    )


def build_replay(stored: dict) -> Response:
    """Rebuild a stored response for replay."""
    headers = dict(stored.get("headers") or {})
    headers[CACHE_STATUS_HEADER] = "true"

    return Response(
        content=stored.get("body", ""),
        status_code=stored.get("status_code", 200),
        headers=headers,
        media_type=stored.get("media_type") or "application/json",
    )


def build_conflict_response(message: str, status_code: int) -> Response:
    """A JSON error response that does not depend on the app's handlers."""
    return Response(
        content=json.dumps({"success": False, "message": message}),
        status_code=status_code,
        media_type="application/json",
    )


def build_mismatch_response(path: str) -> Response:
    """422 for a key reused against a different request body."""
    return build_conflict_response(
        "This Idempotency-Key was already used for a different request to "
        f"{path}. Use a new key for a new request, or resend the original "
        "request unchanged to replay its response.",
        422,
    )


def build_in_progress_response() -> Response:
    """409 for a duplicate that arrived while the original is still running."""
    response = build_conflict_response(
        "A request with this Idempotency-Key is already in progress.",
        409,
    )
    # Without this the client has nothing to back off against and will hammer.
    response.headers["Retry-After"] = str(RETRY_AFTER_SECONDS)

    return response


# ---------------------------------------------------------------------------
# The route class
# ---------------------------------------------------------------------------


class IdempotentRoute(APIRoute):
    """An ``APIRoute`` that honours ``Idempotency-Key`` on unsafe methods.

    Attach with ``APIRouter(route_class=IdempotentRoute)``. Requests without
    the header are unaffected, so this is safe to put on a whole router.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            idempotency_key = request.headers.get("Idempotency-Key")

            if not idempotency_key or request.method not in IDEMPOTENT_METHODS:
                return await original_route_handler(request)

            user_id = extract_user_id(request)
            if user_id is None:
                # No identity to scope the entry to. See `extract_user_id`.
                return await original_route_handler(request)

            client = await get_redis()
            if client is None:
                logger.warning("Idempotency: Redis unavailable, bypassing.")
                return await original_route_handler(request)

            path = request.url.path

            # Reading the body here is safe: Starlette caches it on the
            # request, so the handler downstream still receives it.
            body = await request.body()

            cache_key = build_cache_key(user_id, request.method, path, idempotency_key)
            fingerprint = build_fingerprint(request.method, path, body)

            # ---- Replay, if we have one ------------------------------------

            try:
                cached = await client.get(cache_key)
            except Exception as exc:
                logger.error("Idempotency: read failed for %s: %s", cache_key, exc)
                return await original_route_handler(request)

            if cached:
                try:
                    stored = json.loads(cached)
                except (TypeError, ValueError):
                    # A corrupt entry should not wedge the endpoint forever.
                    logger.error("Idempotency: corrupt entry at %s", cache_key)
                    stored = None

                if stored is not None:
                    if stored.get("fingerprint") != fingerprint:
                        return build_mismatch_response(path)

                    return build_replay(stored)

            # ---- Claim the key ---------------------------------------------
            #
            # One command, so there is no window in which the key exists
            # without a TTL. `SETNX` followed by `EXPIRE` is two round trips,
            # and a process killed between them left a lock that never expired
            # -- that idempotency key then answered 409 forever, recoverable
            # only by deleting it in Redis by hand.
            #
            # The value is a token unique to this attempt so that the release
            # below can check it still owns the lock. Without that, a handler
            # that overran the TTL would delete a lock a *different* request
            # had since acquired.

            lock_key = f"{cache_key}:lock"
            lock_token = uuid.uuid4().hex

            try:
                acquired = await client.set(
                    lock_key,
                    lock_token,
                    nx=True,
                    ex=LOCK_TTL_SECONDS,
                )
            except Exception as exc:
                logger.error("Idempotency: lock failed for %s: %s", lock_key, exc)
                return await original_route_handler(request)

            if not acquired:
                return build_in_progress_response()

            # ---- Run, then store -------------------------------------------

            try:
                response = await original_route_handler(request)

                body_bytes = getattr(response, "body", None)

                if not isinstance(body_bytes, (bytes, bytearray)):
                    # A StreamingResponse or FileResponse has no materialised
                    # body. Consuming its iterator to cache it would break
                    # streaming, so these are passed through unstored and the
                    # response says so rather than leaving the client to
                    # assume a retry will replay.
                    response.headers[NOT_STORED_HEADER] = "false"
                    return response

                if response.status_code >= 500:
                    # A server error is not an outcome worth making permanent
                    # for 24 hours; the retry should get a real attempt.
                    response.headers[NOT_STORED_HEADER] = "false"
                    return response

                try:
                    await client.setex(
                        cache_key,
                        RESPONSE_TTL_SECONDS,
                        serialise_response(response, bytes(body_bytes), fingerprint),
                    )
                    response.headers[NOT_STORED_HEADER] = "true"
                except Exception as exc:
                    # The handler already committed its work. Surfacing this
                    # as a 500 would tell the client an operation failed when
                    # it succeeded, and invite a retry of it.
                    logger.error(
                        "Idempotency: could not store response for %s: %s",
                        cache_key,
                        exc,
                    )
                    response.headers[NOT_STORED_HEADER] = "false"

                return response

            finally:
                await release_lock(client, lock_key, lock_token)

        return custom_route_handler


#: Release the lock only if we still hold it. Compare-and-delete has to be
#: atomic, or the check and the delete can straddle another request's
#: acquisition.
_RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


async def release_lock(client: aioredis.Redis, lock_key: str, token: str) -> None:
    """Drop our in-flight lock, tolerating any Redis failure."""
    try:
        await client.eval(_RELEASE_LOCK_SCRIPT, 1, lock_key, token)
    except Exception as exc:
        # The lock has a TTL, so the worst case is that this key rejects
        # duplicates for a couple of minutes longer than necessary.
        logger.warning("Idempotency: could not release %s: %s", lock_key, exc)
