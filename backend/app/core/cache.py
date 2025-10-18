"""Redis cache helper for session storage and pub/sub.

Provides simple helpers to create/get the Redis client, push/list messages,
store session meta and publish messages to session channels.
"""

from __future__ import annotations

import os
import json
import asyncio
from typing import Any, List, Optional

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis: Optional["aioredis.Redis"] = None


async def get_redis() -> "aioredis.Redis":
    global _redis
    if _redis is None:
        if aioredis is None:
            raise RuntimeError("redis.asyncio is not installed. Install 'redis' package.")
        _redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis


def _messages_key(session_id: str) -> str:
    return f"session:{session_id}:messages"


def _meta_key(session_id: str) -> str:
    return f"session:{session_id}:meta"


def _channel_name(session_id: str) -> str:
    return f"session:{session_id}:channel"


async def create_session(session_id: str, meta: Optional[dict] = None, ttl_seconds: int = 6 * 3600) -> None:
    r = await get_redis()
    key = _meta_key(session_id)
    if meta:
        await r.hset(key, mapping={k: json.dumps(v) for k, v in meta.items()})
    await r.expire(key, ttl_seconds)


async def set_session_meta(session_id: str, field: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
    r = await get_redis()
    key = _meta_key(session_id)
    await r.hset(key, field, json.dumps(value))
    if ttl_seconds:
        await r.expire(key, ttl_seconds)


async def get_session_meta(session_id: str) -> dict:
    r = await get_redis()
    key = _meta_key(session_id)
    raw = await r.hgetall(key)
    return {k: json.loads(v) if v is not None else None for k, v in raw.items()}


async def append_message(session_id: str, message: dict) -> None:
    """Append message JSON to session list (right push)."""
    r = await get_redis()
    key = _messages_key(session_id)
    await r.rpush(key, json.dumps(message))


async def get_messages(session_id: str, start: int = 0, end: int = -1) -> List[dict]:
    r = await get_redis()
    key = _messages_key(session_id)
    items = await r.lrange(key, start, end)
    return [json.loads(i) for i in items]


async def publish_message(session_id: str, message: dict) -> None:
    r = await get_redis()
    channel = _channel_name(session_id)
    await r.publish(channel, json.dumps(message))


async def subscribe(session_id: str):
    """Return a PubSub instance subscribed to the session channel.

    Caller should iterate over `pubsub.listen()` or use `get_message` with timeout.
    """
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(_channel_name(session_id))
    return pubsub
