"""
WebSocket endpoint — real-time agent progress stream.
WS /ws/applications/{id}

Flow:
  Frontend connects → FastAPI subscribes to Redis channel → forwards events → frontend updates UI
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.redis_service import subscribe_to_app

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/applications/{app_id}")
async def websocket_agent_progress(websocket: WebSocket, app_id: str):
    """
    Subscribe to Redis pub/sub channel for this application.
    Forward every event to the connected frontend client.
    """
    await websocket.accept()

    pubsub = await subscribe_to_app(app_id)

    # Send connection confirmation
    await websocket.send_json({
        "event_type": "CONNECTED",
        "payload": {"app_id": app_id, "message": "Subscribed to agent pipeline events"},
    })

    try:
        while True:
            # Non-blocking check for Redis messages (100ms timeout)
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=0.1,
            )

            if message and message.get("type") == "message":
                data = message.get("data")
                if data:
                    try:
                        event = json.loads(data)
                        await websocket.send_json(event)
                    except json.JSONDecodeError:
                        pass

            # Small sleep to avoid busy-looping
            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        await pubsub.unsubscribe()
        await pubsub.aclose()
    except Exception as e:
        await pubsub.unsubscribe()
        await pubsub.aclose()
        await websocket.close(code=1011, reason=str(e))



