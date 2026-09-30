"""/api/sim — bidirectional WebSocket bridge to AirSim + Pixel Streaming config.

The simulator page is the primary consumer of this endpoint. The protocol:

  Server → Client (text, JSON):
    {"type":"hello", scenario, airsim_available, frame_w, frame_h}
    {"type":"telemetry", lat, lon, alt, vx, vy, vz, battery, link_quality}
    {"type":"objective", id, status, progress}
    {"type":"status", state}        # "running"|"hovering"|"landed"|"link_loss"
    {"type":"no_signal"}            # AirSim reachable but no frames
    {"type":"disconnected"}         # AirSim connection lost

  Client → Server (text, JSON):
    {"type":"cmd", action:"arm"}
    {"type":"cmd", action:"takeoff"}
    {"type":"cmd", action:"land"}
    {"type":"cmd", action:"rtl"}
    {"type":"cmd", action:"velocity", vx, vy, vz, yaw}
    {"type":"cmd", action:"goto", lat, lon, alt}
    {"type":"ping"}

The image transmission (图传) channel itself is no longer carried over this
WebSocket — the simulator embeds a Pixel Streaming Player iframe pointing at
the URL returned by GET /api/sim/stream-config. AirSim remains reachable via
the WebSocket for telemetry + command-only traffic.

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
from ..domain.airsim import YawMode
from ..domain.drone_controller import drone_controller, AirSimUnavailable
from ..domain.mission import MissionState, build_rules
from ..domain.scenario_manager import scenario_manager
from ..domain.waypoint_manager import WaypointManager, describe

log = logging.getLogger("sim")

router = APIRouter(prefix="/api/sim", tags=["sim"])

# One waypoint cache shared by all connections: the level's geometry is
# static for the duration of a UE session.
waypoint_manager = WaypointManager(drone_controller)

# Proximity sensors read for `clearance` rules. Each is a separate AirSim
# round-trip, so only the ones a scenario actually needs are polled — see
# `_sensors_for_scenario`.
_DISTANCE_SENSORS = ("DistanceFront", "DistanceDown")


def _read_distance(name: str) -> Optional[float]:
    """One proximity reading in metres, or None when the sim can't answer."""
    try:
        return float(drone_controller.get_distance(name))
    except Exception:  # noqa: BLE001
        # A missing sensor must not stall the 10 Hz loop; the corresponding
        # rule simply stays `pending`.
        return None


def _sensors_for_scenario(scenario: Optional[dict]) -> tuple:
    """Sensor names actually referenced by this scenario's rules.

    Returns empty when nothing needs them, so a scenario made only of
    `reach`/`hold` rules does no extra AirSim round-trips per tick.
    """
    if not scenario:
        return ()
    wanted = {
        str(r.get("sensor"))
        for r in build_rules(scenario)
        if r.get("kind") == "clearance" and r.get("sensor")
    }
    return tuple(s for s in _DISTANCE_SENSORS if s in wanted)


@router.get("/status")
def status_():
    return {
        "airsim_available": drone_controller.is_available(),
        "ip": settings.airsim_ip,
        "port": settings.airsim_port,
    }


@router.get("/stream-config")
def stream_config():
    """Pixel Streaming (UE4.27 + Cirrus) entry point for the simulator.

    Mirrors the `PIXEL_STREAMING_URL` constant in `test.py` at the repo root.
    The simulator embeds an iframe at `pixel_streaming_url`; this endpoint
    tells the frontend where to point it. `available` reflects the AirSim
    backend only — Cirrus reachability is probed client-side from the iframe
    load event.
    """
    return {
        "pixel_streaming_url": settings.pixel_streaming_url,
        "available": drone_controller.is_available(),
    }


@router.get("/waypoints")
def waypoints(slug: Optional[str] = None, refresh: bool = False):
    """Debug view of the waypoints discovered in the running UE level.

    Backs the UE-side setup: author `WP_01`-style actors in the level, hit
    this endpoint, and you get the exact coordinates the rule engine compares
    telemetry against. Returns an empty list rather than erroring when UE is
    down, so it doubles as a connectivity probe.
    """
    found = waypoint_manager.load(slug, force=refresh)
    scenario = scenario_manager.get_by_slug(slug) if slug else None
    return {
        "airsim_available": drone_controller.is_available(),
        "waypoints": describe(found),
        "count": len(found),
        "tasks": build_rules(scenario) if scenario else [],
    }


