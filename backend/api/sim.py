"""/api/sim — bidirectional WebSocket bridge to AirSim.

The simulator page is the primary consumer of this endpoint. The protocol:

  Server → Client (text, JSON):
    {"type":"hello", scenario, airsim_available, frame_w, frame_h}
    {"type":"telemetry", lat, lon, alt, vx, vy, vz, battery, link_quality}
    {"type":"objective", id, status, progress}
    {"type":"status", state}        # "running"|"hovering"|"landed"|"link_loss"
    {"type":"no_signal"}            # AirSim reachable but no frames
    {"type":"disconnected"}         # AirSim connection lost

  Server → Client (binary):
    <raw JPEG bytes>                # 1 per camera frame

  Client → Server (text, JSON):
    {"type":"cmd", action:"arm"}
    {"type":"cmd", action:"takeoff"}
    {"type":"cmd", action:"land"}
    {"type":"cmd", action:"rtl"}
    {"type":"cmd", action:"velocity", vx, vy, vz, yaw}
    {"type":"cmd", action:"goto", lat, lon, alt}
    {"type":"ping"}

When AirSim is unreachable, the server emits `{"type":"no_signal"}` once per
second so the client can render a clear standby state.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..core.settings import settings
from ..domain.drone_controller import drone_controller, AirSimUnavailable

log = logging.getLogger("sim")

router = APIRouter(prefix="/api/sim", tags=["sim"])


@router.get("/status")
def status_():
    return {
        "airsim_available": drone_controller.is_available(),
        "host": settings.projectairsim_host,
        "port_topics": settings.projectairsim_port_topics,
        "port_services": settings.projectairsim_port_services,
        "scene": settings.projectairsim_scene,
        "drone": settings.projectairsim_drone,
        "engine": "ProjectAirSim 1.x (UE 5.7)",
    }


@router.websocket("/ws/{scenario_slug}")
async def sim_socket(websocket: WebSocket, scenario_slug: str):
    await websocket.accept()
    airsim_ok = drone_controller.is_available()
    await websocket.send_text(json.dumps({
        "type": "hello",
        "scenario": scenario_slug,
        "airsim_available": airsim_ok,
        "server_time": time.time(),
    }))
    log.info("sim_ws open scenario=%s airsim=%s", scenario_slug, airsim_ok)

    stop = asyncio.Event()

    async def reader():
        """Read client commands and forward to AirSim."""
        try:
            while not stop.is_set():
                msg = await websocket.receive_text()
                try:
                    data = json.loads(msg)
                except Exception:
                    continue
                await _handle_command(data)
        except WebSocketDisconnect:
            stop.set()
        except Exception as exc:  # noqa: BLE001
            log.exception("sim_ws reader: %s", exc)
            stop.set()

    async def writer():
        """Stream frames + telemetry to the client."""
        last_telemetry = 0.0
        try:
            while not stop.is_set():
                if not drone_controller.is_available():
                    # No AirSim: emit no_signal + synthetic telemetry
                    await websocket.send_text(json.dumps({
                        "type": "no_signal",
                        "battery": 100,
                    }))
                    await asyncio.sleep(1.0)
                    continue

                try:
                    frame = await asyncio.to_thread(drone_controller.capture_frame)
                    state = await asyncio.to_thread(drone_controller.get_state)
                except AirSimUnavailable:
                    await websocket.send_text(json.dumps({"type": "disconnected"}))
                    await asyncio.sleep(1.0)
                    continue

                if frame is not None:
                    await websocket.send_bytes(frame)

                now = time.time()
                if now - last_telemetry > 0.1:  # 10 Hz telemetry
                    await websocket.send_text(json.dumps({
                        "type": "telemetry",
                        **state,
                        "battery": 100 - min(100, int(now % 60)),  # crude demo decay
                        "link_quality": 0.98,
                    }))
                    last_telemetry = now

                await asyncio.sleep(0.033)  # ~30 fps target
        except WebSocketDisconnect:
            stop.set()
        except Exception as exc:  # noqa: BLE001
            log.exception("sim_ws writer: %s", exc)
            stop.set()

    reader_task = asyncio.create_task(reader())
    writer_task = asyncio.create_task(writer())
    await asyncio.wait({reader_task, writer_task}, return_when=asyncio.FIRST_COMPLETED)
    stop.set()
    for t in (reader_task, writer_task):
        if not t.done():
            t.cancel()
    log.info("sim_ws closed scenario=%s", scenario_slug)


async def _handle_command(data: dict) -> None:
    """Translate client commands into ProjectAirSim calls."""
    if data.get("type") != "cmd":
        return
    action = data.get("action")

    def _do():
        if not drone_controller.is_available():
            return
        if action == "arm":
            drone_controller.arm()
        elif action == "takeoff":
            drone_controller.takeoff()
        elif action == "land":
            drone_controller.land()
        elif action == "rtl":
            drone_controller.rtl()
        elif action == "velocity":
            drone_controller.move_by_velocity(
                float(data.get("vx", 0)),
                float(data.get("vy", 0)),
                float(data.get("vz", 0)),
                float(data.get("yaw", 0)),
            )
        elif action == "goto":
            drone_controller.goto(
                float(data.get("lat", 0)),
                float(data.get("lon", 0)),
                float(data.get("alt", 20)),
            )

    try:
        await asyncio.to_thread(_do)
    except Exception as exc:  # noqa: BLE001
        log.warning("cmd %s failed: %s", action, exc)