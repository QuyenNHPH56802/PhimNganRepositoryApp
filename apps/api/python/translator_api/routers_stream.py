"""Progress streaming router.

Phase 8 publishes `workflow_step_status` updates via:
  WebSocket  /workflows/{id}/ws
  SSE        /workflows/{id}/events

Both endpoints subscribe to an in-process broker keyed by workflow id.
Activities emit updates via `publish_step(...)`; the helpers here fan them
out to subscribers.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/workflows", tags=["workflow-stream"])


_subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)


def publish_step(workflow_id: str, payload: dict[str, Any]) -> None:
    """Push a step update to every subscriber for `workflow_id`."""

    for queue in list(_subscribers.get(workflow_id, set())):
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:  # pragma: no cover - queue bounded
            pass


@router.websocket("/{workflow_id}/ws")
async def stream_websocket(websocket: WebSocket, workflow_id: str) -> None:
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=128)
    _subscribers[workflow_id].add(queue)
    try:
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        return
    finally:
        _subscribers[workflow_id].discard(queue)


@router.get("/{workflow_id}/events")
async def stream_sse(workflow_id: str) -> StreamingResponse:
    async def iterator():
        queue: asyncio.Queue = asyncio.Queue(maxsize=128)
        _subscribers[workflow_id].add(queue)
        try:
            yield ": heartbeat\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            _subscribers[workflow_id].discard(queue)

    return StreamingResponse(iterator(), media_type="text/event-stream")