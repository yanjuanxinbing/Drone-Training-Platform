"""Pydantic schemas — training scenarios."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TaskRule(BaseModel):
    """A machine-checkable training objective.

    `kind` selects the predicate in `mission.RULES`; the remaining fields are
    that predicate's parameters and are validated loosely so a new task kind
    can be added without a schema change.
    """

    id: str
    label: str = ""
    kind: str = "reach"
    points: float = 1.0
    waypoint: Optional[str] = None
    waypoints: List[str] = Field(default_factory=list)
    sensor: Optional[str] = None
    radius: Optional[float] = None
    seconds: Optional[float] = None
    target: Optional[float] = None
    tolerance: Optional[float] = None
    min_distance: Optional[float] = None


class Scenario(BaseModel):
    id: str
    slug: str
    name: str
    name_zh: str
    tagline: str
    tagline_zh: str
    difficulty: str
    duration_minutes: int
    objectives: List[str] = Field(default_factory=list)
    objectives_zh: List[str] = Field(default_factory=list)
    color: str
    accent: str
    icon: str
    metrics: Dict = Field(default_factory=dict)
    # Rule-based objectives. Optional so pre-migration scenarios still load.
    tasks: List[TaskRule] = Field(default_factory=list)


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