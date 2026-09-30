"""End-to-end smoke test: connect to a running backend's sim WebSocket and
print what the server sends, so the objective protocol can be eyeballed.

Usage:
    python -m uvicorn backend.main:app --port 8099
    python backend/scripts/probe_ws.py [slug] [ws://host:port]
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import websockets  # noqa: E402


async def main(slug: str, base: str):
    url = f"{base.rstrip('/')}/api/sim/ws/{slug}"
    print(f"connecting to {url}")
    async with websockets.connect(url) as ws:
        for i in range(3):
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(raw)
            kind = msg.get("type")
            if kind == "hello":
                print(f"  hello  airsim={msg.get('airsim_available')} "
                      f"waypoints={msg.get('waypoints')} "
                      f"objectives={len(msg.get('objectives', []))}")
                for o in msg.get("objectives", []):
                    print(f"      {o['id']} [{o['status']}] "
                          f"prog={o['progress']}  {o['label']}")
            elif kind == "objective":
                print(f"  objective  {msg.get('id')} -> {msg.get('status')} "
                      f"({msg.get('progress')})")
            elif kind == "score":
                print(f"  score  {msg.get('score')}  completed={msg.get('completed')}")
            elif kind == "no_signal":
                print("  no_signal  (UE not running — objectives still tracked)")
            else:
                print(f"  {kind}  {msg}")


if __name__ == "__main__":
    s = sys.argv[1] if len(sys.argv) > 1 else "urban"
    b = sys.argv[2] if len(sys.argv) > 2 else "ws://127.0.0.1:8099"
    asyncio.run(main(s, b))
