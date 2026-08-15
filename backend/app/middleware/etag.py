"""
ETag / conditional request middleware.

Adds an ``ETag`` to safe, successful JSON responses and turns a matching
``If-None-Match`` into a ``304 Not Modified``. The saving is bandwidth and
client-side deserialisation, not database work -- see ``app/core/cache.py`` for
the response cache that avoids the query itself.

Written as raw ASGI rather than ``BaseHTTPMiddleware`` on purpose: we need to
buffer the body to hash it, and we want to bail out and stream straight through
once a response grows past a threshold. ``BaseHTTPMiddleware`` gives us the body
only as an already-committed async iterator, which makes that impossible.
"""

import logging
from typing import Any, Dict, List, MutableMapping, Optional

from app.core.config import settings
from app.core.http_cache import (
    etag_matches,
    generate_etag,
    is_etaggable_content_type,
    merge_vary,
    parse_if_none_match,
)

logger = logging.getLogger(__name__)

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]

# Only safe methods get a validator. HEAD is included because clients use it to
# cheaply revalidate, but a HEAD response has no body to hash, so it is dropped
# later if nothing was buffered.
CACHEABLE_METHODS = frozenset({"GET", "HEAD"})

# Headers that must not survive into a 304. RFC 9110 section 15.4.5 allows only
# metadata that would have been sent with a 200, and a payload-describing header
# on an empty body confuses proxies.
_STRIPPED_ON_304 = frozenset(
    {
        b"content-length",
        b"content-type",
        b"content-encoding",
        b"content-language",
        b"transfer-encoding",
    }
)


def _get_header(headers: List[tuple], name: bytes) -> Optional[str]:
    """Look up a single header value from a raw ASGI header list."""
    for key, value in headers:
        if key.lower() == name:
            return value.decode("latin-1")
    return None


def _set_header(headers: List[tuple], name: bytes, value: str) -> None:
    """Replace (or append) a header in a raw ASGI header list, in place."""
    encoded = value.encode("latin-1")
    for index, (key, _) in enumerate(headers):
        if key.lower() == name:
            headers[index] = (key, encoded)
            return
    headers.append((name, encoded))


class ETagMiddleware:
    """
    Emit entity tags and answer conditional requests.

    Parameters mirror the ``ETAG_*`` settings so the middleware stays testable
    without monkeypatching global config.
    """

    def __init__(
        self,
        app,
        max_body_size: Optional[int] = None,
        cache_control: Optional[str] = None,
    ) -> None:
        self.app = app
        self.max_body_size = (
            max_body_size if max_body_size is not None else settings.ETAG_MAX_BODY_SIZE
        )
        self.cache_control = (
            cache_control if cache_control is not None else settings.ETAG_CACHE_CONTROL
        )

    async def __call__(self, scope: Scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not settings.ENABLE_ETAG or scope["method"] not in CACHEABLE_METHODS:
            await self.app(scope, receive, send)
            return

        client_tags = parse_if_none_match(
            _get_header(scope.get("headers", []), b"if-none-match")
        )

        # Mutable state shared with the send wrapper below. A dict keeps it
        # simple; a closure over locals would need `nonlocal` for each field.
        state: Dict[str, Any] = {
            "start": None,
            "chunks": [],
            "size": 0,
            "buffering": True,
        }

        async def send_wrapper(message: Message) -> None:
            message_type = message["type"]

            if message_type == "http.response.start":
                if self._should_skip(message):
                    state["buffering"] = False
                    await send(message)
                    return
                # Hold the start message back: we cannot commit headers until
                # we know whether this turns into a 304.
                state["start"] = message
                return

            if message_type != "http.response.body" or not state["buffering"]:
                await send(message)
                return

            body = message.get("body", b"")
            state["size"] += len(body)

            if state["size"] > self.max_body_size:
                # Too big to be worth buffering. Release what we have and let
                # the rest stream through untouched.
                await self._flush_unmodified(state, send, message)
                return

            state["chunks"].append(body)

            if message.get("more_body", False):
                return

            await self._complete(state, client_tags, scope, send)

        await self.app(scope, receive, send_wrapper)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _should_skip(self, start_message: Message) -> bool:
        """
        Decide up-front whether a response is a candidate for tagging.

        Anything that is not a plain successful JSON-ish body is passed
        through: errors, redirects, downloads, and handlers that already
        manage their own validator.
        """
        if start_message["status"] != 200:
            return True

        headers = start_message.get("headers", [])

        if _get_header(headers, b"etag") is not None:
            return True

        # A handler that opted out explicitly, or a Set-Cookie response that
        # should never be revalidated from a shared copy.
        cache_control = (_get_header(headers, b"cache-control") or "").lower()
        if "no-store" in cache_control:
            return True

        if not is_etaggable_content_type(_get_header(headers, b"content-type")):
            return True

        # Already-encoded payloads would need to be tagged per encoding; not
        # worth the complexity while compression is handled at the edge.
        if _get_header(headers, b"content-encoding") is not None:
            return True

        return False

    async def _flush_unmodified(
        self, state: Dict[str, Any], send, message: Message
    ) -> None:
        """Give up on buffering and emit everything collected so far."""
        if state["start"] is not None:
            await send(state["start"])
            state["start"] = None

        for chunk in state["chunks"]:
            await send({"type": "http.response.body", "body": chunk, "more_body": True})

        state["chunks"] = []
        state["buffering"] = False
        await send(message)

    async def _complete(
        self,
        state: Dict[str, Any],
        client_tags: List[str],
        scope: Scope,
        send,
    ) -> None:
        """Body is fully buffered: tag it, or answer 304."""
        start_message = state["start"]
        if start_message is None:
            # Defensive: a body without a start message is a protocol error we
            # should not paper over.
            logger.warning("ETag middleware saw a response body with no start")
            return

        body = b"".join(state["chunks"])
        headers: List[tuple] = list(start_message.get("headers", []))

        # HEAD responses carry no body; hashing b"" would hand every HEAD the
        # same validator, which is worse than having none.
        if not body:
            await send({**start_message, "headers": headers})
            await send({"type": "http.response.body", "body": b""})
            return

        etag = generate_etag(body)

        _set_header(headers, b"etag", etag)
        if _get_header(headers, b"cache-control") is None:
            _set_header(headers, b"cache-control", self.cache_control)
        # Responses are user-scoped, so a shared cache must key on the caller.
        _set_header(
            headers,
            b"vary",
            merge_vary(_get_header(headers, b"vary"), ["Authorization"]),
        )

        if client_tags and etag_matches(etag, client_tags):
            await self._send_not_modified(headers, send)
            return

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": headers,
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def _send_not_modified(self, headers: List[tuple], send) -> None:
        """Emit a bodyless 304 carrying only the still-valid metadata."""
        preserved = [
            (key, value)
            for key, value in headers
            if key.lower() not in _STRIPPED_ON_304
        ]

        await send(
            {
                "type": "http.response.start",
                "status": 304,
                "headers": preserved,
            }
        )
        await send({"type": "http.response.body", "body": b""})
