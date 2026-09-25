"""Pydantic schemas — path planning & no-fly zones."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RoutePlanRequest(BaseModel):
    start: str = Field(..., description="lng,lat")
    end: str = Field(..., description="lng,lat")