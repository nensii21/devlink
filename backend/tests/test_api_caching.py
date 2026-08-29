import pytest
from unittest.mock import patch, MagicMock
from app.core.cache import cache_manager, cached
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

app = FastAPI()


class MockSession:
    def __init__(self, id_val):
        self.id_val = id_val

    def __repr__(self):
        return f"<MockSession {self.id_val}>"


def get_db():
    return MockSession("db123")


def get_current_user():
    return {"id": 1, "username": "test_user"}


@app.get("/test/sync-cache")
@cached(ttl=60, key_prefix="test:sync")
def sync_endpoint(
    q: str,
    db: MockSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"data": f"cached_result_for_{q}", "user": current_user["username"]}


@app.get("/test/object-serialization")
@cached(ttl=60, key_prefix="test:serialize")
def object_endpoint():
    class ComplexObj:
        def __init__(self):
            self.id = 1
            self.name = "complex"
            self._private = "hidden"

    return [ComplexObj(), ComplexObj()]


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    # The cache is off by default under pytest. These tests need it on.
    #
    # This used to be `cache_manager._is_testing = False` -- reaching into a
    # private attribute, because there was no other way in: the flag was
    # computed once at import from `"pytest" in sys.modules` and nothing could
    # change it afterwards. `enable()` / `disable()` are that way in (#1402).
    original = cache_manager.enabled
    original_redis = cache_manager._redis_client
    cache_manager.enable()
    cache_manager.clear_l1()

    yield

    cache_manager._enabled = original
    cache_manager._redis_client = original_redis
    cache_manager.clear_l1()


def test_caching_decorator_ignores_dependencies():
    """
    Test that the cached decorator ignores FastAPI dependencies like Session, Request, User
    so that the cache key is stable across requests.
    """
    response1 = client.get("/test/sync-cache?q=hello")
    assert response1.status_code == 200
    assert response1.json()["data"] == "cached_result_for_hello"

    # Verify it was cached in L1
    keys = list(cache_manager._l1_cache.keys())
    assert len(keys) == 1

    # The key should NOT contain the memory address of MockSession
    key = keys[0]
    assert "MockSession" not in key
    assert "current_user" not in key
    assert "hello" in key


def test_cache_hit():
    """Test that subsequent requests hit the cache."""
    with patch("app.core.cache.logger.debug") as mock_logger:
        client.get("/test/sync-cache?q=world")
        # Second hit
        client.get("/test/sync-cache?q=world")

        # Check logs for cache hit
        calls = [call.args[0] for call in mock_logger.mock_calls]
        assert any("Cache HIT" in call for call in calls)


def test_object_serialization():
    """Test that the decorator correctly serializes complex objects and strips private fields."""
    response = client.get("/test/object-serialization")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "1"
    assert data[0]["name"] == "complex"
    assert "_private" not in data[0]


def test_cache_miss():
    """Test cache miss logging."""
    with patch("app.core.cache.logger.debug") as mock_logger:
        client.get("/test/sync-cache?q=new_query")

        calls = [call.args[0] for call in mock_logger.mock_calls]
        assert any("Cache MISS" in call for call in calls)


def test_l1_cache_expiry():
    """Test that items expire from L1 cache."""
    cache_manager.set("test_key", "value", ttl=-1)  # Already expired
    assert cache_manager.get("test_key") is None


def test_l1_cache_expiry_stores_nothing():
    """A non-positive TTL caches nothing rather than an entry that can only
    ever miss."""
    cache_manager.set("expired_key", "value", ttl=-1)
    assert "expired_key" not in cache_manager._l1_cache


def test_l2_redis_fallback():
    """Test that if L1 misses, it checks L2."""
    cache_manager._redis_client = MagicMock()
    cache_manager._redis_client.get.return_value = '{"from": "redis"}'

    val = cache_manager.get("redis_key")
    assert val == {"from": "redis"}

    # Should rehydrate L1
    assert "redis_key" in cache_manager._l1_cache


def test_redis_connection_failure():
    """Test graceful fallback if Redis fails."""
    with patch("app.core.cache.redis.from_url") as mock_redis:
        mock_redis.side_effect = Exception("Connection Refused")
        cache_manager.connect()
        assert cache_manager._redis_client is None


def test_redis_set_error():
    """Test graceful fallback if Redis set fails."""
    cache_manager._redis_client = MagicMock()
    cache_manager._redis_client.setex.side_effect = Exception("Write Error")

    # Should not raise exception
    cache_manager.set("error_key", "value", ttl=10)

    # Should still be in L1
    assert "error_key" in cache_manager._l1_cache


def test_redis_get_error():
    """Test graceful fallback if Redis get fails."""
    cache_manager._redis_client = MagicMock()
    cache_manager._redis_client.get.side_effect = Exception("Read Error")

    # Should return None, not raise exception
    val = cache_manager.get("error_key_get")
    assert val is None


def test_redis_delete():
    """Test delete across levels."""
    cache_manager._redis_client = MagicMock()

    cache_manager.set("del_key", "val")
    cache_manager.delete("del_key")

    assert "del_key" not in cache_manager._l1_cache
    cache_manager._redis_client.delete.assert_called_with("del_key")


def test_redis_delete_error():
    """Test graceful fallback if Redis delete fails."""
    cache_manager._redis_client = MagicMock()
    cache_manager._redis_client.delete.side_effect = Exception("Delete Error")

    cache_manager.set("del_key2", "val")
    # Should not raise
    cache_manager.delete("del_key2")

    # But it should still be removed from L1
    assert "del_key2" not in cache_manager._l1_cache
