"""
Two-level response cache: a bounded in-process L1 in front of Redis.

The L1 tier is what most of this file is about, because the previous version
had none of the machinery that makes an in-process cache safe to run for
weeks:

* it was a plain dict with no size limit;
* the only thing that removed an expired entry was a read of that exact key,
  so a key written once and never read again held its value for the life of
  the process;
* reads added entries too -- an L2 hit re-hydrated L1 with a hard-coded 60
  second TTL regardless of what the caller had asked for;
* and `set()` wrote to the dict even when the cache was switched off, which
  under pytest meant filling a dict nothing would ever read from.

The keys `@cached` builds are per-caller and per-argument, so the key space is
the product of every distinct user id and every distinct set of query
arguments the decorated routes see. Unbounded growth of a dict holding fully
materialised response payloads, on a long-lived worker.

L1 is an LRU with a maximum entry count and a periodic sweep now, and the
enabled/disabled state is explicit rather than sniffed from `sys.modules` --
which is the other half of the problem, because a cache that turns itself off
whenever pytest is imported is a cache no test can exercise.

Not addressed here: `@cached` omits the caller from the key unless
`current_user` arrives as a keyword argument, so per-user responses can be
served across accounts. That is #1170, it is a change to key construction
rather than to the store, and the two want separate review.
"""

import fnmatch
import json
import logging
import sys
import threading
import time
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

#: Maximum number of entries the in-process L1 tier will hold.
#:
#: A ceiling on entries rather than on bytes: measuring the size of an
#: arbitrary decoded JSON structure means walking it on every write, which
#: costs more than the cache saves. The count is what stops the dict growing
#: without limit, and the eviction policy is what decides which entries a full
#: cache keeps.
DEFAULT_L1_MAX_ENTRIES = 1000

#: How often the expiry sweep runs, in seconds.
#:
#: Eviction alone handles a full cache; the sweep handles the other shape --
#: a cache that never fills, whose entries expire and are never read again.
#: Those hold their values indefinitely without it.
DEFAULT_SWEEP_INTERVAL = 60.0

#: Seconds to keep an L2 hit in L1 when the remaining TTL cannot be read.
L1_REHYDRATE_FALLBACK_TTL = 60.0

#: Ceiling on an L1 entry re-hydrated from L2. A key with an hour left in
#: Redis should not pin a copy in every worker's memory for an hour.
L1_REHYDRATE_MAX_TTL = 3600.0

#: Keys deleted per Redis round trip in `delete_pattern`.
#:
#: The old loop issued one DELETE per matched key, serially, on the write path
#: of every endpoint that invalidates a cache. Batching trades a larger
#: command for far fewer round trips.
DELETE_BATCH_SIZE = 250


