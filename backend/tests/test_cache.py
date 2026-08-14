"""
Two-level cache behaviour.

`MultiLevelCache` short-circuits under pytest (`_is_testing`), which is what
keeps the rest of the suite from picking up cached responses between tests.
These tests deliberately turn that off so the real logic is exercised, and
turn it back on afterwards.

Redis is not assumed to be running. `_redis_client` is left as `None`, which
is the documented degraded mode, and the L2 paths that need a client are
driven with a small fake.
"""

import threading
import time

import pytest

from app.core import cache as cache_module
from app.core.cache import (
    ANONYMOUS,
    MultiLevelCache,
    build_cache_key,
    cached,
)


@pytest.fixture
def cache():
    """A real, isolated cache with the test short-circuit disabled."""
    instance = MultiLevelCache(max_entries=5)
    instance._is_testing = False
    return instance


@pytest.fixture
def live_cache(monkeypatch):
    """
    Point the module-level singleton at a real cache, so the `@cached`
    decorator actually caches for the duration of a test.
    """
    instance = MultiLevelCache(max_entries=5)
    instance._is_testing = False
    monkeypatch.setattr(cache_module, "cache_manager", instance)
    return instance


class _User:
    """Stands in for the User model; only `id` is read."""

    def __init__(self, id):
        self.id = id


# ---------------------------------------------------------------------------
# Per-caller keys
# ---------------------------------------------------------------------------


def test_two_users_do_not_share_a_cached_value(live_cache):
    """
    The bug this file exists for. `current_user` was dropped from the key, so
    the first caller's response was served to everyone for the whole TTL.
    """
    calls = []

    @cached(ttl=300, key_prefix="feed")
    def personalised_feed(current_user=None):
        calls.append(current_user.id)
        return {"owner": current_user.id}

    alice = _User("alice")
    bob = _User("bob")

    assert personalised_feed(current_user=alice) == {"owner": "alice"}
    assert personalised_feed(current_user=bob) == {"owner": "bob"}

    # Both actually ran; neither was served the other's answer.
    assert calls == ["alice", "bob"]


def test_the_same_user_is_served_from_cache(live_cache):
    calls = []

    @cached(ttl=300, key_prefix="feed")
    def personalised_feed(current_user=None):
        calls.append(current_user.id)
        return {"owner": current_user.id}

    alice = _User("alice")

    personalised_feed(current_user=alice)
    personalised_feed(current_user=alice)

    assert calls == ["alice"]


def test_per_user_false_shares_one_entry(live_cache):
    """The opt-out, for responses that genuinely do not vary by caller."""
    calls = []

    @cached(ttl=300, key_prefix="public", per_user=False)
    def public_listing(current_user=None):
        calls.append(1)
        return {"items": []}

    public_listing(current_user=_User("alice"))
    public_listing(current_user=_User("bob"))

    assert len(calls) == 1


def test_anonymous_callers_share_an_entry(live_cache):
    """They are indistinguishable to the endpoint, so they see one response."""
    calls = []

    @cached(ttl=300, key_prefix="feed")
    def feed(current_user=None):
        calls.append(1)
        return {"items": []}

    feed(current_user=None)
    feed(current_user=None)

    assert len(calls) == 1


def test_a_user_without_an_id_is_refused_rather_than_guessed(live_cache):
    """
    Falling back to `str(user)` would give `<object at 0x...>` -- unique per
    instance, so caching would silently stop working instead of failing.
    """

    @cached(ttl=300, key_prefix="feed")
    def feed(current_user=None):
        return {}

    with pytest.raises(TypeError, match="per_user=False"):
        feed(current_user=object())


# ---------------------------------------------------------------------------
# Key construction
# ---------------------------------------------------------------------------


def test_key_includes_prefix_function_and_caller():
    key = build_cache_key("feed", "get_feed", "alice", (), {})

    assert key.startswith("feed:get_feed:alice:")


def test_different_arguments_produce_different_keys():
    first = build_cache_key("p", "f", ANONYMOUS, (), {"limit": 10})
    second = build_cache_key("p", "f", ANONYMOUS, (), {"limit": 20})

    assert first != second


def test_kwarg_order_does_not_change_the_key():
    """Otherwise the same call spelled two ways gets two entries."""
    first = build_cache_key("p", "f", ANONYMOUS, (), {"a": 1, "b": 2})
    second = build_cache_key("p", "f", ANONYMOUS, (), {"b": 2, "a": 1})

    assert first == second


def test_request_plumbing_is_excluded_from_the_key():
    """
    `db` and `request` carry no semantic input. Including them would give
    every request a unique key and disable caching entirely.
    """

    class Session:
        pass

    first = build_cache_key("p", "f", ANONYMOUS, (), {"limit": 10, "db": Session()})
    second = build_cache_key("p", "f", ANONYMOUS, (), {"limit": 10, "db": Session()})

    assert first == second


def test_key_length_is_bounded_by_the_input():
    """
    Keys used to embed the stringified arguments, so a long search term
    produced a proportionally long key in both cache levels.
    """
    short = build_cache_key("p", "f", ANONYMOUS, (), {"q": "a"})
    long = build_cache_key("p", "f", ANONYMOUS, (), {"q": "a" * 100_000})

    assert len(short) == len(long)
    assert len(long) < 100


def test_decorator_exposes_its_key_prefix():
    @cached(ttl=60, key_prefix="feed")
    def get_feed():
        return []

    assert get_feed.cache_key_prefix == "feed:get_feed"


# ---------------------------------------------------------------------------
# L1 bounds and eviction
# ---------------------------------------------------------------------------


