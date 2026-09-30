"""One-shot migration: attach rule-based `tasks` to each scenario in db/data/scenarios.json.

Idempotent — re-running leaves already-migrated scenarios untouched. Existing
`objectives` / `objectives_zh` strings are preserved because the frontend still
renders them; `tasks` is the additive field the rule engine consumes.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "db", "data", "scenarios.json")

TASKS = {
    "urban": [
        {"id": "01", "label": "Take off from the rooftop pad", "kind": "altitude",
         "target": 20.0, "tolerance": 3.0, "points": 1},
        {"id": "02", "label": "Thread the tower gap at 60 m AGL", "kind": "reach",
         "waypoint": "WP_02", "radius": 8.0, "points": 2},
        {"id": "03", "label": "Hold the inspection waypoint for 8 s", "kind": "hold",
         "waypoint": "WP_03", "radius": 6.0, "seconds": 8.0, "points": 2},
    ],
    "forest": [
        {"id": "01", "label": "Climb to 8 m AGL", "kind": "altitude",
         "target": 8.0, "tolerance": 2.0, "points": 1},
        {"id": "02", "label": "Clear 2 m from the canopy", "kind": "clearance",
         "sensor": "DistanceFront", "min_distance": 2.0, "points": 2},
        {"id": "03", "label": "Cross three corridor gates in order", "kind": "sequence",
         "waypoints": ["WP_11", "WP_12", "WP_13"], "radius": 6.0, "points": 2},
    ],
    "indoor": [
        {"id": "01", "label": "Enter the atrium at 2 m", "kind": "altitude",
         "target": 2.0, "tolerance": 0.5, "points": 1},
        {"id": "02", "label": "Inspect 4 columns in sequence", "kind": "sequence",
         "waypoints": ["WP_21", "WP_22", "WP_23", "WP_24"], "radius": 1.0, "points": 3},
        {"id": "03", "label": "Land on the 60 cm pad", "kind": "reach",
         "waypoint": "WP_25", "radius": 0.6, "points": 2},
    ],
    "mountain": [
        {"id": "01", "label": "Reach 120 m AGL", "kind": "altitude",
         "target": 120.0, "tolerance": 10.0, "points": 1},
        {"id": "02", "label": "Trigger and recover RTH", "kind": "reach",
         "waypoint": "WP_32", "radius": 10.0, "points": 2},
        {"id": "03", "label": "Land on the slope, centred", "kind": "reach",
         "waypoint": "WP_33", "radius": 0.3, "points": 2},
    ],
    "coastal": [
        {"id": "01", "label": "Hold 5 m AGL over the swell", "kind": "altitude",
         "target": 5.0, "tolerance": 1.0, "points": 1},
        {"id": "02", "label": "Route around the maritime NFZs", "kind": "sequence",
         "waypoints": ["WP_41", "WP_42", "WP_43"], "radius": 8.0, "points": 2},
        {"id": "03", "label": "Photograph both navigation buoys", "kind": "sequence",
         "waypoints": ["WP_44", "WP_45"], "radius": 6.0, "points": 2},
    ],
    "industrial": [
        {"id": "01", "label": "Hold 1.5 m from the conductors", "kind": "clearance",
         "sensor": "DistanceFront", "min_distance": 1.5, "points": 2},
        {"id": "02", "label": "Tag 5 thermal anomalies in order", "kind": "sequence",
         "waypoints": ["WP_51", "WP_52", "WP_53", "WP_54", "WP_55"], "radius": 5.0, "points": 2},
        {"id": "03", "label": "Complete the substation point cloud", "kind": "reach",
         "waypoint": "WP_56", "radius": 5.0, "points": 1},
    ],
}


def main() -> int:
    if not os.path.exists(PATH):
        print(f"missing: {PATH}")
        return 1

    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for scenario in data.get("scenarios", []):
        slug = scenario.get("slug")
        tasks = TASKS.get(slug)
        if not tasks:
            continue
        if scenario.get("tasks"):
            print(f"  {slug}: already has tasks, skipped")
            continue
        scenario["tasks"] = tasks
        changed += 1
        print(f"  {slug}: +{len(tasks)} tasks")

    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"migrated {changed} scenario(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
