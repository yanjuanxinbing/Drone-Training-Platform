# Drone / Training Platform

A multi-scenario pilot training platform built from the original Flet-based
drone rental project. The UI framework has been replaced with **Next.js 15 +
React 19 + TypeScript** and the desktop runtime with **FastAPI** on Python
3.11+.

The homepage is a Swiss-grid, Bauhaus-minimalist stage with a full-width
horizontal hero reel of wide-angle indoor drone footage, leading into six
canonical training scenarios (Urban, Forest, Indoor, Mountain, Coastal,
Industrial), each with a Three.js browser simulator and an optional
AirSim live-stream bridge.

---

## Repository layout

```
Drone Training Platform/
├── backend/                FastAPI service (port 8000 by default)
│   ├── api/                REST + WebSocket endpoints
│   ├── core/               Settings, JWT, password hashing
│   ├── domain/             Framework-agnostic business logic
│   │   ├── airsim/         Vendored AirSim client
│   │   ├── config.py
│   │   ├── drone_controller.py
│   │   ├── drone_manager.py
│   │   ├── file.py
│   │   ├── route_manager.py
│   │   ├── scenario_manager.py
│   │   └── user_manager.py
│   ├── schemas/            Pydantic v2 request/response models
│   ├── main.py             ASGI entry
│   └── requirements.txt
├── frontend/               Next.js 15 + React 19 (port 3000 by default)
│   ├── src/app/            App Router pages
│   ├── src/components/     chrome · hero · sections · ui · three
│   ├── src/lib/            api · auth · types · scenarios
│   ├── src/styles/         tokens · reset · typography
│   └── public/videos/      Placeholder SVG posters + (optional) MP4 reels
├── db/
│   └── data/               JSON persistence (drones · users · scenarios · progress · config)
└── README.md
```

---

## Running it

### 1. Backend

```bash
cd "C:\Users\23080\Desktop\fun\Drone Training Platform"
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

- Interactive API docs at <http://localhost:8000/docs>
- Health check at `/healthz`
- Six scenarios seeded into `db/data/scenarios.json` on first launch.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

- Homepage at <http://localhost:3000>
- All routes are statically generated except `/drones/[id]`.

### 3. Optional — AirSim

When `AirSim` is running on `127.0.0.1:41451`, the backend's `/api/sim/status`
will report `airsim_available: true` and `/ws/sim/{slug}` will stream real
camera frames. Otherwise the simulator runs entirely in-browser via Three.js.

---

## Design system

The frontend uses six core tokens — `--ink`, `--paper`, `--ash-500`,
`--mist`, `--birch`, `--walnut` — over a strict 12-column Swiss grid with a
24 px gutter and an 8 px baseline. The display face is Inter Tight
(an open-source Helvetica-style alternative) paired with JetBrains Mono
for numerics, indices, and metadata. Decorative geometry (circles,
squares, triangles) is used sparingly as Bauhaus-period decoration.

Replace the placeholder posters under `frontend/public/videos/` with real
wide-angle indoor clips to bring the hero reel to life. The fallback grid
poster will continue to render if a video fails to load.

---

## Auth model

- Passwords are stored using **bcrypt** (passlib). Existing legacy SHA-256
  hashes (from the old Flet-era `users.json`) auto-upgrade to bcrypt on
  the first successful login.
- Sessions are JWT-based with a 7-day expiry. The token is stored in
  `localStorage` under `dtp.token`.
- The backend serves the API on port 8000 with permissive CORS for the
  frontend origin.

---

## Scenarios

| Slug       | Name (EN)        | Name (ZH)  | Difficulty   |
| ---------- | ---------------- | ---------- | ------------ |
| `urban`    | Urban Skyline    | 城市楼宇   | Advanced     |
| `forest`   | Forest Corridor  | 森林穿越   | Intermediate |
| `indoor`   | Indoor Precision | 室内精准   | Expert       |
| `mountain` | Alpine Ascent    | 山地应急   | Advanced     |
| `coastal`  | Coastal Survey   | 海岸巡检   | Intermediate |
| `industrial` | Industrial Grid | 工业巡检   | Beginner     |

Each scenario has both a typed Pydantic schema (served from
`backend/domain/scenario_manager.py`) and a parallel TypeScript constant
(`frontend/src/lib/scenarios.ts`). The latter is the source of truth for the
hero carousel index, the scenario grid, and the per-page static generation.

---

## Smoke-test script

```bash
# Backend
curl http://localhost:8000/healthz
curl http://localhost:8000/api/scenarios | head -c 200

# Frontend (after build)
curl -I http://localhost:3000/
curl -I http://localhost:3000/training/urban
curl -I http://localhost:3000/simulator/urban
```

End-to-end flow:

1. Visit `/` — hero reel autoplays; scenario grid is interactive.
2. Click any scenario → `/training/[slug]` — objectives, flight envelope,
   launch CTA.
3. Click **Launch simulator** → `/simulator/[slug]` — Three.js scene + HUD.
4. Press <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> to translate,
   <kbd>Space</kbd>/<kbd>Shift</kbd> to climb / descend, <kbd>Q</kbd>/<kbd>E</kbd>
   to yaw. Land & save records progress to your account.
5. Sign in via `/login` (or register at `/register`), then visit
   `/account/progress` for the per-scenario table.

---

## License & credits

- `frontend/public/videos/*.svg` — placeholders, free to replace.
- `backend/domain/airsim/` — vendored copy of the AirSim Python client.
- The remaining source is released under the same permissive terms as the
  original project.