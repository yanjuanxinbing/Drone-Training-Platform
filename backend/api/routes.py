"""/api/routes — path planning with no-fly zone avoidance."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..domain.route_manager import RouteManager
from ..schemas.routes import RoutePlanRequest

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.post("/plan")
def plan(req: RoutePlanRequest):
    try:
        start_lng, start_lat = map(float, req.start.split(","))
        end_lng, end_lat = map(float, req.end.split(","))
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "坐标格式应为 'lng,lat'")

    try:
        result = RouteManager.plan_route((start_lat, start_lng), (end_lat, end_lng))
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"路径规划失败：{exc}")


@router.get("/no-fly-zones")
def nfz(ltlat: float, ltlng: float, rblat: float, rblng: float):
    try:
        return {"zones": RouteManager.get_nfz(ltlat, ltlng, rblat, rblng)}
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"禁飞区查询失败：{exc}")