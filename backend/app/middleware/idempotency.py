import json
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize a global redis connection pool for idempotency caching
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis for idempotency: {e}")
    redis_client = None


class IdempotentRoute(APIRoute):
    """
    Custom APIRoute that implements Idempotency for POST/PUT/PATCH requests.
    Requires an 'Idempotency-Key' header. Caches the response in Redis for 24 hours.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            idempotency_key = request.headers.get("Idempotency-Key")

            if not idempotency_key or request.method not in ["POST", "PUT", "PATCH"]:
                # If no key is provided, bypass idempotency check
                return await original_route_handler(request)

            if redis_client is None:
                # Fallback if Redis is down
                logger.warning(
                    "Redis client is not available. Bypassing idempotency check."
                )
                return await original_route_handler(request)

            # Ensure uniqueness by user if auth exists, otherwise just key
            user_id = "anonymous"
            if "Authorization" in request.headers:
                user_id = "authenticated"

            cache_key = f"idempotent:{user_id}:{idempotency_key}"

            # Check cache
            try:
                cached_data_str = redis_client.get(cache_key)
                if cached_data_str:
                    data = json.loads(cached_data_str)

                    headers = data.get("headers", {})
                    headers["X-Idempotent-Cache"] = "hit"

                    return Response(
                        content=data["body"],
                        status_code=data["status_code"],
                        headers=headers,
                        media_type=data.get("media_type", "application/json"),
                    )
            except Exception as e:
                logger.error(f"Error reading idempotency key from Redis: {e}")
                return await original_route_handler(request)

            # Lock to prevent race conditions on the same key
            lock_key = f"{cache_key}:lock"
            is_new = redis_client.setnx(lock_key, "locked")
            if not is_new:
                # Another request is currently processing this key
                return Response(
                    content=json.dumps(
                        {"success": False, "message": "Request already in progress"}
                    ),
                    status_code=409,
                    media_type="application/json",
                )

            redis_client.expire(lock_key, 60)  # 60 second lock

            try:
                # Process the request
                response: Response = await original_route_handler(request)

                # Only cache successful or client-error responses, not 500s
                if hasattr(response, "body") and response.status_code < 500:
                    cache_payload = {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response.body.decode("utf-8"),
                        "media_type": response.media_type,
                    }
                    redis_client.setex(
                        cache_key, 86400, json.dumps(cache_payload)
                    )  # cache for 24 hours
            finally:
                redis_client.delete(lock_key)

            return response

        return custom_route_handler
