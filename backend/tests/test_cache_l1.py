"""
Tests for issue #1402: the L1 cache tier.

None of this code had ever run under pytest. `MultiLevelCache.__init__`
computed `"pytest" in sys.modules` once, at import, and stored it forever, so
`get` returned `None` before touching either tier and the `@cached` decorator
called straight through. Eviction, expiry, key construction, the Redis
fallback and the serialisation branches in `cached()` were all unreachable
from a test.

`set()` was *not* short-circuited, though, so the dict filled up across a test
session with entries nothing would ever read -- a small version of the leak
these tests are about.

So the first thing every test here does is turn the cache on.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from app.core.cache import (
    DEFAULT_L1_MAX_ENTRIES,
    MultiLevelCache,
    _serialize_for_cache,
    cache_manager,
    cached,
)


@pytest.fixture
def cache() -> MultiLevelCache:
    """An enabled, isolated cache with a small ceiling so eviction is visible."""
    return MultiLevelCache(max_entries=5, sweep_interval=0.0, enabled=True)


# --------------------------------------------------------------------------
# The cache can be tested at all
# --------------------------------------------------------------------------


def test_the_cache_defaults_to_off_under_pytest():
    """The default is worth keeping: caching across tests makes failures
    depend on execution order."""
    assert MultiLevelCache().enabled is False


def test_but_it_can_be_turned_on():
    """
    The part that was missing. `_is_testing` was computed once at import and
    could never be told otherwise, so nothing in this file could have been
    written against the old version.
    """
    c = MultiLevelCache()
    assert c.enabled is False
    c.enable()
    assert c.enabled is True

    c.set("k", "v", ttl=60)
    assert c.get("k") == "v"


def test_a_disabled_cache_does_not_accumulate_entries():
    """
    `set()` used to write to L1 regardless of the disabled flag, so a cache
    nothing could read from still filled up.
    """
    c = MultiLevelCache(enabled=False)
    for i in range(100):
        c.set(f"k{i}", i, ttl=300)

    assert c.l1_size == 0
    assert c.get("k0") is None


def test_disabling_drops_what_is_held():
    c = MultiLevelCache(enabled=True)
    c.set("k", "v", ttl=300)
    assert c.l1_size == 1

    c.disable()
    assert c.l1_size == 0


# --------------------------------------------------------------------------
# L1 is bounded
# --------------------------------------------------------------------------


def test_l1_never_exceeds_its_ceiling(cache):
    """
    The bug. A plain dict with no limit, holding fully materialised response
    payloads, on a worker that runs for weeks.
    """
    for i in range(500):
        cache.set(f"key-{i}", f"value-{i}", ttl=300)

    assert cache.l1_size <= 5


def test_the_coldest_entry_is_evicted_first(cache):
    for i in range(5):
        cache.set(f"k{i}", i, ttl=300)

    # Touch k0 so it is no longer the least recently used.
    assert cache.get("k0") == 0

    cache.set("k5", 5, ttl=300)

    assert cache.get("k0") == 0
    assert cache.get("k1") is None


def test_a_read_promotes_an_entry(cache):
    for i in range(5):
        cache.set(f"k{i}", i, ttl=300)

    for _ in range(3):
        cache.get("k2")

    for i in range(5, 9):
        cache.set(f"k{i}", i, ttl=300)

    assert cache.get("k2") == 2


def test_overwriting_a_key_does_not_grow_the_cache(cache):
    for _ in range(50):
        cache.set("same-key", "value", ttl=300)

    assert cache.l1_size == 1


def test_evictions_are_counted(cache):
    for i in range(20):
        cache.set(f"k{i}", i, ttl=300)

    assert cache.stats()["evictions"] > 0


def test_the_default_ceiling_is_finite():
    assert DEFAULT_L1_MAX_ENTRIES > 0
    assert MultiLevelCache(enabled=True)._max_entries == DEFAULT_L1_MAX_ENTRIES


def test_a_ceiling_below_one_is_clamped():
    c = MultiLevelCache(max_entries=0, enabled=True)
    c.set("a", 1, ttl=300)
    assert c.l1_size == 1


# --------------------------------------------------------------------------
# Expiry is reclaimed without a read of that exact key
# --------------------------------------------------------------------------


def test_an_expired_entry_is_not_returned(cache):
    cache.set("k", "v", ttl=1)
    time.sleep(1.1)
    assert cache.get("k") is None


def test_expired_entries_are_swept_without_being_read():
    """
    The other half of the leak. Expiry used to be noticed only when someone
    read that exact key again, so a cache that never filled never reclaimed
    anything: entries written once and never read held their values for the
    life of the process.
    """
    c = MultiLevelCache(max_entries=1000, sweep_interval=0.0, enabled=True)
    for i in range(50):
        c.set(f"k{i}", i, ttl=1)

    assert c.l1_size == 50
    time.sleep(1.1)

    # A read of *some other* key is enough to trigger the sweep.
    c.get("unrelated")

    assert c.l1_size == 0


def test_the_sweep_respects_its_interval():
    c = MultiLevelCache(max_entries=1000, sweep_interval=3600.0, enabled=True)
    for i in range(10):
        c.set(f"k{i}", i, ttl=1)
    time.sleep(1.1)

    c.get("unrelated")

    # Not swept yet -- but the individual entries are still not served.
    assert c.l1_size == 10
    assert c.get("k0") is None


def test_eviction_prefers_expired_entries_over_live_ones():
    """Discarding something still valid to make room for something already
    dead is pure loss."""
    c = MultiLevelCache(max_entries=5, sweep_interval=3600.0, enabled=True)
    for i in range(4):
        c.set(f"old{i}", i, ttl=1)
    time.sleep(1.1)

    c.set("fresh", "value", ttl=300)
    c.set("fresh2", "value", ttl=300)

    assert c.get("fresh") == "value"
    assert c.get("fresh2") == "value"


def test_expiries_are_counted(cache):
    cache.set("k", "v", ttl=1)
    time.sleep(1.1)
    cache.get("k")
    assert cache.stats()["expired"] >= 1


# --------------------------------------------------------------------------
# Invalidation
# --------------------------------------------------------------------------


def test_delete_removes_from_l1(cache):
    cache.set("k", "v", ttl=300)
    cache.delete("k")
    assert cache.get("k") is None


def test_delete_pattern_removes_matching_keys(cache):
    cache.set("post_list:a", 1, ttl=300)
    cache.set("post_list:b", 2, ttl=300)
    cache.set("user:1", 3, ttl=300)

    cache.delete_pattern("post_*")

    assert cache.get("post_list:a") is None
    assert cache.get("post_list:b") is None
    assert cache.get("user:1") == 3


def test_delete_pattern_batches_its_redis_deletes():
    """
    One DELETE per matched key, serially, on the write path of every endpoint
    that invalidates. `posts.py` calls this on create, update, delete, like,
    unlike and comment.
    """
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.scan_iter.return_value = iter([f"post_{i}" for i in range(600)])
    c._redis_client = fake

    c.delete_pattern("post_*")

    # 600 keys at 250 per batch: three calls, not six hundred.
    assert fake.delete.call_count == 3
    assert sum(len(call.args) for call in fake.delete.call_args_list) == 600


def test_delete_pattern_survives_a_redis_error():
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.scan_iter.side_effect = RuntimeError("connection reset")
    c._redis_client = fake
    c.set("post_a", 1, ttl=300)

    c.delete_pattern("post_*")

    # L1 is still invalidated even when L2 cannot be reached.
    assert c.get("post_a") is None


def test_clear_l1_empties_the_tier(cache):
    for i in range(3):
        cache.set(f"k{i}", i, ttl=300)
    cache.clear_l1()
    assert cache.l1_size == 0


# --------------------------------------------------------------------------
# L2 re-hydration
# --------------------------------------------------------------------------


def test_an_l2_hit_rehydrates_l1_with_the_remaining_ttl():
    """
    The old code used a hard-coded 60 seconds, so a value with 5 seconds left
    was served from L1 for another minute.
    """
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.get.return_value = '"cached"'
    fake.ttl.return_value = 5
    c._redis_client = fake

    assert c.get("k") == "cached"

    _, expiry = c._l1_cache["k"]
    assert expiry - time.time() <= 6


def test_a_key_with_no_l2_expiry_falls_back_to_a_default():
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.get.return_value = '"cached"'
    fake.ttl.return_value = -1  # Redis: no expiry set
    c._redis_client = fake

    assert c.get("k") == "cached"
    _, expiry = c._l1_cache["k"]
    assert 0 < expiry - time.time() <= 61


def test_a_very_long_l2_ttl_is_clamped():
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.get.return_value = '"cached"'
    fake.ttl.return_value = 86_400
    c._redis_client = fake

    c.get("k")
    _, expiry = c._l1_cache["k"]
    assert expiry - time.time() <= 3601


def test_an_l2_hit_is_counted_and_rehydrated_for_the_next_read():
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.get.return_value = "42"
    fake.ttl.return_value = 100
    c._redis_client = fake

    assert c.get("k") == 42
    assert c.get("k") == 42

    # Second read came from L1.
    assert fake.get.call_count == 1
    assert c.stats()["hits_l1"] == 1
    assert c.stats()["hits_l2"] == 1


def test_a_redis_read_error_is_a_miss_not_a_crash():
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.get.side_effect = RuntimeError("connection reset")
    c._redis_client = fake

    assert c.get("k") is None


def test_a_redis_write_error_still_populates_l1():
    c = MultiLevelCache(enabled=True)
    fake = MagicMock()
    fake.setex.side_effect = RuntimeError("connection reset")
    c._redis_client = fake

    c.set("k", "v", ttl=300)
    assert c.get("k") == "v"


# --------------------------------------------------------------------------
# The decorator
# --------------------------------------------------------------------------


class _Model(BaseModel):
    value: int


def test_the_decorator_caches_a_result():
    cache_manager.enable()
    cache_manager.clear_l1()
    calls = []

    @cached(ttl=60, key_prefix="t")
    def compute(n: int):
        calls.append(n)
        return {"n": n}

    try:
        assert compute(n=1) == {"n": 1}
        assert compute(n=1) == {"n": 1}
        assert calls == [1]
    finally:
        cache_manager.disable()


def test_different_arguments_get_different_entries():
    cache_manager.enable()
    cache_manager.clear_l1()
    calls = []

    @cached(ttl=60, key_prefix="t")
    def compute(n: int):
        calls.append(n)
        return {"n": n}

    try:
        compute(n=1)
        compute(n=2)
        assert calls == [1, 2]
    finally:
        cache_manager.disable()


def test_a_disabled_cache_calls_straight_through():
    cache_manager.disable()
    calls = []

    @cached(ttl=60, key_prefix="t")
    def compute(n: int):
        calls.append(n)
        return {"n": n}

    compute(n=1)
    compute(n=1)
    assert calls == [1, 1]


def test_a_none_result_is_not_cached():
    cache_manager.enable()
    cache_manager.clear_l1()
    calls = []

    @cached(ttl=60, key_prefix="t")
    def compute():
        calls.append(1)
        return None

    try:
        assert compute() is None
        assert compute() is None
        assert calls == [1, 1]
    finally:
        cache_manager.disable()


# --------------------------------------------------------------------------
# Serialisation branches, none of which had ever run
# --------------------------------------------------------------------------


def test_a_pydantic_model_is_serialised():
    assert _serialize_for_cache(_Model(value=3)) == {"value": 3}


def test_a_list_of_models_is_serialised():
    assert _serialize_for_cache([_Model(value=1), _Model(value=2)]) == [
        {"value": 1},
        {"value": 2},
    ]


def test_a_plain_dict_passes_through():
    assert _serialize_for_cache({"a": 1}) == {"a": 1}


def test_a_list_of_scalars_passes_through():
    assert _serialize_for_cache([1, 2, 3]) == [1, 2, 3]


def test_an_arbitrary_object_becomes_its_public_attributes():
    class Thing:
        def __init__(self):
            self.a = 1
            self._private = 2

    out = _serialize_for_cache(Thing())
    assert out == {"a": "1"}


# --------------------------------------------------------------------------
# Stats
# --------------------------------------------------------------------------


def test_stats_report_the_tier_state(cache):
    cache.set("k", "v", ttl=300)
    cache.get("k")
    cache.get("missing")

    stats = cache.stats()
    assert stats["enabled"] is True
    assert stats["l1_entries"] == 1
    assert stats["l1_max_entries"] == 5
    assert stats["hits_l1"] == 1
    assert stats["misses"] == 1
    assert stats["l2_connected"] is False
