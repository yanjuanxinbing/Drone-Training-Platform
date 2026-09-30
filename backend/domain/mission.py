"""Mission rules — the training-objective rule engine.

Design note
-----------
Objective *judging* lives here in Python, never in UE. UE only supplies
waypoint geometry (see `waypoint_manager.py`); the tolerance, dwell time and
ordering rules below are data, so retuning a mission never requires a UE
re-cook.

A scenario carries a list of `TaskRule` objects. Each rule declares a `kind`
that selects a predicate, plus whatever parameters that predicate needs.
`MissionState.update()` folds a telemetry sample into per-task progress and
returns only the tasks whose observable state *changed* this tick, so the
WebSocket layer can emit a diff instead of 10 Hz of noise.

Coordinate frames
-----------------
Telemetry (`get_state`) reports **NED, in metres**: z is metres *above* the
home origin, so altitude AGL is simply `z`. Waypoints are stored the same
way, in UE-local NED. Both therefore compare directly — no conversion. See
`waypoint_manager.py` for how UE world coordinates are mapped into this frame.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

# Task lifecycle. `pending` → `active` → `satisfied` | `failed`.
PENDING = "pending"
ACTIVE = "active"
SATISFIED = "satisfied"
FAILED = "failed"

TERMINAL_STATES = (SATISFIED, FAILED)


def _has_position(t: Dict[str, float]) -> bool:
    """True when the sample carries a usable NED position.

    AirSim can omit the kinematics read, in which case the WS sends explicit
    `None` values. Every position-based rule must treat that as "unknown"
    rather than as the origin — a rule that reads None as 0 m would instantly
    satisfy a waypoint sitting at (0, 0, 0).
    """
    return t.get("x") is not None and t.get("y") is not None


def _dist3(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Euclidean distance in the NED metre frame.

    Returns inf when either side is missing a coordinate — a rule with no
    position must not read as "zero metres away", which would auto-satisfy
    every reach/hold task the moment AirSim dropped the NED fields.
    """
    for key in ("x", "y", "z"):
        if a.get(key) is None or b.get(key) is None:
            return math.inf
    return math.sqrt(
        (a["x"] - b["x"]) ** 2
        + (a["y"] - b["y"]) ** 2
        + (a.get("z", 0.0) - b.get("z", 0.0)) ** 2
    )


# ── Rule kinds ────────────────────────────────────────────────────────────
# Each predicate receives the accumulated context and mutates nothing; it
# returns (status, progress) where progress ∈ [0, 1].

RuleFn = Callable[["RuleContext"], "tuple[str, float]"]


@dataclass
class RuleContext:
    """Everything a predicate may look at, gathered once per tick."""

    telemetry: Dict[str, float]
    now: float
    dt: float
    waypoints: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Stateful bookkeeping shared across ticks — dwell timers for `hold`, the
    # visit cursor for `sequence`. These dicts are owned by the MissionState
    # and passed in by reference, so a predicate's writes survive to the next
    # tick. Creating them here as defaults would give every context its own
    # throwaway dict and silently reset progress on each call.
    dwell: Dict[str, float] = field(default_factory=dict)
    visited: Dict[str, int] = field(default_factory=dict)

    def target(self, name: str) -> Optional[Dict[str, float]]:
        """Look a waypoint up by key, or None when UE didn't supply it.

        A missing waypoint must not crash the mission — the rule simply can't
        be satisfied until the level provides the geometry.
        """
        return self.waypoints.get(name)


def rule_reach(ctx: RuleContext, r: Dict[str, Any]) -> tuple[str, float]:
    """Fly within `radius` (metres) of a named waypoint."""
    wp = ctx.target(r["waypoint"])
    if wp is None:
        return PENDING, 0.0
    d = _dist3(ctx.telemetry, wp)
    if math.isinf(d):
        # No position this tick (AirSim omitted NED). Stay pending — treating
        # "unknown" as "far away" would report the task as in progress.
        return PENDING, 0.0
    radius = float(r.get("radius", 5.0))
    if d <= radius:
        return SATISFIED, 1.0
    # Progress = how far along the approach we are, floored at 0. Uses a soft
    # knee so the bar moves visibly but never regresses to a fake completion.
    approach = max(0.0, min(1.0, 1.0 - (d - radius) / float(r.get("scale", 50.0))))
    return ACTIVE, approach

