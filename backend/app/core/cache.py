import asyncio
import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable

from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from redis import asyncio as aioredis

from app.core.config import settings

# L1 In-Memory Cache
_local_cache: dict[str, dict[str, Any]] = {}

# L2 Redis Cache
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

def multi_level_cache(expire: int = 300, prefix: str = "cache"):
    """
    Multi-level caching decorator for FastAPI route handlers.
    Checks L1 (in-memory dict) first, then L2 (Redis).
    Automatically serializes Pydantic models.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key based on primitive arguments (ignoring Session, User, Request)
            key_parts = [prefix, func.__name__]
            for arg in args:
                if isinstance(arg, (str, int, float, bool, tuple)):
                    key_parts.append(str(arg))
                elif hasattr(arg, 'id') or hasattr(arg, 'uuid'): # Handle UUID params if passed positionally
                    key_parts.append(str(getattr(arg, 'id', getattr(arg, 'uuid', ''))))
                    
            for k, v in kwargs.items():
                if isinstance(v, (str, int, float, bool, tuple)):
                    key_parts.append(f"{k}={v}")
                elif hasattr(v, 'id') or hasattr(v, 'uuid'):
                    key_parts.append(f"{k}={getattr(v, 'id', getattr(v, 'uuid', ''))}")
                elif str(type(v)) == "<class 'uuid.UUID'>":
                    key_parts.append(f"{k}={v}")
            
            raw_key = ":".join(key_parts)
            cache_key = hashlib.md5(raw_key.encode()).hexdigest()
            current_time = time.time()
            
            # 1. Check L1 Cache
            if cache_key in _local_cache:
                entry = _local_cache[cache_key]
                if entry['expires_at'] > current_time:
                    return entry['data']
                else:
                    del _local_cache[cache_key]
            
            # 2. Check L2 Cache
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    # Backfill L1
                    _local_cache[cache_key] = {
                        'data': data,
                        'expires_at': current_time + expire
                    }
                    return data
            except Exception as e:
                print(f"Redis cache error on get: {e}")
                
            # 3. Cache Miss - Execute Original Function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await run_in_threadpool(func, *args, **kwargs)
                
            # Handle empty/None responses gracefully
            if result is None:
                return result
                
            # Serialize result for caching
            serializable_data = jsonable_encoder(result)
            
            # Populate L1
            _local_cache[cache_key] = {
                'data': serializable_data,
                'expires_at': current_time + expire
            }
            
            # Populate L2
            try:
                await redis_client.setex(cache_key, expire, json.dumps(serializable_data))
            except Exception as e:
                print(f"Redis cache error on set: {e}")
                
            return result
        return wrapper
    return decorator
