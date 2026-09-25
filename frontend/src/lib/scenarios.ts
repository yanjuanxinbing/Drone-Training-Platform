// Local fallback scenario metadata. Mirrors `backend/domain/scenario_manager.py`
// and is used when the backend isn't reachable (e.g. demo / preview mode).

export const SCENARIOS = [
  {
    slug: "urban",
    name: "Urban Skyline",
    name_zh: "城市楼宇",
    tagline: "Threading skyscrapers under GPS interference.",
    tagline_zh: "高楼之间穿梭，应对 GPS 干扰与楼顶起降。",
    difficulty: "Advanced",
    duration_minutes: 18,
    objectives: [
      "Take off from a rooftop pad without GPS lock.",
      "Thread a 1.5 m gap between two towers at 60 m AGL.",
      "Reach the inspection waypoint, hold for 8 s, return to home.",
    ],
    objectives_zh: [
      "无 GPS 情况下从屋顶平台起飞。",
      "在 60 米高度穿越两栋楼之间的 1.5 米缝隙。",
      "抵达巡检航点，悬停 8 秒，返回机库。",
    ],
    metrics: {
      max_altitude_m: 80,
      wind_m_s: 9.0,
      gps_quality: "degraded",
    },
    color: "#1A1A18",
    accent: "#C9A47A",
    number: "01",
  },
  {
    slug: "forest",
    name: "Forest Corridor",
    name_zh: "森林穿越",
    tagline: "Attitude-mode flight through dense canopy.",
    tagline_zh: "姿态模式下穿越茂密树冠，绕障与低空飞行。",
    difficulty: "Intermediate",
    duration_minutes: 12,
    objectives: [
      "Maintain 2 m clearance from trees at 8 m AGL.",
      "Execute three lateral dodges in under 6 s each.",
      "Identify and avoid a moving obstacle.",
    ],
    objectives_zh: [
      "在 8 米高度保持与树木 2 米的安全距离。",
      "6 秒内完成三次横向闪避。",
      "识别并避开移动障碍物。",
    ],
    metrics: {
      max_altitude_m: 12,
      wind_m_s: 4.0,
      gps_quality: "good",
    },
    color: "#1A1A18",
    accent: "#8B6F4E",
    number: "02",
  },
  {
    slug: "indoor",
    name: "Indoor Precision",
    name_zh: "室内精准",
    tagline: "GPS-denied inspection of an atrium.",
    tagline_zh: "无 GPS 环境下对中庭进行精细巡检。",
    difficulty: "Expert",
    duration_minutes: 22,
    objectives: [
      "Hold position within 5 cm using vision-only odometry.",
      "Inspect 4 marked columns in sequence, 0.3 m offset tolerated.",
      "Land on a 60 cm diameter pad without operator input.",
    ],
    objectives_zh: [
      "纯视觉里程计保持位置误差 < 5 cm。",
      "依次巡检 4 根标记柱，允许 0.3 米偏移。",
      "全自动降落至 60 cm 直径平台。",
    ],
    metrics: {
      max_altitude_m: 6,
      wind_m_s: 0.0,
      gps_quality: "denied",
    },
    color: "#FFFFFF",
    accent: "#6B6B68",
    number: "03",
  },
  {
    slug: "mountain",
    name: "Alpine Ascent",
    name_zh: "山地应急",
    tagline: "High-altitude operations and emergency RTH.",
    tagline_zh: "高海拔作业，应急返航与气压补偿。",
    difficulty: "Advanced",
    duration_minutes: 25,
    objectives: [
      "Compensate barometric drift above 3500 m AGL.",
      "Trigger RTH on simulated link loss and recover.",
      "Land on a 1.5 m slope within 30 cm of center.",
    ],
    objectives_zh: [
      "3500 米以上高度修正气压漂移。",
      "链路失联时启动自动返航并恢复。",
      "在 1.5 米斜坡上降落，偏差 < 30 cm。",
    ],
    metrics: {
      max_altitude_m: 220,
      wind_m_s: 14.0,
      gps_quality: "good",
    },
    color: "#1A1A18",
    accent: "#E8E8E5",
    number: "04",
  },
  {
    slug: "coastal",
    name: "Coastal Survey",
    name_zh: "海岸巡检",
    tagline: "Maritime corridor over salt and swell.",
    tagline_zh: "跨海通道巡检，应对海事禁飞与盐雾。",
    difficulty: "Intermediate",
    duration_minutes: 16,
    objectives: [
      "Plan a route around three maritime NFZs.",
      "Maintain 5 m AGL over swell up to 1.5 m.",
      "Photograph 2 navigation buoys with auto-framing.",
    ],
    objectives_zh: [
      "绕过 3 处海事禁飞区规划航线。",
      "浪高 1.5 米情况下保持 5 米高度。",
      "自动取景拍摄 2 个航标浮筒。",
    ],
    metrics: {
      max_altitude_m: 25,
      wind_m_s: 11.0,
      gps_quality: "good",
    },
    color: "#1A1A18",
    accent: "#C9A47A",
    number: "05",
  },
  {
    slug: "industrial",
    name: "Industrial Grid",
    name_zh: "工业巡检",
    tagline: "Powerline and pipeline inspection.",
    tagline_zh: "电网、管道、光伏阵列精细化巡检。",
    difficulty: "Beginner",
    duration_minutes: 14,
    objectives: [
      "Maintain 1.5 m offset from energized conductors.",
      "Capture 5 thermal anomalies along a 1 km pipeline.",
      "Generate a point cloud of a substation in under 4 min.",
    ],
    objectives_zh: [
      "与带电导线保持 1.5 米距离。",
      "在 1 公里管道上捕捉 5 处温度异常。",
      "4 分钟内完成变电站点云采集。",
    ],
    metrics: {
      max_altitude_m: 15,
      wind_m_s: 5.0,
      gps_quality: "good",
    },
    color: "#1A1A18",
    accent: "#6B6B68",
    number: "06",
  },
] as const;