@router.websocket("/ws/{scenario_slug}")
async def sim_socket(websocket: WebSocket, scenario_slug: str):
    await websocket.accept()
    airsim_ok = drone_controller.is_available()

    # Build the mission up front so the client gets the full objective list
    # immediately, and so missing waypoints surface as `pending` rather than
    # as a list that never populates.
    scenario = scenario_manager.get_by_slug(scenario_slug)
    rules = build_rules(scenario) if scenario else []
    points = waypoint_manager.load(scenario_slug) if airsim_ok else {}
    mission = MissionState(rules, points)

    await websocket.send_text(json.dumps({
        "type": "hello",
        "scenario": scenario_slug,
        "airsim_available": airsim_ok,
        "server_time": time.time(),
        "objectives": mission.snapshot(),
        "waypoints": len(points),
    }))
    log.info(
        "sim_ws open scenario=%s airsim=%s tasks=%d waypoints=%d",
        scenario_slug, airsim_ok, len(rules), len(points),
    )

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
        """Stream telemetry and objective progress to the client.

        The image transmission (图传) channel is now served by the Pixel
        Streaming Player iframe, not by this WebSocket — see the module
        docstring. The writer's job is JSON telemetry, link state, and the
        mission rule engine's verdict on each training objective.
        """
        last_telemetry = 0.0
        sensors = _sensors_for_scenario(scenario)
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
                    state = await asyncio.to_thread(drone_controller.get_state)
                except AirSimUnavailable:
                    await websocket.send_text(json.dumps({"type": "disconnected"}))
                    await asyncio.sleep(1.0)
                    continue

                now = time.time()
                if now - last_telemetry > 0.1:  # 10 Hz telemetry
                    payload = {
                        "type": "telemetry",
                        **state,
                        "battery": 100 - min(100, int(now % 60)),  # crude demo decay
                        "link_quality": 0.98,
                    }

                    # Fold the sample into the rule engine using the NED
                    # fields (nx/ny/nz, metres) — the same frame
                    # `simGetObjectPose` returns waypoints in. The GeoPoint
                    # lat/lon/alt above are for display only; feeding those to
                    # the rules compares degrees against metres and never
                    # satisfies. If NED is missing the rules see no position
                    # and stay `pending` rather than judging against zeros.
                    telemetry = {
                        "x": state.get("nx"),
                        "y": state.get("ny"),
                        "z": state.get("nz"),
                    }
                    for name in sensors:
                        dist = _read_distance(name)
                        if dist is not None:
                            telemetry[f"sensor:{name}"] = dist

                    changed = mission.update(telemetry, now)
                    if changed:
                        # Send each changed task individually: the client's
                        # `objective` handler matches on a single id.
                        for task in changed:
                            await websocket.send_text(
                                json.dumps({"type": "objective", **task})
                            )
                        await websocket.send_text(json.dumps({
                            "type": "score",
                            "score": mission.score(),
                            "completed": mission.all_satisfied,
                        }))

                    await websocket.send_text(json.dumps(payload))
                    last_telemetry = now

                await asyncio.sleep(0.1)  # 10 Hz telemetry cadence
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
    """Translate client commands into AirSim calls."""
    if data.get("type") != "cmd":
        return
    action = data.get("action")

    def _do():
        try:
            client = drone_controller._ensure_connected()
        except AirSimUnavailable:
            return
        if action == "arm":
            client.armDisarm(True)
        elif action == "disarm":
            client.armDisarm(False)
        elif action == "emergency":
            # Kill motors — works in any phase. Mirrors /api/emergency in app.py
            # at the repo root so the gamepad Y button is a true "kill switch".
            client.armDisarm(False)
        elif action == "takeoff":
            client.takeoffAsync(timeout_sec=15).get()
        elif action == "land":
            client.landAsync().get()
        elif action == "rtl":
            # Return to the drone's own home point. This used to import
            # `RouteManager` from a module that has since been deleted, which
            # made every RTL a silent ImportError — `getHomeGeoPoint` is the
            # supported source for this and needs no extra dependency.
            try:
                home = client.getHomeGeoPoint()
            except Exception:  # noqa: BLE001
                log.warning("rtl: home point unavailable")
                return
            if home is None:
                return
            client.moveToGPSAsync(
                latitude=home.latitude,
                longitude=home.longitude,
                altitude=20.0,
                velocity=10.0,
                drivetrain=0,
                yaw_mode=0,
            ).get()
        elif action == "velocity":
            yaw = float(data.get("yaw", 0))
            vx = float(data.get("vx", 0))
            vy = float(data.get("vy", 0))
            vz = float(data.get("vz", 0))
            # Single AirSim call drives vx/vy/vz AND yaw rate concurrently —
            # mirroring app.py's control_loop (root). moveByVelocityAsync does
            # not accept a yaw parameter; moveByVelocityBodyFrameAsync does via
            # YawMode(is_rate=True, yaw_or_rate=…). This is why holding LX and
            # RY together now yaws while strafing instead of dropping one axis.
            client.moveByVelocityBodyFrameAsync(
                vx, vy, vz,
                duration=0.2,
                yaw_mode=YawMode(is_rate=True, yaw_or_rate=yaw),
            )
        elif action == "goto":
            client.moveToGPSAsync(
                latitude=float(data.get("lat", 0)),
                longitude=float(data.get("lon", 0)),
                altitude=float(data.get("alt", 20)),
                velocity=10,
            ).get()
    try:
        await asyncio.to_thread(_do)
    except Exception as exc:  # noqa: BLE001
        log.warning("cmd %s failed: %s", action, exc)