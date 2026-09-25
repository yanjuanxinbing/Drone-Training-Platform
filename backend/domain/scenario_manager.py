"""Six canonical training scenarios.

Each scenario defines: a name, difficulty, objectives, mission profile (start
position / target), evaluation criteria, and a default HUD theme color.
"""
from __future__ import annotations

from typing import Iterable
from .file import FileReader, FileWriter


DEFAULT_SCENARIOS = [
    {
        "id": "urban",
        "slug": "urban",
        "name": "Urban Skyline",
        "name_zh": "城市楼宇",
        "tagline": "Threading skyscrapers under GPS interference.",
        "tagline_zh": "高楼之间穿梭，应对 GPS 干扰与楼顶起降。",
        "difficulty": "Advanced",
        "duration_minutes": 18,
        "objectives": [
            "Take off from a rooftop pad without GPS lock.",
            "Thread a 1.5 m gap between two towers at 60 m AGL.",
            "Reach the inspection waypoint, hold for 8 s, return to home.",
        ],
        "objectives_zh": [
            "无 GPS 情况下从屋顶平台起飞。",
            "在 60 米高度穿越两栋楼之间的 1.5 米缝隙。",
            "抵达巡检航点，悬停 8 秒，返回机库。",
        ],
        "color": "#1A1A18",
        "accent": "#C9A47A",
        "icon": "urban",
        "metrics": {
            "max_altitude_m": 80,
            "wind_m_s": 9.0,
            "gps_quality": "degraded",
        },
    },
    {
        "id": "forest",
        "slug": "forest",
        "name": "Forest Corridor",
        "name_zh": "森林穿越",
        "tagline": "Attitude-mode flight through dense canopy.",
        "tagline_zh": "姿态模式下穿越茂密树冠，绕障与低空飞行。",
        "difficulty": "Intermediate",
        "duration_minutes": 12,
        "objectives": [
            "Maintain 2 m clearance from trees at 8 m AGL.",
            "Execute three lateral dodges in under 6 seconds each.",
            "Identify and avoid a moving obstacle (simulated paraglider).",
        ],
        "objectives_zh": [
            "在 8 米高度保持与树木 2 米的安全距离。",
            "6 秒内完成三次横向闪避。",
            "识别并避开移动障碍物（模拟滑翔伞）。",
        ],
        "color": "#1A1A18",
        "accent": "#8B6F4E",
        "icon": "forest",
        "metrics": {
            "max_altitude_m": 12,
            "wind_m_s": 4.0,
            "gps_quality": "good",
        },
    },
    {
        "id": "indoor",
        "slug": "indoor",
        "name": "Indoor Precision",
        "name_zh": "室内精准",
        "tagline": "GPS-denied inspection of an atrium.",
        "tagline_zh": "无 GPS 环境下对中庭进行精细巡检。",
        "difficulty": "Expert",
        "duration_minutes": 22,
        "objectives": [
            "Hold position within 5 cm using vision-only odometry.",
            "Inspect 4 marked columns in sequence, 0.3 m offset tolerated.",
            "Land on a 60 cm diameter pad without operator input.",
        ],
        "objectives_zh": [
            "纯视觉里程计保持位置误差 < 5 cm。",
            "依次巡检 4 根标记柱，允许 0.3 米偏移。",
            "全自动降落至 60 cm 直径平台。",
        ],
        "color": "#FFFFFF",
        "accent": "#6B6B68",
        "icon": "indoor",
        "metrics": {
            "max_altitude_m": 6,
            "wind_m_s": 0.0,
            "gps_quality": "denied",
        },
    },
    {
        "id": "mountain",
        "slug": "mountain",
        "name": "Alpine Ascent",
        "name_zh": "山地应急",
        "tagline": "High-altitude operations and emergency RTH.",
        "tagline_zh": "高海拔作业，应急返航与气压补偿。",
        "difficulty": "Advanced",
        "duration_minutes": 25,
        "objectives": [
            "Compensate barometric drift above 3500 m AGL.",
            "Trigger RTH on simulated link loss and recover.",
            "Land on a 1.5 m slope within 30 cm of center.",
        ],
        "objectives_zh": [
            "3500 米以上高度修正气压漂移。",
            "链路失联时启动自动返航并恢复。",
            "在 1.5 米斜坡上降落，偏差 < 30 cm。",
        ],
        "color": "#1A1A18",
        "accent": "#E8E8E5",
        "icon": "mountain",
        "metrics": {
            "max_altitude_m": 220,
            "wind_m_s": 14.0,
            "gps_quality": "good",
        },
    },
    {
        "id": "coastal",
        "slug": "coastal",
        "name": "Coastal Survey",
        "name_zh": "海岸巡检",
        "tagline": "Maritime corridor over salt and swell.",
        "tagline_zh": "跨海通道巡检，应对海事禁飞与盐雾。",
        "difficulty": "Intermediate",
        "duration_minutes": 16,
        "objectives": [
            "Plan a route around three maritime NFZs.",
            "Maintain 5 m AGL over swell up to 1.5 m.",
            "Photograph 2 navigation buoys with auto-framing.",
        ],
        "objectives_zh": [
            "绕过 3 处海事禁飞区规划航线。",
            "浪高 1.5 米情况下保持 5 米高度。",
            "自动取景拍摄 2 个航标浮筒。",
        ],
        "color": "#1A1A18",
        "accent": "#C9A47A",
        "icon": "coastal",
        "metrics": {
            "max_altitude_m": 25,
            "wind_m_s": 11.0,
            "gps_quality": "good",
        },
    },
    {
        "id": "industrial",
        "slug": "industrial",
        "name": "Industrial Grid",
        "name_zh": "工业巡检",
        "tagline": "Powerline and pipeline inspection.",
        "tagline_zh": "电网、管道、光伏阵列精细化巡检。",
        "difficulty": "Beginner",
        "duration_minutes": 14,
        "objectives": [
            "Maintain 1.5 m offset from energized conductors.",
            "Capture 5 thermal anomalies along a 1 km pipeline.",
            "Generate a point cloud of a substation in under 4 minutes.",
        ],
        "objectives_zh": [
            "与带电导线保持 1.5 米距离。",
            "在 1 公里管道上捕捉 5 处温度异常。",
            "4 分钟内完成变电站点云采集。",
        ],
        "color": "#1A1A18",
        "accent": "#6B6B68",
        "icon": "industrial",
        "metrics": {
            "max_altitude_m": 15,
            "wind_m_s": 5.0,
            "gps_quality": "good",
        },
    },
]


class ScenarioManager:
    FILE = "scenarios.json"

    def __init__(self):
        self.scenarios: list = []
        self._load_or_seed()

    def _load_or_seed(self):
        data = FileReader.read_json(self.FILE)
        if data.get("scenarios"):
            self.scenarios = data["scenarios"]
        else:
            self.scenarios = DEFAULT_SCENARIOS
            self.save()

    def get_all(self) -> list:
        return self.scenarios

    def get_by_slug(self, slug: str) -> dict | None:
        for s in self.scenarios:
            if s.get("slug") == slug or s.get("id") == slug:
                return s
        return None

    def save(self) -> None:
        FileWriter.write_json(self.FILE, {"scenarios": self.scenarios})


scenario_manager = ScenarioManager()