class MultiLevelCache:
    """
    An L1 in-process LRU cache in front of an L2 Redis cache.

    Thread-safe: FastAPI runs sync endpoints in a thread pool, so two requests
    can be inside `get` and `set` at the same time. The lock is held only
    around dictionary work, never across a Redis call.
    """

    def __init__(
        self,
        max_entries: int = DEFAULT_L1_MAX_ENTRIES,
        sweep_interval: float = DEFAULT_SWEEP_INTERVAL,
        enabled: Optional[bool] = None,
    ):
        # An OrderedDict is the LRU: `move_to_end` on a hit, `popitem(last=False)`
        # to evict the coldest entry.
        self._l1_cache: "OrderedDict[str, Tuple[Any, float]]" = OrderedDict()
        self._redis_client: Optional[redis.Redis] = None
        self._lock = threading.RLock()

        self._max_entries = max(1, int(max_entries))
        self._sweep_interval = float(sweep_interval)
        self._last_sweep = time.time()

        # Explicit, and settable. The previous version computed
        # `"pytest" in sys.modules` once at import and could never be told
        # otherwise, so no test in the repository exercised any of this code.
        self._enabled = self._default_enabled() if enabled is None else bool(enabled)

        self._hits_l1 = 0
        self._hits_l2 = 0
        self._misses = 0
        self._evictions = 0
        self._expired = 0

    # ------------------------------------------------------------------ #
    #  Enabled state                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _default_enabled() -> bool:
        """
        Off under pytest, on otherwise.

        Caching between test cases makes failures depend on execution order,
        which is worth avoiding by default. What was not worth it was making
        that decision permanent: `enable()` and `disable()` exist so a test
        that wants to check caching behaviour can, and so the tests for this
        file can run at all.
        """
        return "pytest" not in sys.modules

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        """Turn the cache off and drop whatever L1 is holding."""
        self._enabled = False
        self.clear_l1()

    # ------------------------------------------------------------------ #
    #  Connection                                                         #
    # ------------------------------------------------------------------ #

    def connect(self) -> None:
        """Initialize the connection to Redis (L2 cache)."""
        try:
            self._redis_client = redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            self._redis_client.ping()
            logger.info("Connected to Redis for L2 caching.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis. Falling back to L1 only: {e}")
            self._redis_client = None

    def disconnect(self) -> None:
        """Close the Redis connection."""
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None

    # ------------------------------------------------------------------ #
    #  L1 bookkeeping                                                     #
    # ------------------------------------------------------------------ #

    def _sweep_expired_locked(self, now: float) -> int:
        """
        Drop every expired L1 entry. Caller holds the lock.

        Without this, expiry is only noticed when someone reads that exact key
        again -- so a cache that never reaches its size limit never reclaims
        anything, and holds its values for as long as the process runs.
        """
        stale = [key for key, (_, expiry) in self._l1_cache.items() if expiry <= now]
        for key in stale:
            del self._l1_cache[key]
        self._expired += len(stale)
        self._last_sweep = now
        return len(stale)

    def _maybe_sweep_locked(self, now: float) -> None:
        if now - self._last_sweep >= self._sweep_interval:
            swept = self._sweep_expired_locked(now)
            if swept:
                logger.debug("Cache sweep reclaimed %d expired L1 entries", swept)

    def _evict_locked(self) -> None:
        """
        Bring L1 back within its ceiling, coldest entry first.

        Expired entries go before live ones: evicting something still valid to
        make room for something already dead is pure loss.
        """
        if len(self._l1_cache) <= self._max_entries:
            return

        self._sweep_expired_locked(time.time())

        while len(self._l1_cache) > self._max_entries:
            self._l1_cache.popitem(last=False)
            self._evictions += 1

    def _store_l1_locked(self, key: str, value: Any, expiry: float) -> None:
        self._l1_cache[key] = (value, expiry)
        self._l1_cache.move_to_end(key)
        self._evict_locked()

    def clear_l1(self) -> None:
        """Empty the in-process tier. Does not touch Redis."""
        with self._lock:
            self._l1_cache.clear()

    @property
    def l1_size(self) -> int:
        with self._lock:
            return len(self._l1_cache)

    def stats(self) -> Dict[str, Any]:
        """
        Counters for the cache's behaviour.

        `evictions` climbing steadily means `max_entries` is too small for the
        key space; `expired` climbing while `evictions` stays flat means
        entries are being written and never read, which is a question about
        the TTLs rather than about the size.
        """
        with self._lock:
            return {
                "enabled": self._enabled,
                "l1_entries": len(self._l1_cache),
                "l1_max_entries": self._max_entries,
                "l2_connected": self._redis_client is not None,
                "hits_l1": self._hits_l1,
                "hits_l2": self._hits_l2,
                "misses": self._misses,
                "evictions": self._evictions,
                "expired": self._expired,
            }

    # ------------------------------------------------------------------ #
    #  Read / write                                                       #
    # ------------------------------------------------------------------ #

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value, checking L1 then L2."""
        if not self._enabled:
            return None

        now = time.time()

        with self._lock:
            self._maybe_sweep_locked(now)

            entry = self._l1_cache.get(key)
            if entry is not None:
                value, expiry = entry
                if expiry > now:
                    # A hit makes the entry the most recently used, which is
                    # the whole of the LRU policy.
                    self._l1_cache.move_to_end(key)
                    self._hits_l1 += 1
                    logger.debug(f"Cache HIT (L1): {key}")
                    return value
                del self._l1_cache[key]
                self._expired += 1

        if self._redis_client:
            try:
                cached_data = self._redis_client.get(key)
                if cached_data is not None:
                    value = json.loads(cached_data)
                    # Re-hydrate L1 for whatever L2 has left, rather than a
                    # fixed 60 seconds. The old constant meant a value with 5
                    # seconds to live was served from L1 for another minute,
                    # and one with an hour left was re-fetched twelve times an
                    # hour.
                    remaining = self._remaining_ttl(key)
                    with self._lock:
                        self._store_l1_locked(key, value, time.time() + remaining)
                    self._hits_l2 += 1
                    logger.debug(f"Cache HIT (L2): {key}")
                    return value
            except Exception as e:
                logger.error(f"Redis get error for {key}: {e}")

        self._misses += 1
        logger.debug(f"Cache MISS: {key}")
        return None

    def _remaining_ttl(self, key: str) -> float:
        """
        Seconds left on an L2 key, clamped to something sane.

        """
        try:
            ttl = int(self._redis_client.ttl(key))
        except (TypeError, ValueError):
            # `TTL` is not universally implemented -- some Redis-compatible
            # servers and most test doubles return something that is not a
            # number. Not knowing the remaining time is not a reason to skip
            # the L1 write; it is a reason to pick a conservative default.
            return L1_REHYDRATE_FALLBACK_TTL
        except Exception:
            return L1_REHYDRATE_FALLBACK_TTL

        if ttl < 0:
            # Redis answers -1 for a key with no expiry and -2 for one that
            # has just vanished. Neither is a duration.
            return L1_REHYDRATE_FALLBACK_TTL
        return float(min(ttl, L1_REHYDRATE_MAX_TTL))

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in both L1 and L2."""
        if not self._enabled:
            # The old version wrote to L1 regardless, so a disabled cache
            # still accumulated entries nothing would ever read.
            return

        ttl = int(ttl)
        if ttl <= 0:
            # A non-positive TTL is "already expired". Storing it would put an
            # entry in L1 that can only ever be a miss, and `SETEX` rejects it
            # outright, so the honest answer is to cache nothing.
            self.delete(key)
            return

        with self._lock:
            self._store_l1_locked(key, value, time.time() + ttl)

        if self._redis_client:
            try:
                serialized = json.dumps(value, default=str)
                self._redis_client.setex(key, ttl, serialized)
            except Exception as e:
                logger.error(f"Redis set error for {key}: {e}")

    def delete(self, key: str) -> None:
        """Invalidate a key across all cache levels."""
        with self._lock:
            self._l1_cache.pop(key, None)

        if self._redis_client:
            try:
                self._redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error for {key}: {e}")

    def delete_pattern(self, pattern: str) -> None:
        """
        Invalidate keys matching a glob across all cache levels.

        Called on every write to the most frequently written endpoints, so the
        Redis half batches: the old loop issued one DELETE per matched key,
        serially, which is a round trip per key on a warm cache.
        """
        with self._lock:
            doomed = [k for k in self._l1_cache if fnmatch.fnmatch(k, pattern)]
            for key in doomed:
                del self._l1_cache[key]

        if not self._redis_client:
            return

        try:
            batch: List[str] = []
            for key in self._redis_client.scan_iter(match=pattern, count=500):
                batch.append(key)
                if len(batch) >= DELETE_BATCH_SIZE:
                    self._redis_client.delete(*batch)
                    batch.clear()
            if batch:
                self._redis_client.delete(*batch)
        except Exception as e:
            logger.error(f"Redis delete_pattern error for {pattern}: {e}")


