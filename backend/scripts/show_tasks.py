"""Show which waypoints each scenario's task rules actually reference.

Useful when deciding which WP_ actors to place in the UE level.
Run: python backend/scripts/show_tasks.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "db", "data", "scenarios.json")

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

all_refs = []
for s in data.get("scenarios", []):
    print(f"\n[{s['slug']}]  {s['name']}")
    for t in s.get("tasks", []):
        refs = []
        if t.get("waypoint"):
            refs.append(t["waypoint"])
        refs += t.get("waypoints", [])
        if refs:
            all_refs.extend(refs)
        shown = ", ".join(refs) if refs else "-- no waypoint needed --"
        extra = ""
        if t["kind"] == "reach":
            extra = f"  radius={t.get('radius')}m"
        elif t["kind"] == "hold":
            extra = f"  radius={t.get('radius')}m for {t.get('seconds')}s"
        elif t["kind"] == "sequence":
            extra = f"  radius={t.get('radius')}m"
        elif t["kind"] == "altitude":
            extra = f"  target={t.get('target')}m ±{t.get('tolerance')}m"
        elif t["kind"] == "clearance":
            extra = f"  sensor={t.get('sensor')} ≥{t.get('min_distance')}m"
        print(f"  {t['id']}  {t['kind']:9s}  {shown}{extra}")
        print(f"       {t.get('label','')}")

print(f"\n{'='*60}")
print("All waypoint names referenced across all scenarios:")
for w in sorted(set(all_refs)):
    print(f"  {w}")
print(f"Total distinct: {len(set(all_refs))}")
