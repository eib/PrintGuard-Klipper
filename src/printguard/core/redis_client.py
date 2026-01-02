"""Async Redis client for state management and Pub/Sub."""

import redis.asyncio as redis
import json
from .config import settings

_redis_pool: redis.Redis | None = None


async def redis_subscriber(ws_manager) -> None:
    """Background task that listens to Redis Pub/Sub and broadcasts to local WebSockets."""
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(settings.REDIS_CHANNEL)
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                await ws_manager.broadcast(data)
            except Exception:
                pass


async def get_redis() -> redis.Redis:
    """Get the Redis connection pool instance."""
    global _redis_pool
    if _redis_pool is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_pool


async def init_redis() -> None:
    """Initialize the Redis connection pool."""
    global _redis_pool
    _redis_pool = redis.from_url(
        settings.REDIS_URL,
        db=settings.REDIS_DB,
        decode_responses=True,
    )


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