export type ScenarioMeta = (typeof SCENARIOS)[number] & {
  metrics?: Record<string, number | string>;
};

export function getScenario(slug: string): ScenarioMeta | undefined {
  return SCENARIOS.find((s) => s.slug === slug);
}

// ── Carousel slides ─────────────────────────────────────────────────────
export type HeroSlide = {
  id: string;
  title: string;
  caption: string;
  meta: string;
  video: string;
  poster: string;
};

export const HERO_SLIDES: HeroSlide[] = [
  {
    id: "warehouse",
    title: "WAREHOUSE — 01",
    caption: "Autonomous inventory sweep, 18 000 m² of rafters.",
    meta: "Indoor · 04:32 · DJI M30T",
    video: "/videos/indoor-warehouse.mp4",
    poster: "/videos/poster-warehouse.svg",
  },
  {
    id: "stage",
    title: "STAGE — 02",
    caption: "Multi-axis cinematography in a 38 m atrium.",
    meta: "Indoor · 06:18 · Skydio 2+",
    video: "/videos/indoor-stage.mp4",
    poster: "/videos/poster-stage.svg",
  },
  {
    id: "atrium",
    title: "ATRIUM — 03",
    caption: "Precision inspection at 0.3 m offset, vision-only.",
    meta: "Indoor · 03:51 · Autel EVO II",
    video: "/videos/indoor-atrium.mp4",
    poster: "/videos/poster-atrium.svg",
  },
  {
    id: "lab",
    title: "LAB — 04",
    caption: "Sub-centimetre SLAM mapping in a sterile lab.",
    meta: "Indoor · 09:12 · Mavic 3 Pro",
    video: "/videos/indoor-lab.mp4",
    poster: "/videos/poster-lab.svg",
  },
];