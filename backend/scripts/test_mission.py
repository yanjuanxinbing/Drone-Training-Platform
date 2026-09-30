"""Offline self-test for the mission rule engine.

No UE, no AirSim, no WebSocket — this drives MissionState with synthetic
telemetry so the rules can be verified before the simulator is even running.

Run from the project root:  python backend/scripts/test_mission.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.domain.mission import MissionState, build_rules  # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def drive(mission, samples, t0=1000.0, dt=0.1):
    """Feed telemetry through the engine, return the final status map."""
    t = t0
    for s in samples:
        mission.update(s, t)
        t += dt
    return mission.status


def test_reach():
    print("reach")
    wp = {"WP_01": {"x": 0.0, "y": 0.0, "z": 10.0}}
    rules = [{"id": "01", "label": "reach", "kind": "reach", "waypoint": "WP_01", "radius": 5.0}]
    m = MissionState(rules, wp)
    # Far away → active, not satisfied.
    m.update({"x": 100.0, "y": 0.0, "z": 0.0}, 1000.0)
    check("far target is active", m.status["01"] == "active", m.status)
    check("far target not satisfied", m.progress["01"] < 0.2, m.progress)
    # Fly in.
    m.update({"x": 1.0, "y": 0.0, "z": 10.0}, 1000.1)
    check("arrival satisfies", m.status["01"] == "satisfied", m.status)
    # Terminal: flying away must not un-satisfy or re-award.
    m.update({"x": 90.0, "y": 0.0, "z": 0.0}, 1000.2)
    check("stays satisfied after leaving", m.status["01"] == "satisfied", m.status)


def test_reach_missing_waypoint():
    print("reach / missing waypoint")
    rules = [{"id": "01", "label": "x", "kind": "reach", "waypoint": "WP_99", "radius": 5.0}]
    m = MissionState(rules, {})  # UE provided nothing
    m.update({"x": 0.0, "y": 0.0, "z": 0.0}, 1000.0)
    check("missing waypoint stays pending", m.status["01"] == "pending", m.status)
    check("missing waypoint gives no progress", m.progress["01"] == 0.0, m.progress)


def test_hold():
    print("hold")
    wp = {"WP_03": {"x": 0.0, "y": 0.0, "z": 20.0}}
    rules = [{"id": "03", "label": "hold", "kind": "hold", "waypoint": "WP_03",
              "radius": 6.0, "seconds": 8.0}]
    m = MissionState(rules, wp)
    on = {"x": 0.0, "y": 0.0, "z": 20.0}
    t = 2000.0
    for _ in range(40):  # 4 s of dwell, need 8 s
        m.update(on, t)
        t += 0.1
    check("partial dwell stays active", m.status["03"] == "active", m.status)
    check("partial dwell ~50%", 0.4 < m.progress["03"] < 0.6, m.progress)
    for _ in range(50):  # cross 8 s
        m.update(on, t)
        t += 0.1
    check("full dwell satisfied", m.status["03"] == "satisfied", m.status)

    # Leaving the zone resets progress.
    m2 = MissionState(rules, wp)
    t = 3000.0
    for _ in range(30):
        m2.update(on, t)
        t += 0.1
    m2.update({"x": 50.0, "y": 0.0, "z": 0.0}, t)
    check("leaving zone resets progress", m2.progress["03"] == 0.0, m2.progress)


def test_altitude():
    print("altitude")
    rules = [{"id": "01", "label": "climb", "kind": "altitude",
              "target": 20.0, "tolerance": 3.0}]
    m = MissionState(rules, {})
    m.update({"x": 0, "y": 0, "z": 0.0}, 1000.0)
    check("on ground is active", m.status["01"] == "active", m.status)
    m.update({"x": 0, "y": 0, "z": 19.0}, 1000.1)
    check("inside band satisfied", m.status["01"] == "satisfied", m.status)


def test_sequence():
    print("sequence")
    wp = {
        "WP_11": {"x": 0.0, "y": 0.0, "z": 0.0},
        "WP_12": {"x": 100.0, "y": 0.0, "z": 0.0},
        "WP_13": {"x": 200.0, "y": 0.0, "z": 0.0},
    }
    rules = [{"id": "02", "label": "gates", "kind": "sequence",
              "waypoints": ["WP_11", "WP_12", "WP_13"], "radius": 6.0}]
    m = MissionState(rules, wp)
    # Skipping ahead to the last gate must not count.
    m.update({"x": 200.0, "y": 0.0, "z": 0.0}, 1000.0)
    check("skipping ahead does not finish", m.status["02"] != "satisfied", m.status)
    # Visit in order.
    for i, x in enumerate([0.0, 100.0, 200.0]):
        m.update({"x": x, "y": 0.0, "z": 0.0}, 1001.0 + i)
    check("in-order visits satisfy", m.status["02"] == "satisfied", m.status)


def test_clearance():
    print("clearance")
    rules = [{"id": "01", "label": "safe", "kind": "clearance",
              "sensor": "DistanceFront", "min_distance": 2.0}]
    m = MissionState(rules, {})
    m.update({"x": 0, "y": 0, "z": 0}, 1000.0)
    check("no sensor reading stays pending", m.status["01"] == "pending", m.status)
    m.update({"x": 0, "y": 0, "z": 0, "sensor:DistanceFront": 5.0}, 1000.1)
    check("clear of obstacle satisfied", m.status["01"] == "satisfied", m.status)

    m2 = MissionState(rules, {})
    m2.update({"x": 0, "y": 0, "z": 0, "sensor:DistanceFront": 0.4}, 1000.0)
    check("too close stays active", m2.status["01"] == "active", m2.status)


def test_unknown_kind():
    print("unknown rule kind")
    m = MissionState([{"id": "09", "label": "?", "kind": "nonsense"}], {})
    m.update({"x": 0, "y": 0, "z": 0}, 1000.0)
    check("unknown kind fails closed", m.status["09"] == "failed", m.status)


def test_score_and_build():
    print("score / build_rules")
    rules = [
        {"id": "01", "kind": "altitude", "target": 10.0, "tolerance": 1.0, "points": 1},
        {"id": "02", "kind": "altitude", "target": 20.0, "tolerance": 1.0, "points": 3},
    ]
    m = MissionState(rules, {})
    m.update({"x": 0, "y": 0, "z": 10.0}, 1000.0)
    check("partial score reflects weights", 0 < m.score() < 100, m.score())
    check("not all satisfied yet", m.all_satisfied is False)
    m.update({"x": 0, "y": 0, "z": 20.0}, 1000.1)
    check("all satisfied", m.all_satisfied is True, m.status)
    check("full score", m.score() == 100, m.score())

    # Legacy scenarios (plain-string objectives) must still yield rules.
    legacy = build_rules({"objectives": ["Fly to the tower.", "Hold position."]})
    check("legacy objectives become rules", len(legacy) == 2, legacy)
    check("legacy rule has id", legacy[0]["id"] == "01", legacy[0])
    check("legacy rule kind is reach", legacy[0]["kind"] == "reach", legacy[0])
    # Explicit tasks take precedence.
    explicit = build_rules({"objectives": ["ignored"], "tasks": rules})
    check("tasks take precedence", len(explicit) == 2 and explicit[0]["id"] == "01", explicit)


def test_real_scenarios():
    print("real scenario data")
    from backend.domain.scenario_manager import scenario_manager
    for s in scenario_manager.get_all():
        rs = build_rules(s)
        # Task count is scenario-defined (`blocks` ships a single smoke-test
        # task), so assert the rules exist rather than a fixed length.
        check(f"{s['slug']}: rules built", len(rs) >= 1, rs)
        m = MissionState(rs, {})
        # A tick with empty telemetry must not raise on any real rule.
        try:
            m.update({"x": 0.0, "y": 0.0, "z": 0.0}, 1000.0)
            ok = True
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"      raised: {exc}")
        check(f"{s['slug']}: empty telemetry safe", ok)


def test_missing_ned_does_not_autocomplete():
    """Regression guard: the WS feeds the rules NED metres (nx/ny/nz). When
    AirSim drops those, every position rule must go pending — never read the
    absent value as 0 and "satisfy" the mission at the origin."""
    print("missing NED telemetry")
    wp = {"WP_01": {"x": 0.0, "y": 0.0, "z": 10.0}}
    rules = [
        {"id": "01", "label": "reach", "kind": "reach", "waypoint": "WP_01", "radius": 5.0},
        {"id": "02", "label": "hold", "kind": "hold", "waypoint": "WP_01", "radius": 5.0, "seconds": 1.0},
        {"id": "03", "label": "alt", "kind": "altitude", "target": 10.0, "tolerance": 1.0},
    ]
    # Exactly what sim.py builds when get_state() omits the NED fields.
    null_ned = {"x": None, "y": None, "z": None}
    m = MissionState(rules, wp)
    for _ in range(5):
        m.update(dict(null_ned), 1000.0)
        m.update(dict(null_ned), 1000.1)
    check("reach stays pending without NED", m.status["01"] == "pending", m.status)
    check("hold stays pending without NED", m.status["02"] == "pending", m.status)
    check("altitude stays pending without NED", m.status["03"] == "pending", m.status)
    check("nothing auto-satisfied", not m.all_satisfied, m.status)
    check("score stays 0", m.score() == 0, m.score())

    # And it must recover once NED returns.
    m.update({"x": 0.0, "y": 0.0, "z": 10.0}, 1001.0)
    check("reach completes when NED returns", m.status["01"] == "satisfied", m.status)


def test_blocks_smoke():
    """The `blocks` debug scenario is the end-to-end smoke path: one reach
    rule against WP_00, which is the actor the UE level actually contains."""
    print("blocks smoke (WP_00)")
    from backend.domain.scenario_manager import scenario_manager
    s = scenario_manager.get_by_slug("blocks")
    if s is None:
        print("  SKIP  blocks scenario not present")
        return
    rs = build_rules(s)
    check("blocks has one task", len(rs) == 1, rs)
    check("task targets WP_00", rs[0].get("waypoint") == "WP_00", rs[0])

    # Before the actor exists in the level, the task must not false-positive.
    m = MissionState(rs, {})
    m.update({"x": 0.0, "y": 0.0, "z": 0.0}, 1000.0)
    check("no waypoint => not satisfied", m.status["00"] != "satisfied", m.status)

    # With WP_00 discovered, arriving completes the mission.
    wp = {"WP_00": {"x": 50.0, "y": 0.0, "z": 10.0}}
    m2 = MissionState(rs, wp)
    m2.update({"x": 0.0, "y": 0.0, "z": 10.0}, 1000.0)
    check("far from WP_00 incomplete", not m2.all_satisfied, m2.status)
    m2.update({"x": 51.0, "y": 0.0, "z": 10.0}, 1000.1)
    check("arriving completes", m2.all_satisfied, m2.status)
    check("score is 100", m2.score() == 100, m2.score())


if __name__ == "__main__":
    for fn in [
        test_reach, test_reach_missing_waypoint, test_hold, test_altitude,
        test_sequence, test_clearance, test_unknown_kind, test_score_and_build,
        test_real_scenarios, test_missing_ned_does_not_autocomplete, test_blocks_smoke,
    ]:
        fn()
        print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("all mission rule tests passed")