def test_l1_is_bounded(cache):
    """
    The leak: entries written and never read again stayed forever, and keys
    embed arguments, so a paginated endpoint mints one per page.
    """
    for n in range(50):
        cache.set(f"key-{n}", n, ttl=300)

    assert cache.l1_size == 5


def test_eviction_drops_the_least_recently_used(cache):
    for n in range(5):
        cache.set(f"key-{n}", n, ttl=300)

    # Touch key-0 so it is no longer the coldest.
    assert cache.get("key-0") == 0

    cache.set("key-new", "new", ttl=300)

    assert cache.get("key-0") == 0
    assert cache.get("key-1") is None


def test_expired_entries_are_not_returned(cache):
    cache.set("short", "value", ttl=1)
    cache._l1_cache["short"] = ("value", time.time() - 1)

    assert cache.get("short") is None


def test_expired_entry_is_dropped_on_read(cache):
    cache.set("short", "value", ttl=300)
    cache._l1_cache["short"] = ("value", time.time() - 1)

    cache.get("short")

    assert cache.l1_size == 0


# ---------------------------------------------------------------------------
# Invalidation
# ---------------------------------------------------------------------------


def test_delete_removes_a_key(cache):
    cache.set("gone", "value", ttl=300)
    cache.delete("gone")

    assert cache.get("gone") is None


def test_delete_prefix_removes_a_whole_namespace(cache):
    """
    The decorator builds keys internally, so a caller that mutates the
    underlying data cannot reconstruct them. Without this, cached data could
    only be waited out.
    """
    cache.set("projects:get:anon:aaa", 1, ttl=300)
    cache.set("projects:get:anon:bbb", 2, ttl=300)
    cache.set("feed:get_feed:anon:ccc", 3, ttl=300)

    dropped = cache.delete_prefix("projects:get")

    assert dropped == 2
    assert cache.get("projects:get:anon:aaa") is None
    assert cache.get("feed:get_feed:anon:ccc") == 3


def test_delete_of_an_absent_key_does_not_raise(cache):
    cache.delete("never-existed")


def test_clear_l1_empties_the_map(cache):
    cache.set("a", 1, ttl=300)
    cache.set("b", 2, ttl=300)

    cache.clear_l1()

    assert cache.l1_size == 0


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


def test_concurrent_access_does_not_raise(cache):
    """
    Sync FastAPI endpoints run in a thread pool, so every L1 mutation is
    concurrent. The unguarded version could raise KeyError when two threads
    expired the same key at once.
    """
    errors = []

    def hammer(worker):
        try:
            for n in range(200):
                key = f"key-{n % 10}"
                cache.set(key, n, ttl=300)
                cache.get(key)
                if n % 20 == 0:
                    cache.delete(key)
        except Exception as exc:  # pragma: no cover - the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=hammer, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert cache.l1_size <= 5


def test_expiry_race_does_not_raise(cache):
    """Two threads reading the same expired key both hit the removal path."""
    errors = []

    cache.set("shared", "value", ttl=300)
    cache._l1_cache["shared"] = ("value", time.time() - 1)

    def read():
        try:
            for _ in range(500):
                cache.get("shared")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=read) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []


# ---------------------------------------------------------------------------
# Redis interaction
# ---------------------------------------------------------------------------


class _FakeRedis:
    """Just enough Redis for the L2 paths."""

    def __init__(self, ttl=30):
        self.store = {}
        self.ttls = {}
        self._ttl = ttl
        self.closed = False
        self.deleted = []

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value
        self.ttls[key] = ttl

    def ttl(self, key):
        return self.ttls.get(key, self._ttl)

    def delete(self, key):
        self.deleted.append(key)
        self.store.pop(key, None)

    def scan_iter(self, match="*", count=None):
        prefix = match.rstrip("*")
        return [key for key in list(self.store) if key.startswith(prefix)]

    def close(self):
        self.closed = True


def test_l2_hit_promotes_into_l1_within_the_remaining_ttl(cache):
    """
    Promotion used to use a hardcoded 60s, which could outlive the L2 entry
    it came from -- leaving this process serving a value the rest of the
    fleet had dropped.
    """
    fake = _FakeRedis()
    fake.store["k"] = "42"
    fake.ttls["k"] = 5
    cache._redis_client = fake

    assert cache.get("k") == 42

    _, expiry = cache._l1_cache["k"]
    assert expiry - time.time() <= 5 + 0.5


def test_l2_promotion_is_capped(cache):
    """A very long-lived L2 entry must not pin an L1 slot indefinitely."""
    fake = _FakeRedis()
    fake.store["k"] = "42"
    fake.ttls["k"] = 86_400
    cache._redis_client = fake

    cache.get("k")

    _, expiry = cache._l1_cache["k"]
    assert expiry - time.time() <= 60 + 0.5


def test_redis_errors_degrade_to_l1(cache):
    class Broken:
        def get(self, key):
            raise RuntimeError("redis is down")

        def setex(self, key, ttl, value):
            raise RuntimeError("redis is down")

    cache._redis_client = Broken()

    # Neither raises; the value is still served from L1.
    cache.set("k", "value", ttl=300)
    assert cache.get("k") == "value"


def test_disconnect_clears_the_client(cache):
    """
    It previously closed the connection but kept the reference, so anything
    reaching the cache after shutdown used a closed client.
    """
    fake = _FakeRedis()
    cache._redis_client = fake

    cache.disconnect()

    assert fake.closed is True
    assert cache._redis_client is None


def test_delete_prefix_reaches_l2(cache):
    fake = _FakeRedis()
    fake.store = {"projects:a": "1", "projects:b": "2", "feed:c": "3"}
    cache._redis_client = fake

    cache.delete_prefix("projects:")

    assert sorted(fake.deleted) == ["projects:a", "projects:b"]
