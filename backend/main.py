"""Drone Training Platform — FastAPI entry point.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import auth, routes, scenarios, sim, users
from .core.settings import settings
from .domain.drone_controller import drone_controller

# Configure the ProjectAirSim singleton with settings-derived defaults.
drone_controller.host = settings.projectairsim_host
drone_controller.port_topics = settings.projectairsim_port_topics
drone_controller.port_services = settings.projectairsim_port_services
drone_controller.scene_config = settings.projectairsim_scene
drone_controller.drone_name = settings.projectairsim_drone
drone_controller.camera_id = settings.projectairsim_camera

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "Multi-scenario drone training platform. Provides auth, six canonical "
        "training scenarios with per-user progress tracking, A* path planning "
        "with no-fly-zone avoidance, and an optional ProjectAirSim (UE 5.7) "
        "live-stream channel."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(routes.router)
app.include_router(scenarios.router)
app.include_router(sim.router)


@app.get("/")
def root():
    return {
        "name": settings.project_name,
        "version": settings.version,
        "docs": "/docs",
        "scenarios": "/api/scenarios",
    }


@app.get("/healthz")
def healthz():
    return {"ok": True}


# Optional: serve static media (avatars) under /media.
ROOT_DIR = Path(__file__).resolve().parent.parent
media_dir = ROOT_DIR / "db" / "img"
if media_dir.exists():
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")