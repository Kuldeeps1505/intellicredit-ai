"""
Simple in-process event bus using asyncio.Queue.
Replaces Redis pub/sub for hackathon/demo — no external services needed.
"""
import asyncio
from collections import defaultdict
from typing import Dict, List

# app_id → list of subscriber queues
_subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)


def subscribe(app_id: str) -> asyncio.Queue:
    """Create and register a new queue for this app_id. Returns the queue."""
    q: asyncio.Queue = asyncio.Queue()
    _subscribers[app_id].append(q)
    return q


def unsubscribe(app_id: str, q: asyncio.Queue):
    """Remove a subscriber queue."""
    try:
        _subscribers[app_id].remove(q)
    except ValueError:
        pass


async def publish(app_id: str, event: dict):
    """Broadcast event to all subscribers of this app_id."""
    for q in list(_subscribers.get(app_id, [])):
        await q.put(event)
