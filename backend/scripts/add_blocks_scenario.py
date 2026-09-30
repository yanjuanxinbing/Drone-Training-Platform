"""Add the `blocks` debug scenario to db/data/scenarios.json.

Mirrors the `Blocks · Debug` entry that already exists in the frontend
(`frontend/src/lib/scenarios.ts`) but was never added to the backend, so
`/simulator/blocks` had no server-side scenario to load.

Deliberately minimal: one `reach` task against `WP_00`, the smallest thing
that exercises the whole chain — AirSim discovery → coordinate mapping →
rule evaluation → objective messages.

Idempotent: a no-op when the scenario is already present.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "db", "data", "scenarios.json")

BLOCKS = {
    "id": "blocks",
    "slug": "blocks",
    "name": "Blocks · Debug",
    "name_zh": "方块场 · 调试",
    "tagline": "AirSim Blocks environment for bridge & video-stream debugging.",
    "tagline_zh": "AirSim Blocks 调试环境，用于测试桥接与图传链路。",
    "difficulty": "Debug",
    "duration_minutes": 0,
    "objectives": [
        "Fly to waypoint WP_00.",
    ],
    "objectives_zh": [
        "飞抵航点 WP_00。",
    ],
    "color": "#0E0E0C",
    "accent": "#4ECDC4",
    "icon": "blocks",
    "metrics": {
        "max_altitude_m": 50,
        "wind_m_s": 0.0,
        "gps_quality": "debug",
    },
    # The single smoke-test task. Generous radius so the very first flight
    # completes it — tighten once the chain is proven end to end.
    "tasks": [
        {
            "id": "00",
            "label": "Fly to WP_00",
            "kind": "reach",
            "waypoint": "WP_00",
            "radius": 5.0,
            "points": 1,
        }
    ],
}


def main() -> int:
    if not os.path.exists(PATH):
        print(f"missing: {PATH}")
        return 1

    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data.setdefault("scenarios", [])
    for s in scenarios:
        if s.get("slug") == BLOCKS["slug"]:
            print("  blocks: already present, skipped")
            return 0

    scenarios.append(BLOCKS)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(f"  blocks: added ({len(scenarios)} scenarios total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