def rule_hold(ctx: RuleContext, r: Dict[str, Any]) -> tuple[str, float]:
    """Stay within `radius` for `seconds` without drifting out.

    Progress is wall-clock dwell, so it survives brief 10 Hz jitter but resets
    the moment the drone genuinely leaves the zone.
    """
    wp = ctx.target(r["waypoint"])
    if wp is None:
        return PENDING, 0.0
    d = _dist3(ctx.telemetry, wp)
    if math.isinf(d):
        return PENDING, 0.0
    radius = float(r.get("radius", 5.0))
    need = float(r.get("seconds", 8.0))
    if d > radius:
        ctx.dwell.pop(r["id"], None)
        return ACTIVE, 0.0
    held = ctx.dwell.get(r["id"], 0.0) + ctx.dt
    ctx.dwell[r["id"]] = held
    if held >= need:
        return SATISFIED, 1.0
    return ACTIVE, min(1.0, held / need)


def rule_altitude(ctx: RuleContext, r: Dict[str, Any]) -> tuple[str, float]:
    """Climb to a target altitude band, measured AGL."""
    target = float(r.get("target", 15.0))
    tol = float(r.get("tolerance", 2.0))
    alt = ctx.telemetry.get("z")
    if alt is None:
        return PENDING, 0.0
    alt = float(alt)
    if abs(alt - target) <= tol:
        return SATISFIED, 1.0
    delta = abs(alt - target) - tol
    span = max(1.0, float(r.get("scale", 20.0)))
    return ACTIVE, max(0.0, min(1.0, 1.0 - delta / span))


def rule_sequence(ctx: RuleContext, r: Dict[str, Any]) -> tuple[str, float]:
    """Visit an ordered list of waypoints.

    Order matters: the drone must reach waypoint 1, then 2, and so on. Progress
    is the fraction of the list already cleared, which keeps the front-end bar
    honest on a five-stop inspection run.
    """
    names: List[str] = list(r.get("waypoints", []))
    if not names:
        return PENDING, 0.0
    # No position this tick — stay pending rather than reporting progress
    # toward a target we cannot measure against.
    if not _has_position(ctx.telemetry):
        return PENDING, 0.0
    radius = float(r.get("radius", 5.0))
    idx = ctx.visited.get(r["id"], 0)
    while idx < len(names):
        wp = ctx.target(names[idx])
        if wp is not None and _dist3(ctx.telemetry, wp) <= radius:
            idx += 1
            continue
        break
    ctx.visited[r["id"]] = idx
    if idx >= len(names):
        return SATISFIED, 1.0
    return ACTIVE, idx / len(names)


def rule_clearance(ctx: RuleContext, r: Dict[str, Any]) -> tuple[str, float]:
    """Hold a safe distance from a named obstacle actor.

    `distance` comes from the drone's own distance sensors and is supplied by
    the caller as `sensor:<NAME>` in `telemetry` — see `sim.py`, which folds
    the closest reading into the sample. Without a sensor reading the rule
    stays pending rather than silently passing.
    """
    key = f"sensor:{r.get('sensor', 'DistanceFront')}"
    dist = ctx.telemetry.get(key)
    if dist is None:
        return PENDING, 0.0
    safe = float(r.get("min_distance", 2.0))
    if dist >= safe:
        return SATISFIED, 1.0
    return ACTIVE, max(0.0, min(1.0, dist / max(0.01, safe)))


RULES: Dict[str, RuleFn] = {
    "reach": rule_reach,
    "hold": rule_hold,
    "altitude": rule_altitude,
    "sequence": rule_sequence,
    "clearance": rule_clearance,
}


# ── Mission state ─────────────────────────────────────────────────────────


