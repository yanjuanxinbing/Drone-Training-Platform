"""Drone controller backed by ProjectAirSim (UE 5.7).

ProjectAirSim replaces the legacy AirSim client. The connection model is
async, the protocol is gRPC, and the simulator must load a scene JSONC
config on startup. Coordinates are NED throughout.

Public surface stays synchronous so the existing FastAPI bridge can call
these from `asyncio.to_thread(...)` without restructuring. Internally we
maintain a single background event loop and dispatch coroutines onto it
via `asyncio.run_coroutine_threadsafe`.

The bridge protocol (`/api/sim/ws/{slug}`) is unchanged: server streams
binary JPEG frames + JSON telemetry, accepts `cmd` frames. Only the
backend implementation is swapped.
"""
from __future__ import annotations

import asyncio
import base64
import io
import threading
import time
from typing import Optional

from PIL import Image

from .route_manager import RouteManager


class AirSimUnavailable(RuntimeError):
    pass


class DroneController:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port_topics: int = 8989,
        port_services: int = 8990,
        scene_config: str = "scene_basic_drone.jsonc",
        drone_name: str = "Drone1",
        camera_id: str = "front_center",
    ):
        self.host = host
        self.port_topics = port_topics
        self.port_services = port_services
        self.scene_config = scene_config
        self.drone_name = drone_name
        self.camera_id = camera_id

        self._client = None
        self._world = None
        self._drone = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._available_cache: Optional[float] = None
        self._available_cache_ttl = 2.0

    # ── Event loop management ────────────────────────────────────────────
    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is not None and self._loop.is_running():
            return self._loop
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=loop.run_forever, daemon=True, name="pa-loop")
        thread.start()
        self._loop = loop
        self._loop_thread = thread
        return loop

    def _run(self, coro, timeout: float = 5.0):
        loop = self._ensure_loop()
        fut = asyncio.run_coroutine_threadsafe(coro, loop)
        return fut.result(timeout=timeout)

    # ── Connection lifecycle (sync facade over async connect) ────────────
    async def _connect_async(self):
        from projectairsim import ProjectAirSimClient, World, Drone

        if self._client is not None:
            return self._client
        client = ProjectAirSimClient(
            address=self.host,
            port_topics=self.port_topics,
            port_services=self.port_services,
        )
        client.connect()
        world = World(client, self.scene_config, delay_after_load_sec=2)
        drone = Drone(client, world, self.drone_name)
        self._client = client
        self._world = world
        self._drone = drone
        return client

    def _ensure_connected_sync(self):
        if self._drone is not None:
            return self._drone
        with self._lock:
            if self._drone is not None:
                return self._drone
            try:
                self._run(self._connect_async(), timeout=10.0)
            except Exception as exc:  # noqa: BLE001
                raise AirSimUnavailable(
                    f"ProjectAirSim unreachable at {self.host}:{self.port_topics}/"
                    f"{self.port_services} ({exc})"
                ) from exc
        return self._drone

    def is_available(self) -> bool:
        now = time.time()
        if self._available_cache is not None and now - self._available_cache < self._available_cache_ttl:
            return self._available_cache > 0
        try:
            self._ensure_connected_sync()
            self._available_cache = now
            return True
        except AirSimUnavailable:
            self._available_cache = now
            return False

    def close(self):
        if self._client is not None and self._loop is not None:
            try:
                self._run(self._client.disconnect() if hasattr(self._client, "disconnect") else self._noop())
            except Exception:
                pass
        self._client = None
        self._world = None
        self._drone = None

    async def _noop(self):  # placeholder for symmetry
        return None

    # ── Telemetry ────────────────────────────────────────────────────────
    async def _get_state_async(self) -> dict:
        drone = self._drone
        if drone is None:
            raise AirSimUnavailable("not connected")
        pose = drone.get_ground_truth_pose()
        kin = drone.get_estimated_kinematics() or {}
        try:
            battery_state = drone.get_battery_state("Battery1") or {}
        except Exception:
            battery_state = {}
        lin = kin.get("linear_velocity", {}) or {}
        ang = kin.get("angular_velocity", {}) or {}
        pos = pose.translation
        # ProjectAirSim is NED: +z is down, altitude = -z
        alt = -float(pos.z)
        return {
            "lat": float(getattr(pos, "x", 0.0)),    # not real lat/lon — NED x/y as stand-in
            "lon": float(getattr(pos, "y", 0.0)),
            "alt": alt,
            "vx": float(lin.get("x", 0.0)),
            "vy": float(lin.get("y", 0.0)),
            "vz": float(lin.get("z", 0.0)),
            "yaw": float(ang.get("z", 0.0)),
            "battery": float(battery_state.get("battery_remaining", 100)),
            "landed_state": drone.get_landed_state().name if hasattr(drone, "get_landed_state") else "UNKNOWN",
        }

    def get_state(self) -> dict:
        return self._run(self._get_state_async(), timeout=3.0)

    # ── Camera ────────────────────────────────────────────────────────────
    async def _capture_frame_async(self) -> Optional[bytes]:
        from projectairsim.types import ImageType
        drone = self._drone
        if drone is None:
            raise AirSimUnavailable("not connected")
        images = drone.get_images(self.camera_id, [ImageType.SCENE])
        if not images or ImageType.SCENE not in images:
            return None
        payload = images[ImageType.SCENE]
        data = payload.get("data") if isinstance(payload, dict) else None
        if data is None:
            return None
        if isinstance(data, str):
            data = base64.b64decode(data)
        img = Image.open(io.BytesIO(data)).convert("RGB")
        # Re-encode as JPEG so the WebSocket stream size is predictable.
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=78)
        return buf.getvalue()

    def capture_frame(self) -> Optional[bytes]:
        try:
            return self._run(self._capture_frame_async(), timeout=2.0)
        except AirSimUnavailable:
            return None
        except Exception:
            return None

    # ── Commands ─────────────────────────────────────────────────────────
    def _do_cmd(self, action: str, **params) -> bool:
        """Dispatch a command synchronously, returning success."""
        drone = self._ensure_connected_sync()  # raises AirSimUnavailable
        try:
            if action == "arm":
                self._run(drone.enable_api_control(), timeout=2.0)
                self._run(drone.arm(), timeout=2.0)
                return True
            if action == "takeoff":
                self._run(drone.enable_api_control(), timeout=2.0)
                self._run(drone.arm(), timeout=2.0)
                self._run(drone.takeoff_async(timeout_sec=15), timeout=20.0)
                return True
            if action == "land":
                self._run(drone.land_async(), timeout=30.0)
                return True
            if action == "rtl":
                self._run(drone.go_home_async(), timeout=30.0)
                return True
            if action == "velocity":
                self._run(drone.enable_api_control(), timeout=2.0)
                vx = float(params.get("vx", 0))
                vy = float(params.get("vy", 0))
                vz = float(params.get("vz", 0))
                yaw = float(params.get("yaw", 0))
                if yaw != 0:
                    self._run(drone.rotate_by_yaw_rate_async(yaw, 0.15), timeout=2.0)
                self._run(
                    drone.move_by_velocity_body_frame_async(
                        vx=max(-10, min(10, vx)),
                        vy=max(-10, min(10, vy)),
                        vz=max(-5, min(5, vz)),
                        duration=0.2,
                    ),
                    timeout=2.0,
                )
                return True
            if action == "goto":
                # NED-space goto via geo_pose — assumes scene origin ≈ geo origin
                from projectairsim.types import GeoPoint
                gp = GeoPoint(
                    latitude=float(params.get("lat", 0)),
                    longitude=float(params.get("lon", 0)),
                    altitude=float(params.get("alt", 20)),
                )
                self._run(drone.move_to_geo_position_async(gp, 10.0, timeout_sec=120), timeout=125.0)
                return True
        except AirSimUnavailable:
            raise
        except Exception:
            return False
        return False

    def arm(self) -> bool:
        try:
            return self._do_cmd("arm")
        except AirSimUnavailable:
            return False

    def takeoff(self) -> bool:
        try:
            return self._do_cmd("takeoff")
        except AirSimUnavailable:
            return False

    def land(self) -> bool:
        try:
            return self._do_cmd("land")
        except AirSimUnavailable:
            return False

    def move_by_velocity(self, vx: float, vy: float, vz: float, yaw: float = 0.0) -> bool:
        try:
            return self._do_cmd("velocity", vx=vx, vy=vy, vz=vz, yaw=yaw)
        except AirSimUnavailable:
            return False

    def rtl(self) -> bool:
        try:
            return self._do_cmd("rtl")
        except AirSimUnavailable:
            return False

    def goto(self, lat: float, lon: float, alt: float) -> bool:
        try:
            return self._do_cmd("goto", lat=lat, lon=lon, alt=alt)
        except AirSimUnavailable:
            return False

    # ── Legacy compatibility shims (used by `routemanager.create_task`) ─
    def goto_gps(self, lat: float, lon: float, alt: float = 20.0):
        """Legacy entrypoint used by the rental route-task runner."""
        return self.goto(lat, lon, alt)

    def create_task(self, start_location: str, location: str, callback) -> None:
        """Legacy entrypoint — kept for backwards compat with routemanager."""
        start_lng, start_lat = start_location.split(",")
        dest_lng, dest_lat = location.split(",")
        start = [float(start_lat), float(start_lng)]
        end = [float(dest_lat), float(dest_lng)]
        routes = RouteManager.auto_plan_and_visualize(start, end)

        def _fly():
            try:
                self.takeoff()
                for leg in routes:
                    for p in leg:
                        self.goto_gps(p[0], p[1])
                self.land()
            finally:
                callback()

        t = threading.Thread(target=_fly, daemon=True)
        t.start()


# Singleton
drone_controller = DroneController()