# Global singleton.
#
# Sized from configuration rather than the module constants, so the ceiling
# can be raised on a deployment whose working set is larger than the default
# without editing code.
cache_manager = MultiLevelCache(
    max_entries=settings.CACHE_L1_MAX_ENTRIES,
    sweep_interval=settings.CACHE_L1_SWEEP_SECONDS,
)


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Cache the result of a synchronous function.

    Ignores FastAPI dependencies (Session, Request, Response, User) when
    building the key.

    Note: the caller only reaches the key when `current_user` is passed as a
    keyword argument, which is #1170 and not fixed here.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_manager.enabled:
                return func(*args, **kwargs)

            safe_kwargs = {}
            user_id_key = ""
            for k, v in kwargs.items():
                if k == "current_user" and hasattr(v, "id"):
                    user_id_key = f"u:{v.id}"
                if k in ["db", "request", "response", "current_user"]:
                    continue
                # Also skip objects that look like SQLAlchemy sessions or FastAPI requests
                if "Session" in type(v).__name__ or "Request" in type(v).__name__:
                    continue
                safe_kwargs[k] = str(v)

            safe_args = [
                str(a)
                for a in args
                if "Session" not in type(a).__name__
                and "Request" not in type(a).__name__
            ]

            # Generate a consistent cache key
            cache_key = (
                f"{key_prefix}:{func.__name__}:{safe_args}:{safe_kwargs}:{user_id_key}"
            )

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            if result is None:
                return result

            store_value = _serialize_for_cache(result)
            cache_manager.set(cache_key, store_value, ttl)
            return store_value

        return wrapper

    return decorator


def _serialize_for_cache(result: Any) -> Any:
    """
    Reduce a return value to something `json.dumps` can handle.

    Split out of `cached` so it can be tested on its own: it was previously
    inline, and inside a decorator that never ran under pytest, which meant
    none of these branches had ever been exercised.
    """
    if isinstance(result, list):
        return [_serialize_one(item) for item in result]
    return _serialize_one(result)


def _serialize_one(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict") and callable(getattr(value, "dict")):
        return value.dict()
    if hasattr(value, "__dict__"):
        return {
            k: str(v) for k, v in value.__dict__.items() if not k.startswith("_")
        }
    return value
