"""
Redis service — session state + pub/sub for WebSocket events.
"""
import json
import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


# ── Session State ─────────────────────────────────────────
async def set_session(app_id: str, key: str, value: dict, ttl: int = 86400):
    """Write to shared agent session: session:{app_id}:{key}"""
    r = await get_redis()
    full_key = f"session:{app_id}:{key}"
    await r.set(full_key, json.dumps(value), ex=ttl)


async def get_session(app_id: str, key: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(f"session:{app_id}:{key}")
    return json.loads(raw) if raw else None


async def delete_session(app_id: str, key: str):
    r = await get_redis()
    await r.delete(f"session:{app_id}:{key}")


# ── Pub/Sub (WebSocket events) ────────────────────────────
CHANNEL_PREFIX = "ws:app:"


async def publish_event(app_id: str, event: dict):
    """
    Publish an event to the Redis channel for this application.
    WebSocket handler subscribes to this channel and forwards to frontend.
    """
    r = await get_redis()
    channel = f"{CHANNEL_PREFIX}{app_id}"
    await r.publish(channel, json.dumps(event))


async def subscribe_to_app(app_id: str):
    """
    Returns an async pubsub object subscribed to this application's channel.
    Used by the WebSocket endpoint.
    """
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(f"{CHANNEL_PREFIX}{app_id}")
    return pubsub