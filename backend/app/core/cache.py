"""
Two-level cache: an in-process L1 in front of a shared Redis L2.

Three rules shape everything here.

**A cache key must name every input the value depends on.** The obvious ones
are the function's arguments. The one that is easy to miss is *who is asking*
-- and missing it is not a stale-data bug, it is one user being served
another user's response. ``current_user`` used to be dropped from the key
along with ``db`` and ``request``, on the grounds that all three are FastAPI
dependencies. But ``db`` and ``request`` carry no semantic input, and
``current_user`` is nothing but semantic input. See :func:`cached`.

**A cache that cannot forget is a memory leak.** L1 keys embed the call's
arguments, so an endpoint with a free-text or paginated parameter mints a new
key per distinct argument. Without a bound and an eviction policy the dict
grows for the lifetime of the process.

**Sync FastAPI endpoints run in a thread pool.** Every mutation of the L1
mapping is therefore concurrent and has to be guarded.
"""

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Mapping
from functools import wraps
from typing import Any, Callable, Optional, Tuple

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

#: Most entries the in-process L1 will hold. Past this the least recently used
#: entry is dropped. It is a bound on entry *count*, not bytes -- measuring
#: the size of arbitrary cached payloads costs more than it saves, and the
#: count is what keeps the failure mode ("grows forever") off the table.
DEFAULT_L1_MAX_ENTRIES = 1000

#: Longest an entry promoted from L2 is held in L1. The real ceiling is the
#: entry's remaining L2 TTL; this caps it so a very long-lived L2 entry does
#: not pin an L1 slot.
L1_PROMOTION_MAX_TTL = 60

#: Separates the parts of a cache key. Chosen because it does not appear in
#: the hex digest the argument fingerprint reduces to, so the prefix and
#: namespace stay unambiguously delimited.
KEY_SEPARATOR = ":"

#: Marks the caller in a key when the function takes no identifiable user.
ANONYMOUS = "anon"

#: Dependencies that are request plumbing rather than semantic input. Note
#: that `current_user` is deliberately *not* here.
_NON_SEMANTIC_KWARGS = frozenset({"db", "request", "response", "session"})

#: Type-name fragments identifying the same plumbing when passed positionally.
_NON_SEMANTIC_TYPES = ("Session", "Request", "Response")


