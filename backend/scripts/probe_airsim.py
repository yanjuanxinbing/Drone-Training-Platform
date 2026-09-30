"""Direct AirSim probe — read waypoints straight from UE, no backend needed.

Separates "did UE ship the WP_00 actor?" from "is the backend wired up?".
Run with the packaged Blocks.exe already running:
    python backend/scripts/probe_airsim.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.domain.airsim import MultirotorClient  # noqa: E402


def main() -> int:
    try:
        c = MultirotorClient(ip="127.0.0.1", port=41451)
        c.confirmConnection()
    except Exception as exc:  # noqa: BLE001
        print(f"AirSim not reachable: {exc}")
        return 1

    print("connected to AirSim\n")

    try:
        actors = c.simListSceneObjects("WP_.*")
        print(f"simListSceneObjects('WP_.*') -> {len(actors)} match(es)")
        for a in actors[:20]:
            print(f"    {a}")
    except Exception as exc:  # noqa: BLE001
        print(f"simListSceneObjects failed: {exc}")
        return 1

    if not actors:
        print("\nNo WP_ actors found in the level.")
        print("  Either the actor is named differently, or this build was")
        print("  cooked before the level was saved with it.")
        try:
            allobjs = c.simListSceneObjects(".*")
            print(f"\n  scene has {len(allobjs)} objects; sample:")
            for a in allobjs[:30]:
                print(f"    {a}")
        except Exception:  # noqa: BLE001
            pass
        return 2

    print()
    for a in actors[:10]:
        try:
            p = c.simGetObjectPose(a)
            pos = p.position
            print(f"  {a}: x={pos.x_val:.2f} y={pos.y_val:.2f} z={pos.z_val:.2f}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {a}: pose read FAILED ({exc})")

    try:
        st = c.getMultirotorState()
        g = st.gps_location
        print(f"\ndrone now: lat={g.latitude:.6f} lon={g.longitude:.6f} alt={g.altitude:.2f}")
    except Exception as exc:  # noqa: BLE001
        print(f"\ndrone state unavailable: {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
