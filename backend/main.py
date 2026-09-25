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

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "Multi-scenario drone training platform. Provides auth, six canonical "
        "training scenarios with per-user progress tracking, A* path planning "
        "with no-fly-zone avoidance, and an optional AirSim live-stream channel."
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