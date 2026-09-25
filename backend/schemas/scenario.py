"""Pydantic schemas — training scenarios."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class Scenario(BaseModel):
    id: str
    slug: str
    name: str
    name_zh: str
    tagline: str
    tagline_zh: str
    difficulty: str
    duration_minutes: int
    objectives: List[str]
    objectives_zh: List[str]
    color: str
    accent: str
    icon: str
    metrics: Dict


class ScenarioList(BaseModel):
    items: List[Scenario]


class ProgressEntry(BaseModel):
    scenario_slug: str
    attempts: int = 0
    best_score: int = 0
    best_duration_seconds: int = 0
    completed: bool = False
    last_played: Optional[str] = None


class ProgressSave(BaseModel):
    scenario_slug: str
    score: int
    duration_seconds: int
    completed: bool = True