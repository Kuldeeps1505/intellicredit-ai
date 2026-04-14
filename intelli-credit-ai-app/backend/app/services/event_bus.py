"""
In-process event bus + live pipeline state store.
Uses a file-based state store so it survives uvicorn --reload.
The thread writes events here; the polling endpoint reads from here.
"""
import asyncio
import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any

# ── State file location ───────────────────────────────────────────────────────
_STATE_DIR = Path(__file__).parent.parent.parent / "pipeline_state"
_STATE_DIR.mkdir(exist_ok=True)


def _state_file(app_id: str) -> Path:
    return _STATE_DIR / f"{app_id}.json"


def _read_state(app_id: str) -> Dict[str, Any]:
    f = _state_file(app_id)
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            pass
    return {"agents": {}, "logs": [], "progress": 0, "done": False}


def _write_state(app_id: str, state: Dict[str, Any]):
    try:
        _state_file(app_id).write_text(json.dumps(state))
    except Exception:
        pass


def get_pipeline_state(app_id: str) -> Dict[str, Any]:
    return _read_state(app_id)


def update_agent_state(app_id: str, agent_id: str, status: str, elapsed: int = 0):
    state = _read_state(app_id)
    state["agents"][agent_id] = {"status": status, "elapsed": elapsed}
    # Recompute progress
    completed = sum(1 for v in state["agents"].values() if v["status"] == "complete")
    total = 9
    state["progress"] = min(int((completed / total) * 100), 99)
    if status == "complete" and completed >= total:
        state["progress"] = 100
        state["done"] = True
    _write_state(app_id, state)


def append_log(app_id: str, timestamp: str, agent: str, message: str, level: str = "info"):
    state = _read_state(app_id)
    state["logs"].append({"timestamp": timestamp, "agent": agent, "message": message, "level": level})
    if len(state["logs"]) > 200:
        state["logs"] = state["logs"][-200:]
    _write_state(app_id, state)


def mark_done(app_id: str):
    state = _read_state(app_id)
    state["progress"] = 100
    state["done"] = True
    _write_state(app_id, state)


def reset_pipeline_state(app_id: str):
    """Clear state when pipeline is re-run."""
    f = _state_file(app_id)
    if f.exists():
        f.unlink()


# ── WebSocket pub/sub ─────────────────────────────────────────────────────────
_subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)


def subscribe(app_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers[app_id].append(q)
    return q


def unsubscribe(app_id: str, q: asyncio.Queue):
    try:
        _subscribers[app_id].remove(q)
    except ValueError:
        pass


async def publish(app_id: str, event: dict):
    """Broadcast to WebSocket subscribers AND update file-based state."""
    etype = event.get("event_type", "")
    agent_id = event.get("agent_id") or event.get("agentId", "")
    ts = (event.get("timestamp", ""))[11:19] or "00:00:00"

    if etype in ("AGENT_STATUS", "agent_status") and agent_id:
        update_agent_state(app_id, agent_id, "running", 0)
    elif etype in ("AGENT_COMPLETE", "agent_complete") and agent_id:
        elapsed = int(event.get("elapsed", 0))
        update_agent_state(app_id, agent_id, "complete", elapsed)
    elif etype in ("AGENT_ERROR", "agent_error") and agent_id:
        update_agent_state(app_id, agent_id, "error", 0)
    elif etype in ("COMPLETE", "complete", "pipeline_complete"):
        mark_done(app_id)

    # Forward to WebSocket subscribers
    for q in list(_subscribers.get(app_id, [])):
        await q.put(event)
