"""
Redis service — replaced with in-process event bus for hackathon demo.
No Redis required. All pub/sub goes through asyncio.Queue via event_bus.py.
Session state stored in a simple dict.
"""
from app.services.event_bus import publish as _publish, subscribe, unsubscribe

# ── In-memory session store ───────────────────────────────────────────────────
_session: dict = {}


async def set_session(app_id: str, key: str, value: dict, ttl: int = 86400):
    _session[f"{app_id}:{key}"] = value


async def get_session(app_id: str, key: str) -> dict | None:
    return _session.get(f"{app_id}:{key}")


async def delete_session(app_id: str, key: str):
    _session.pop(f"{app_id}:{key}", None)


# ── Pub/Sub (kept for compatibility with existing agent code) ─────────────────

async def publish_event(app_id: str, event: dict):
    await _publish(app_id, event)


async def subscribe_to_app(app_id: str):
    """Returns a queue-backed pubsub shim compatible with the WebSocket router."""
    q = subscribe(app_id)
    return _QueuePubSub(app_id, q)


class _QueuePubSub:
    def __init__(self, app_id: str, queue):
        self._app_id = app_id
        self._queue = queue

    async def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 0.1):
        import asyncio, json
        try:
            event = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            return {"type": "message", "data": json.dumps(event)}
        except asyncio.TimeoutError:
            return None

    async def unsubscribe(self, *args):
        unsubscribe(self._app_id, self._queue)

    async def aclose(self):
        unsubscribe(self._app_id, self._queue)