class MultiLevelCache:
    """
    An L1 in-memory cache (bounded, LRU) in front of an L2 Redis cache.

    L1 absorbs the repeat reads inside one process; L2 shares across
    processes. A miss in L1 that hits L2 promotes the value back into L1.
    """

    def __init__(self, max_entries: int = DEFAULT_L1_MAX_ENTRIES):
        import sys

        # An OrderedDict rather than a plain dict: eviction needs to know
        # which entry was used least recently, and move_to_end/popitem give
        # that in O(1).
        self._l1_cache: "OrderedDict[str, Tuple[Any, float]]" = OrderedDict()
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._redis_client: Optional[redis.Redis] = None
        self._is_testing = "pytest" in sys.modules

    # -- connection ------------------------------------------------------

    def connect(self) -> None:
        """Initialize the connection to Redis (L2 Cache)."""
        try:
            self._redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self._redis_client.ping()
            logger.info("Connected to Redis for L2 caching.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis. Falling back to L1 only: {e}")
            self._redis_client = None

    def disconnect(self) -> None:
        """
        Close the Redis connection.

        The reference is cleared as well. It previously was not, so anything
        reaching the cache after shutdown used a closed client and raised
        instead of degrading to L1.
        """
        if self._redis_client:
            try:
                self._redis_client.close()
            except Exception as e:  # pragma: no cover - depends on client state
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis_client = None

    # -- L1 helpers ------------------------------------------------------

    def _l1_get(self, key: str) -> Tuple[bool, Any]:
        """``(hit, value)`` from L1, dropping the entry if it has expired."""
        with self._lock:
            entry = self._l1_cache.get(key)
            if entry is None:
                return False, None

            value, expiry = entry
            if expiry <= time.time():
                # pop, not `del`: another thread may have evicted it between
                # the get and here, and `del` would raise KeyError.
                self._l1_cache.pop(key, None)
                return False, None

            self._l1_cache.move_to_end(key)
            return True, value

    def _l1_set(self, key: str, value: Any, ttl: float) -> None:
        """Store in L1, evicting the least recently used entry if full."""
        with self._lock:
            self._l1_cache[key] = (value, time.time() + ttl)
            self._l1_cache.move_to_end(key)

            while len(self._l1_cache) > self._max_entries:
                self._l1_cache.popitem(last=False)

    def _promote(self, client: Any, key: str, value: Any) -> None:
        """
        Copy an L2 hit into L1, for no longer than it has left in L2.

        Promotion used to use a flat 60 seconds, which could outlive the L2
        entry it came from -- leaving this process serving a value the rest of
        the fleet had already dropped.
        """
        promotion_ttl = L1_PROMOTION_MAX_TTL

        try:
            remaining = client.ttl(key)
            # A negative TTL means no expiry set (-1) or the key vanished
            # between the GET and here (-2). Anything non-numeric means the
            # client is not telling us, so keep the default.
            if isinstance(remaining, (int, float)) and remaining >= 0:
                promotion_ttl = min(remaining, L1_PROMOTION_MAX_TTL)
        except Exception as e:
            logger.debug(f"Could not read TTL for {key}, using default: {e}")

        if promotion_ttl > 0:
            self._l1_set(key, value, promotion_ttl)

    # -- public API ------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache, checking L1 then L2."""
        if self._is_testing:
            return None

        hit, value = self._l1_get(key)
        if hit:
            logger.debug(f"Cache HIT (L1): {key}")
            return value

        client = self._redis_client
        if client:
            try:
                cached_data = client.get(key)
            except Exception as e:
                logger.error(f"Redis get error for {key}: {e}")
                cached_data = None

            if cached_data is not None:
                try:
                    value = json.loads(cached_data)
                except (TypeError, ValueError) as e:
                    logger.error(f"Undecodable L2 payload for {key}: {e}")
                    return None

                logger.debug(f"Cache HIT (L2): {key}")

                # Promotion is best-effort and deliberately in its own guard:
                # the value has already been decoded and is going to be
                # returned either way. Folding this into the block above meant
                # a failure here threw away a perfectly good answer.
                self._promote(client, key, value)

                return value

        logger.debug(f"Cache MISS: {key}")
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in both L1 and L2 caches."""
        self._l1_set(key, value, ttl)

        client = self._redis_client
        if client:
            try:
                serialized = json.dumps(value, default=str)
                client.setex(key, ttl, serialized)
            except Exception as e:
                logger.error(f"Redis set error for {key}: {e}")

    def delete(self, key: str) -> None:
        """Invalidate a key across all cache levels."""
        with self._lock:
            self._l1_cache.pop(key, None)

        client = self._redis_client
        if client:
            try:
                client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error for {key}: {e}")

    def delete_prefix(self, prefix: str) -> int:
        """
        Invalidate every key starting with ``prefix``. Returns how many L1
        entries were dropped.

        Without this there was no way to invalidate anything the ``@cached``
        decorator wrote: it builds keys internally from the call's arguments,
        so a caller that mutates the underlying data cannot reconstruct the
        keys it just invalidated. Stale data could only be waited out.

        Uses ``SCAN`` rather than ``KEYS`` -- ``KEYS`` blocks the Redis event
        loop for the whole sweep, which on a shared instance stalls every
        other client.
        """
        with self._lock:
            doomed = [key for key in self._l1_cache if key.startswith(prefix)]
            for key in doomed:
                self._l1_cache.pop(key, None)

        client = self._redis_client
        if client:
            try:
                for key in client.scan_iter(match=f"{prefix}*", count=500):
                    client.delete(key)
            except Exception as e:
                logger.error(f"Redis prefix delete error for {prefix}: {e}")

        return len(doomed)

    def clear_l1(self) -> None:
        """Drop every L1 entry. Mostly for tests and for shutdown."""
        with self._lock:
            self._l1_cache.clear()

    @property
    def l1_size(self) -> int:
        """How many entries L1 is currently holding."""
        with self._lock:
            return len(self._l1_cache)


# Global singleton
cache_manager = MultiLevelCache()


# ---------------------------------------------------------------------------
# Key construction
# ---------------------------------------------------------------------------


def _identify_caller(kwargs: dict) -> str:
    """
    A stable identifier for whoever is making the call.

    Reads ``current_user`` out of the resolved dependencies. Anonymous
    callers all share one identity, which is correct -- they are
    indistinguishable to the endpoint, so they see the same response.
    """
    user = kwargs.get("current_user")
    if user is None:
        return ANONYMOUS

    # A User model, or any object exposing `.id`.
    identifier = getattr(user, "id", None)

    # A mapping, which is what a dependency returning a plain dict gives.
    if identifier is None and isinstance(user, Mapping):
        identifier = user.get("id")

    if identifier is None:
        # Refuse to guess. Falling back to `str(user)` would produce
        # `<User object at 0x...>` -- unique per instance, so caching would
        # silently stop working rather than fail visibly.
        raise TypeError(
            "cached(): current_user has no `id`; pass per_user=False if this "
            "endpoint's response genuinely does not depend on the caller."
        )

    return str(identifier)


def _fingerprint(args: tuple, kwargs: dict) -> str:
    """
    A short, stable digest of the semantically meaningful arguments.

    Hashed rather than embedded verbatim: keys used to be built by
    interpolating the stringified argument list, so a long search term or a
    filter list produced a key as long as the input. Redis accepts keys up to
    512MB, but multi-kilobyte keys waste memory in both levels and make the
    logs unreadable. A digest is fixed width regardless of input.
    """
    meaningful_kwargs = {
        key: repr(value)
        for key, value in kwargs.items()
        if key not in _NON_SEMANTIC_KWARGS
        and key != "current_user"
        and not any(marker in type(value).__name__ for marker in _NON_SEMANTIC_TYPES)
    }

    meaningful_args = [
        repr(value)
        for value in args
        if not any(marker in type(value).__name__ for marker in _NON_SEMANTIC_TYPES)
    ]

    # sort_keys so two calls with the same kwargs in a different order share a
    # key rather than each getting their own.
    payload = json.dumps(
        {"args": meaningful_args, "kwargs": meaningful_kwargs},
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def build_cache_key(
    key_prefix: str,
    func_name: str,
    caller: str,
    args: tuple,
    kwargs: dict,
) -> str:
    """The key a cached call reads and writes. Public so tests can assert on it."""
    return KEY_SEPARATOR.join(
        (key_prefix or "cache", func_name, caller, _fingerprint(args, kwargs))
    )


def _serialise(result: Any) -> Any:
    """Reduce a result to something ``json.dumps`` will accept."""
    if isinstance(result, (list, tuple)):
        return [_serialise(item) for item in result]

    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")

    if hasattr(result, "dict") and callable(getattr(result, "dict")):
        return result.dict()

    if hasattr(result, "__dict__"):
        return {k: str(v) for k, v in result.__dict__.items() if not k.startswith("_")}

    return result


def cached(ttl: int = 300, key_prefix: str = "", per_user: bool = True):
    """
    Cache a synchronous function's result.

    ``per_user`` defaults to ``True``: the caller's id is part of the key, so
    two users never share an entry. It used to be unconditionally excluded --
    ``current_user`` was skipped along with ``db`` and ``request`` as "a
    FastAPI dependency" -- which meant any endpoint whose response varied by
    caller served the first caller's response to everyone else for the whole
    TTL.

    Set ``per_user=False`` only when the response genuinely does not depend on
    who asked. It is worth the keystrokes: it halves nothing if you are wrong,
    but it makes the claim explicit and reviewable, whereas the old behaviour
    made it silently for every endpoint at once.

    Request plumbing (``db``, ``request``, ``response``) is still excluded
    from the key -- it carries no semantic input, and including it would give
    every request a unique key and disable caching entirely.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if cache_manager._is_testing:
                return func(*args, **kwargs)

            caller = _identify_caller(kwargs) if per_user else ANONYMOUS
            cache_key = build_cache_key(key_prefix, func.__name__, caller, args, kwargs)

            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)

            if result is not None:
                store_value = _serialise(result)
                cache_manager.set(cache_key, store_value, ttl)
                return store_value

            return result

        # Handy for tests and for a caller that wants to invalidate everything
        # this endpoint wrote.
        wrapper.cache_key_prefix = KEY_SEPARATOR.join(
            (key_prefix or "cache", func.__name__)
        )

        return wrapper

    return decorator
