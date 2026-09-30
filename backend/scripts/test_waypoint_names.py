"""Verify the waypoint-actor name matcher accepts real UE actor names.

UE users often name actors lowercase (`wp_00`); the manager must not
silently drop them. Run after editing the naming convention in the level.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.domain.waypoint_manager import _actor_key  # noqa: E402

CASES = [
    # (actor name as it appears in UE, expected key or None)
    ("wp_00", "WP_00"),        # the name currently in the level — lowercase
    ("WP_00", "WP_00"),
    ("WP_0", "WP_00"),         # single digit normalises
    ("Wp_00", "WP_00"),        # mixed case
    ("WP_URBAN_02", "WP_02"),  # scenario-scoped collapses to generic
    ("wp_urban_2", "WP_02"),
    ("WP_100", "WP_100"),      # >2 digits preserved
    # Must be rejected
    ("WP_00_3", None),         # UE dedupe suffix must NOT become waypoint 03
    ("WP_00_Pad", None),
    ("Waypoint00", None),
    ("wp_00a", None),
    ("BP_WP_00", None),
    ("WP_", None),
    ("00", None),
    ("", None),
]

if __name__ == "__main__":
    failures = []
    for raw, expected in CASES:
        got = _actor_key(raw)
        ok = got == expected
        print(f"  {'PASS' if ok else 'FAIL'}  {raw!r:16s} -> {got!r:8s} (expected {expected!r})")
        if not ok:
            failures.append(raw)
    if failures:
        print(f"\n{len(failures)} mismatch(es): {failures}")
        sys.exit(1)
    print("\nall actor-name cases pass")
