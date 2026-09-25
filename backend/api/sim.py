"""/api/sim — AirSim availability check + WebSocket live stream.

The frontend 3D simulator renders entirely in the browser using Three.js.
This endpoint exposes AirSim state (live image frames, telemetry) so the
frontend can opt-in to a real-time video feed when AirSim is available.
"""
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..core.settings import settings
from ..domain.drone_controller import drone_controller, AirSimUnavailable

router = APIRouter(prefix="/api/sim", tags=["sim"])


@router.get("/status")
def status_():
    return {
        "airsim_available": drone_controller.is_available(),
        "ip": settings.airsim_ip,
        "port": settings.airsim_port,
    }


@router.websocket("/ws/{scenario_slug}")
async def sim_socket(websocket: WebSocket, scenario_slug: str):
    await websocket.accept()
    await websocket.send_text(json.dumps({
        "type": "hello",
        "scenario": scenario_slug,
        "airsim_available": drone_controller.is_available(),
    }))

    try:
        if not drone_controller.is_available():
            # Frontend-only mode: send periodic synthetic telemetry so the
            # client knows the channel is alive.
            while True:
                await asyncio.sleep(1.0)
                await websocket.send_text(json.dumps({
                    "type": "telemetry",
                    "scenario": scenario_slug,
                    "lat": 0.0,
                    "lon": 0.0,
                    "alt": 0.0,
                    "battery": 100.0,
                }))
        else:
            while True:
                try:
                    frame = await asyncio.to_thread(drone_controller.capture_frame)
                    state = await asyncio.to_thread(drone_controller.get_state)
                    if frame is not None:
                        # Send binary frame
                        await websocket.send_bytes(frame)
                    await websocket.send_text(json.dumps({
                        "type": "telemetry",
                        **state,
                    }))
                except AirSimUnavailable:
                    await websocket.send_text(json.dumps({"type": "disconnected"}))
                    break
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        return