class MissionState:
    """Per-connection mission run.

    One instance lives for the lifetime of a simulator WebSocket. `update()`
    is called on every 10 Hz telemetry tick and returns the list of tasks
    whose status or progress moved, which is exactly what the client needs in
    order to update its objective checklist.
    """

    def __init__(self, rules: Iterable[Dict[str, Any]], waypoints: Optional[Dict[str, Dict[str, float]]] = None):
        self.rules = [dict(r) for r in rules]
        self.waypoints = dict(waypoints or {})
        self.status: Dict[str, str] = {r["id"]: PENDING for r in self.rules}
        self.progress: Dict[str, float] = {r["id"]: 0.0 for r in self.rules}
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self._last: Optional[float] = None
        # Per-run scratch mutated by predicates (dwell timers, sequence
        # cursors). Instance-level, never class-level: two concurrent
        # simulator connections must not share them.
        self.dwell: Dict[str, float] = {}
        self.visited: Dict[str, int] = {}
        # Context handed to predicates, rebuilt in place each tick so the
        # engine doesn't allocate at 10 Hz.
        self.ctx: RuleContext = RuleContext(telemetry={}, now=0.0, dt=0.0)

    # ── Query ────────────────────────────────────────────────────────────
    @property
    def all_satisfied(self) -> bool:
        return bool(self.status) and all(s == SATISFIED for s in self.status.values())

    def score(self) -> int:
        """0–100, weighted by each task's `points` (default 1)."""
        if not self.rules:
            return 0
        total = sum(float(r.get("points", 1)) for r in self.rules)
        if total <= 0:
            return 0
        got = sum(
            float(r.get("points", 1)) * self.progress.get(r["id"], 0.0) for r in self.rules
        )
        return int(round(100.0 * got / total))

    def snapshot(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": r["id"],
                "label": r.get("label", r["id"]),
                "status": self.status.get(r["id"], PENDING),
                "progress": round(self.progress.get(r["id"], 0.0), 3),
            }
            for r in self.rules
        ]

    # ── Evaluation ───────────────────────────────────────────────────────
    def update(self, telemetry: Dict[str, float], now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Fold one telemetry sample in; return changed tasks.

        Terminal tasks are frozen: once a task is satisfied or failed it keeps
        its verdict for the whole run. That is what stops a task from being
        re-satisfied on a later pass and re-awarding points to the client.
        """
        now = time.time() if now is None else now
        if self.started_at is None:
            self.started_at = now
        dt = 0.1 if self._last is None else max(0.0, min(1.0, now - self._last))
        self._last = now

        changed: List[Dict[str, Any]] = []
        for rule in self.rules:
            rid = rule["id"]
            if self.status.get(rid) in TERMINAL_STATES:
                continue
            fn = RULES.get(rule.get("kind", ""))
            if fn is None:
                # An unknown kind can never pass; leaving it pending is safer
                # than granting progress for a rule we don't understand.
                self.status[rid] = FAILED
                changed.append(self._view(rule))
                continue

            ctx = self.ctx
            ctx.telemetry = telemetry
            ctx.now = now
            ctx.dt = dt
            ctx.waypoints = self.waypoints
            # Bind the stateful scratch by reference so dwell timers and
            # sequence cursors accumulate across ticks.
            ctx.dwell = self.dwell
            ctx.visited = self.visited
            try:
                status, progress = fn(ctx, rule)
            except Exception:
                # A malformed rule must not take down the flight loop.
                status, progress = PENDING, self.progress.get(rid, 0.0)

            progress = max(0.0, min(1.0, float(progress)))
            prev_status = self.status.get(rid, PENDING)
            prev_progress = self.progress.get(rid, 0.0)
            self.status[rid] = status
            self.progress[rid] = progress
            if status != prev_status or abs(progress - prev_progress) >= 0.01:
                changed.append(self._view(rule))

        if self.all_satisfied and self.finished_at is None:
            self.finished_at = now
        return changed

    def _view(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        rid = rule["id"]
        return {
            "id": rid,
            "label": rule.get("label", rid),
            "status": self.status[rid],
            "progress": round(self.progress[rid], 3),
        }


def build_rules(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pull task rules off a scenario record.

    Scenarios written before the rule engine carry `objectives` as bare
    strings. Those are turned into inert `reach` rules with no waypoint, which
    render correctly and simply never auto-satisfy — a soft upgrade rather
    than a hard break.
    """
    tasks = scenario.get("tasks")
    if tasks:
        return [dict(t) for t in tasks]

    out: List[Dict[str, Any]] = []
    objectives = scenario.get("objectives", [])
    for i, obj in enumerate(objectives, start=1):
        if isinstance(obj, dict):
            rule = dict(obj)
            rule.setdefault("id", f"{i:02d}")
            out.append(rule)
        else:
            out.append(
                {
                    "id": f"{i:02d}",
                    "label": obj,
                    "kind": "reach",
                    "waypoint": f"WP_{i:02d}",
                    "radius": 5.0,
                }
            )
    return out
