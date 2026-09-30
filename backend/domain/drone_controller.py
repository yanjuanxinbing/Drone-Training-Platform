"""Drone controller. Wraps AirSim for the optional simulator backend.

Connection to AirSim is established lazily — the controller can be imported
and instantiated without an AirSim server running. Methods that actually
need AirSim raise a clear error if the connection is unavailable.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from . import airsim
from .airsim import DrivetrainType, YawMode

log = logging.getLogger("drone")

class AirSimUnavailable(RuntimeError):
    pass


class DroneController:
    def __init__(self, ip: str = "127.0.0.1", port: int = 41451):
        self.ip = ip
        self.port = port
        self.client: Optional[airsim.MultirotorClient] = None
        self.alt = 0.0
        self._connect_attempts = 0

    def _ensure_connected(self) -> airsim.MultirotorClient:
        if self.client is not None:
            return self.client
        try:
            client = airsim.MultirotorClient(ip=self.ip, port=self.port)
            client.confirmConnection()
            client.enableApiControl(True)
            client.armDisarm(True)
            self.client = client
            return client
        except Exception as exc:  # noqa: BLE001
            self._connect_attempts += 1
            raise AirSimUnavailable(
                f"AirSim not reachable at {self.ip}:{self.port}: {exc}"
            ) from exc

    def is_available(self) -> bool:
        try:
            self._ensure_connected()
            return True
        except AirSimUnavailable:
            return False

    def get_distance(self, sensor_name: str) -> float:
        client = self._ensure_connected()
        data = client.getDistanceSensorData(distance_sensor_name=sensor_name)
        return data.distance

    def takeoff(self, altitude: float = 15.0, timeout: float = 20.0) -> None:
        client = self._ensure_connected()
        print(f"[Takeoff] 起飞中，目标高度 {altitude}m ...")
        client.takeoffAsync(timeout_sec=timeout).result()
        if altitude > 3.0:
            client.moveToZAsync(-altitude, velocity=3.0).result()
        print(f"[Takeoff] 已到达 {altitude}m")
        self.alt = self.get_state()["alt"]

    def goto(self, lat: float, lon: float, timeout: float = 3600.0) -> None:
        client = self._ensure_connected()
        print(f"[Goto] 飞往 ({lat:.6f}, {lon:.6f})，高度 {self.alt}m ...")
        fly_task = client.moveToGPSAsync(
            latitude=lat, longitude=lon, altitude=self.alt, velocity=15.0,
            timeout_sec=timeout,
            drivetrain=DrivetrainType.ForwardOnly,
            yaw_mode=YawMode(False, 0),
        )
        while True:
            if fly_task.done():
                print("[Goto] 已到达目标点")
                break
            distance_front = self.get_distance("DistanceFront")
            distance_left = self.get_distance("DistanceLeft")
            distance_right = self.get_distance("DistanceRight")
            distance_down = self.get_distance("DistanceDown")

            if distance_front < 15.0:
                print(f"⚠️ [Obstacle] 前方障碍物 {distance_front:.2f}m")
                fly_task.cancel()
                client.hoverAsync().result()
                vx, vy, vz = 0.0, 0.0, 0.0
                if distance_left > 25.0:
                    vy = -2.0
                elif distance_right > 25.0:
                    vy = 2.0
                client.moveByVelocityAsync(vx, vy, vz, duration=1.5).result()
                self.alt = self.get_state()["alt"]
                fly_task = client.moveToGPSAsync(
                    latitude=lat, longitude=lon, altitude=self.alt, velocity=15.0,
                    timeout_sec=timeout,
                    drivetrain=DrivetrainType.ForwardOnly,
                    yaw_mode=YawMode(False, 0),
                )
            elif distance_down < 5:
                print(f"⚠️ [Ground] 防触底 {distance_down:.2f}m")
                client.moveByVelocityAsync(0.0, 0.0, -2.0, duration=1.5).result()
                self.alt = self.get_state()["alt"]
                fly_task = client.moveToGPSAsync(
                    latitude=lat, longitude=lon, altitude=self.alt, velocity=15.0,
                    timeout_sec=timeout,
                    drivetrain=DrivetrainType.ForwardOnly,
                    yaw_mode=YawMode(False, 0),
                )
            else:
                self.alt = self.get_state()["alt"]
            time.sleep(0.1)

    def land(self, timeout: float = 60.0) -> None:
        client = self._ensure_connected()
        print("[Land] 开始智能降落程序...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            dist_down = self.get_distance("DistanceDown")
            print(f"[Land] 当前相对地面高度: {dist_down:.2f}m")
            if dist_down > 1.5:
                client.moveByVelocityAsync(0.0, 0.0, 1.5, duration=0.2).result()
            elif dist_down > 0.5:
                client.moveByVelocityAsync(0.0, 0.0, 0.3, duration=0.2).result()
            else:
                break
            time.sleep(0.1)
        client.hoverAsync().result()
        time.sleep(0.5)

    def get_state(self) -> dict:
        """Drone telemetry for the WS stream and the rule engine.

        Two coordinate frames are reported side by side, because callers need
        different ones:

        * `lat`/`lon`/`alt` — absolute GeoPoint, what the frontend displays.
        * `nx`/`ny`/`nz`    — NED metres relative to the home/starting point,
          the frame `simGetObjectPose` returns waypoints in. The mission rule
          engine compares *these*. Never compare `lat`/`lon` against waypoint
          x/y: mixing degrees with metres yields distances of hundreds of
          metres that can never satisfy a metre-scale rule.

        `simGetGroundTruthKinematics` is the NED source — AirSim documents it
        as "the frame of the vehicle's starting point", the same frame the
        waypoint side uses. If it is unavailable the NED fields are None and
        position-based rules stay `pending` rather than judging against zeros.
        """
        client = self._ensure_connected()
        state = client.getMultirotorState()
        gps = state.gps_location
        vel = state.kinematics_estimated.linear_velocity

        ned = None
        try:
            kin = client.simGetGroundTruthKinematics()
            p = kin.position
            ned = (float(p.x_val), float(p.y_val), float(p.z_val))
        except Exception:  # noqa: BLE001
            log.warning("simGetGroundTruthKinematics unavailable; NED omitted")

        out = {
            "lat": gps.latitude,
            "lon": gps.longitude,
            "alt": gps.altitude,
            "vx": vel.x_val,
            "vy": vel.y_val,
            "vz": vel.z_val,
        }
        if ned is not None:
            out["nx"], out["ny"], out["nz"] = ned
        return out

    def capture_frame(self) -> Optional[bytes]:
        """Grab a single JPEG-encoded scene frame from AirSim, or None."""
        try:
            client = self._ensure_connected()
            raw = client.simGetImage("0", airsim.ImageType.Scene)
            if raw:
                return raw
        except AirSimUnavailable:
            return None
        return None

    def close(self) -> None:
        if self.client is not None:
            try:
                self.client.enableApiControl(False)
            except Exception:
                pass

    def fly_task(self, routes, callback) -> None:
        for route in routes:
            self.takeoff()
            for p in route:
                self.goto(p[0], p[1])
            self.land()
        self.close()
        callback()


# Singleton
drone_controller = DroneController()