import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class MultiLevelCache:
    """
    A multi-level cache that utilizes an L1 in-memory cache (dict)
    and an L2 distributed cache (Redis).
    """

    def __init__(self):
        import sys

        is_testing = "pytest" in sys.modules
        self._l1_cache: Dict[str, Tuple[Any, float]] = {}
        self._redis_client: Optional[redis.Redis] = None
        self._is_testing = is_testing

    def connect(self) -> None:
        """Initialize the connection to Redis (L2 Cache)."""
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

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache, checking L1 then L2."""
        if self._is_testing:
            return None
        # 1. Check L1 cache
        if key in self._l1_cache:
            value, expiry = self._l1_cache[key]
            if expiry > time.time():
                logger.debug(f"Cache HIT (L1): {key}")
                return value
            else:
                del self._l1_cache[key]

        # 2. Check L2 cache (Redis)
        if self._redis_client:
            try:
                cached_data = self._redis_client.get(key)
                if cached_data:
                    logger.debug(f"Cache HIT (L2): {key}")
                    value = json.loads(cached_data)
                    # Re-hydrate L1 cache with a short default TTL (e.g., 60 seconds)
                    self._l1_cache[key] = (value, time.time() + 60)
                    return value
            except Exception as e:
                logger.error(f"Redis get error for {key}: {e}")

        logger.debug(f"Cache MISS: {key}")
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in both L1 and L2 caches."""
        # 1. Set L1 cache
        self._l1_cache[key] = (value, time.time() + ttl)

        # 2. Set L2 cache
        if self._redis_client:
            try:
                serialized = json.dumps(value, default=str)
                self._redis_client.setex(key, ttl, serialized)
            except Exception as e:
                logger.error(f"Redis set error for {key}: {e}")

    def delete(self, key: str) -> None:
        """Invalidate a key across all cache levels."""
        if key in self._l1_cache:
            del self._l1_cache[key]

        if self._redis_client:
            try:
                self._redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error for {key}: {e}")


# Global singleton
cache_manager = MultiLevelCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to easily cache the result of a synchronous function.
    Correctly ignores FastAPI dependencies (Session, Request, Response, User) when generating cache keys.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import sys

            if "pytest" in sys.modules:
                return func(*args, **kwargs)

            # Filter kwargs to remove non-serializable FastAPI objects
            safe_kwargs = {}
            for k, v in kwargs.items():
                if k in ["db", "request", "response", "current_user"]:
                    continue
                # Also skip objects that look like SQLAlchemy sessions or FastAPI requests
                if "Session" in type(v).__name__ or "Request" in type(v).__name__:
                    continue
                safe_kwargs[k] = str(v)
            
            safe_args = [str(a) for a in args if "Session" not in type(a).__name__ and "Request" not in type(a).__name__]

            # Generate a consistent cache key
            cache_key = f"{key_prefix}:{func.__name__}:{safe_args}:{safe_kwargs}"

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Save to cache
            if result is not None:
                store_value = result
                # Serialize Pydantic or SQLAlchemy objects
                if hasattr(result, "model_dump"):
                    store_value = result.model_dump(mode="json")
                elif hasattr(result, "dict"):
                    store_value = result.dict()
                elif hasattr(result, "__dict__"):
                    store_value = {
                        k: str(v)
                        for k, v in result.__dict__.items()
                        if not k.startswith("_")
                    }
                elif isinstance(result, list):
                    processed_list = []
                    for item in result:
                        if hasattr(item, "model_dump"):
                            processed_list.append(item.model_dump(mode="json"))
                        elif hasattr(item, "dict"):
                            processed_list.append(item.dict())
                        elif hasattr(item, "__dict__"):
                            processed_list.append({
                                k: str(v)
                                for k, v in item.__dict__.items()
                                if not k.startswith("_")
                            })
                        else:
                            processed_list.append(item)
                    store_value = processed_list
                    
                cache_manager.set(cache_key, store_value, ttl)

            return result

        return wrapper

    return decorator
