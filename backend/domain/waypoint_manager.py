"""UE waypoint bridge — pulls training waypoints out of the running level.

How it works
------------
Waypoints are authored **in UE**, not in this file. The convention is an
actor in the level whose name matches `WP_<NN>` (or `WP_<SLUG>_NN` when a
single level hosts several scenarios). The backend discovers them at mission
start via `simListSceneObjects` and reads each pose with `simGetObjectPose`.

Coordinates
-----------
Everything in this module and in `mission.py` is **NED metres, relative to
the vehicle's home/starting point**:

* `simGetObjectPose(actor)` → NED metres (AirSim applies
  `NedTransform::toGlobalNed()` server-side; the UE-up → NED-down flip and
  the world-origin → home shift are already done).
* `simGetGroundTruthKinematics()` → NED metres in the same frame (AirSim
  documents it as "the frame of the vehicle's starting point").

Both therefore compare directly, in metres, with no conversion anywhere.

The one thing that is *not* in this frame is `getMultirotorState().gps_location`,
a GeoPoint of absolute lat/lon/alt. It is still what the WS telemetry
protocol reports, so `drone_controller.get_state()` carries both: the legacy
`lat`/`lon`/`alt` for the frontend, plus `nx`/`ny`/`nz` in NED metres for
the rule engine. Never mix the two — comparing metres against degrees yields
distances of hundreds of metres that can never satisfy a 5 m rule.

Offline / no-UE mode
--------------------
`load()` never raises. If AirSim is unreachable, or the level contains no
matching actors, it returns whatever it can and lets the caller decide. A
mission with missing waypoints stays `pending` instead of crashing the flight
loop, which is what keeps the sim page usable while UE is still booting.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

log = logging.getLogger("waypoints")

# `WP_01`, `WP_001`, `WP_URBAN_02` …
#
# The optional middle group is a scenario tag (`WP_URBAN_02`), and the final
# group is the index. Both are anchored, and the tag is non-numeric so that a
# UE de-duplication suffix on a *repeated* actor name — `WP_00` copied twice
# becomes `WP_00_3` — is rejected outright rather than being misread as
# waypoint 03. A mis-mapped waypoint would silently judge against the wrong
# target, which is far worse than ignoring the actor.
WAYPOINT_RE = re.compile(r"^WP_(?:[A-Z]+_)?(\d+)$", re.IGNORECASE)

# Query sent to AirSim's `simListSceneObjects`.
#
# That API matches with UE's own regex flavour and is **case sensitive**: a
# level actor named `wp_00` (lowercase, as UE users naturally type it) is NOT
# returned by `WP_.*` — verified against a live Blocks.exe, where `WP_.*`
# matched 0 of 210 actors while `.*` showed `wp_00` present.
#
# `[Ww][Pp]` spells the case-insensitivity out with character classes, which
# every regex engine understands. An inline `(?i)` flag would be terser but
# depends on the engine honouring it mid-pattern, which UE's matcher is not
# guaranteed to do.
#
# The trailing `_.*` is required: without the underscore, the query would
# also pull in unrelated actors whose names merely start with "wp".
WAYPOINT_QUERY = "[Ww][Pp]_.*"


def _actor_key(name: str) -> Optional[str]:
    """Normalise an actor name to a stable waypoint key.

    `WP_03`, `WP_03_3`, and `WP_URBAN_03` all collapse to `WP_03` so that a
    rule can name its target the same way regardless of UE's auto-suffixing
    duplicated actors.
    """
    m = WAYPOINT_RE.match(name.strip())
    if not m:
        return None
    return f"WP_{int(m.group(1)):02d}"


class WaypointManager:
    """Discovers and caches the level's training waypoints."""

    def __init__(self, controller: Any):
        self.controller = controller
        self._cache: Dict[str, Dict[str, float]] = {}
        self._loaded = False

    @property
    def cache(self) -> Dict[str, Dict[str, float]]:
        return self._cache

    def load(self, scenario_slug: Optional[str] = None, force: bool = False) -> Dict[str, Dict[str, float]]:
        """Read waypoints from the live level. Returns the cache either way."""
        if self._loaded and not force:
            return self._cache

        self._cache = {}
        try:
            client = self.controller._ensure_connected()
        except Exception as exc:  # noqa: BLE001
            # AirSim not up yet — a normal condition while the level boots.
            log.info("waypoints: AirSim unavailable (%s)", exc)
            return self._cache

        try:
            actors = client.simListSceneObjects(WAYPOINT_QUERY)
        except Exception as exc:  # noqa: BLE001
            log.warning("waypoints: simListSceneObjects failed: %s", exc)
            return self._cache

        if not actors:
            log.info("waypoints: no %s actors matched %s",
                     WAYPOINT_QUERY, "level")
            return self._cache

        prefix = f"WP_{scenario_slug.upper()}_" if scenario_slug else ""
        generic: Dict[str, Dict[str, float]] = {}
        specific: Dict[str, Dict[str, float]] = {}

        for actor in actors or []:
            key = _actor_key(actor)
            if key is None:
                continue
            wp = self._read(client, actor)
            if not wp:
                continue
            # A scenario-specific actor (`WP_URBAN_02`) takes precedence over
            # the generic one (`WP_02`) when both exist, so a single level can
            # serve several training scenarios.
            if prefix and actor.upper().startswith(prefix):
                specific[key] = wp
            elif key not in generic:
                generic[key] = wp

        self._cache = {**generic, **specific}
        self._loaded = bool(self._cache)
        log.info("waypoints: %d found (%s)", len(self._cache), ", ".join(sorted(self._cache)) or "none")
        return self._cache

    def _read(self, client: Any, actor: str) -> Optional[Dict[str, float]]:
        try:
            pose = client.simGetObjectPose(actor)
        except Exception as exc:  # noqa: BLE001
            log.warning("waypoints: pose read failed for %s: %s", actor, exc)
            return None
        if pose is None:
            return None
        p = pose.position
        # NED metres, home-relative — the same frame as the drone's
        # `simGetGroundTruthKinematics` telemetry. Directly comparable.
        return {
            "x": float(p.x_val),
            "y": float(p.y_val),
            "z": float(p.z_val),
            "actor": actor,
        }


def describe(waypoints: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    """Payload for the /api/sim/waypoints debug endpoint (NED metres)."""
    return [
        {
            "id": key,
            "actor": wp.get("actor", key),
            "x": round(wp["x"], 3),
            "y": round(wp["y"], 3),
            "z": round(wp["z"], 3),
        }
        for key, wp in sorted(waypoints.items())
    ]
