"""/api/scenarios — multi-scenario training metadata + progress."""
from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import get_current_user, get_current_user_optional
from ..core.security import decode_access_token
from ..domain.file import FileReader, FileWriter
from ..domain.scenario_manager import scenario_manager
from ..schemas.scenario import ProgressEntry, ProgressSave, Scenario, ScenarioList

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

PROGRESS_FILE = "progress.json"


def _load_progress() -> dict:
    return FileReader.read_json(PROGRESS_FILE)


def _save_progress(data: dict) -> None:
    FileWriter.write_json(PROGRESS_FILE, data)


def _phone_from_optional(user) -> str | None:
    return user["phone"] if user else None


@router.get("", response_model=ScenarioList)
def list_scenarios():
    items = scenario_manager.get_all()
    return ScenarioList(items=[Scenario(**s) for s in items])


@router.get("/{slug}", response_model=Scenario)
def get_scenario(slug: str):
    s = scenario_manager.get_by_slug(slug)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "场景不存在")
    return Scenario(**s)


@router.post("/{slug}/progress", response_model=ProgressEntry)
def save_progress(slug: str, req: ProgressSave, user=Depends(get_current_user)):
    s = scenario_manager.get_by_slug(slug)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "场景不存在")
    data = _load_progress()
    user_progress = data.setdefault(user["phone"], {})
    existing = user_progress.get(slug, {})
    entry = {
        "scenario_slug": slug,
        "attempts": existing.get("attempts", 0) + 1,
        "best_score": max(existing.get("best_score", 0), req.score),
        "best_duration_seconds": (
            existing.get("best_duration_seconds", 0)
            if existing.get("best_duration_seconds", 0) > 0
            else req.duration_seconds
        ),
        "completed": existing.get("completed", False) or req.completed,
        "last_played": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
    }
    user_progress[slug] = entry
    _save_progress(data)
    return ProgressEntry(**entry)


@router.get("/me/progress", response_model=list[ProgressEntry])
def my_progress(user=Depends(get_current_user)):
    data = _load_progress()
    user_progress = data.get(user["phone"], {})
    return [ProgressEntry(**v) for v in user_progress.values()]