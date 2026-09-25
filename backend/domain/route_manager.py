import heapq
import folium
import requests
from eviltransform import wgs2gcj
from geopy.distance import geodesic

HOMES = [
    (28.162727186151248, 112.93179176701715),
    (28.197838178991322, 112.93394799785588),
    (28.070362744025946, 113.00032241871332),
    (28.372755526429163, 112.9018843955385)
]

START = 28.158683, 112.935477

class RouteManager:
    @staticmethod
    def get_nfz(ltlat, ltlng, rblat, rblng):
        url = "https://flysafe-api.dji.com/api/qep/geo/feedback/areas/in_rectangle"
        params = {
            "ltlat": ltlat, "ltlng": ltlng,
            "rblat": rblat, "rblng": rblng,
            "zones_mode": "flysafe_website",
            "drone": "dji-mavic-3",
            "level": "2"
        }

        resp = requests.get(url, params=params)
        data = resp.json()

        result = []

        for area in data["data"]["areas"]:
            area["lat"], area["lng"] = wgs2gcj(area["lat"], area["lng"])
            base = {
                "id": area["area_id"],
                "name": area["name"],
                "level": area["level"],
                "shape": area["shape"],
            }
            shape = area["shape"]

            if shape == 0:
                base["geometry"] = {
                    "type": "circle",
                    "center": (area["lat"], area["lng"]),
                    "radius": area["radius"],
                }
                result.append(base)
            elif shape == 1:
                pts = area.get("polygon_points")

                if len(pts) > 1:
                    print("未处理的列表格式")

                base["geometry"] = {
                    "type": "polygon",
                    "points": [wgs2gcj(lat, lng) for lng, lat in pts[0]],
                }
                result.append(base)
            elif shape == 2:
                subs = (area.get("sub_areas"))

                for sub in subs:
                    pts = sub.get("polygon_points")

                    if not pts:
                        continue

                    if len(pts) > 1:
                        print("未处理的列表格式")

                    base["geometry"] = {
                        "type": "polygon", 
                        "points": [wgs2gcj(lat, lng) for lng, lat in pts[0]],
                    }
                    result.append(base)
            else:
                print(f"未识别的形状类型: shape={shape}, name={area.get('name')}")
                continue

        return result

    @staticmethod
    def find_closest_home(target_point, homes_set):
        """
        根据直线距离，从机库集合中找出离目标点最近的机库
        target_point: (lat, lng)
        """
        closest_home = None
        min_dist = float('inf')
        
        for home in homes_set:
            dist = geodesic(target_point, home).m
            if dist < min_dist:
                min_dist = dist
                closest_home = home

        return closest_home

    @staticmethod
    def is_point_in_polygon(lat, lng, polygon):
        n = len(polygon)
        inside = False
        p1lat, p1lng = polygon[0]
        for i in range(1, n + 1):
            p2lat, p2lng = polygon[i % n]
            if lat > min(p1lat, p2lat) and lat <= max(p1lat, p2lat):
                if lng <= max(p1lng, p2lng):
                    if p1lat != p2lat:
                        xints = (lat - p1lat) * (p2lng - p1lng) / (p2lat - p1lat) + p1lng
                    if p1lng == p2lng or lng <= xints:
                        inside = not inside
            p1lat, p1lng = p2lat, p2lng
        return inside

    @staticmethod
    def is_collision(lat, lng, nfzs):
        """碰撞检测"""
        for nfz in nfzs:
            geom = nfz.get("geometry")
            
            if geom["type"] == "circle":
                dist = geodesic((lat, lng), geom["center"]).m
                if dist <= geom["radius"]:
                    return True
            elif geom["type"] == "polygon":
                if RouteManager.is_point_in_polygon(lat, lng, geom["points"]):
                    return True
        return False

    @staticmethod
    def snap_to_grid(lat, lng, grid_size):
        return (round(round(lat / grid_size) * grid_size, 6), 
                round(round(lng / grid_size) * grid_size, 6))

    @staticmethod
    def a_star_search(start, goal, nfzs, grid_size=0.0005):
        start_grid = RouteManager.snap_to_grid(start[0], start[1], grid_size)
        goal_grid = RouteManager.snap_to_grid(goal[0], goal[1], grid_size)
        
        directions = [
            (grid_size, 0), (-grid_size, 0), (0, grid_size), (0, -grid_size),
            (grid_size, grid_size), (grid_size, -grid_size), (-grid_size, grid_size), (-grid_size, -grid_size)
        ]
        
        open_set = []
        heapq.heappush(open_set, (0, start_grid[0], start_grid[1]))
        came_from = {}
        g_score = {start_grid: 0}
        closed_set = set()
        
        max_steps = 15000
        steps = 0
        
        while open_set and steps < max_steps:
            _, current_lat, current_lng = heapq.heappop(open_set)
            current = (current_lat, current_lng)

            if current in closed_set:
                continue
            closed_set.add(current)
            steps += 1
            
            if geodesic(current, goal_grid).m <= grid_size * 1.5:
                path = [goal]
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
                
            for dlat, dlng in directions:
                neighbor = (round(current_lat + dlat, 6), round(current_lng + dlng, 6))
                if neighbor in closed_set:
                    continue

                if RouteManager.is_collision(neighbor[0], neighbor[1], nfzs):
                    continue
                    
                tentative_g_score = g_score[current] + geodesic(current, neighbor).m
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + geodesic(neighbor, goal_grid).m
                    heapq.heappush(open_set, (f_score, neighbor[0], neighbor[1]))
                    
        print("局部寻路未完全成功，采用直飞替代段。")
        return [start, goal]

    @staticmethod
    def in_nfz(pt):
        """
        检测单个点是否处于禁飞区内
        pt: (lat, lng) 目标点坐标
        """
        lat, lng = float(pt[0]), float(pt[1])
        ltlat, rblat = lat + 0.04, lat - 0.04
        ltlng, rblng = lng - 0.04, lng + 0.04

        nfzs = RouteManager.get_nfz(ltlat, ltlng, rblat, rblng)

        return RouteManager.is_collision(lat, lng, nfzs)

    @staticmethod
    def auto_plan_and_visualize(load_pt, unload_pt):
        # airsim中起点固定
        start_hm = START
        # 动态寻找离卸货点最近的机库作为终点
        end_hm = RouteManager.find_closest_home(unload_pt, HOMES)

        # 2. 划定禁飞区查询边界
        lats, lngs = [start_hm[0], load_pt[0], unload_pt[0], end_hm[0]], [start_hm[1], load_pt[1], unload_pt[1], end_hm[1]]
        ltlat, rblat = max(lats) + 0.04, min(lats) - 0.04
        ltlng, rblng = min(lngs) - 0.04, max(lngs) + 0.04

        nfzs = RouteManager.get_nfz(ltlat, ltlng, rblat, rblng)
        print(f"当前任务区域内检测到 {len(nfzs)} 个禁飞区。")

        route1 = RouteManager.a_star_search(start_hm, load_pt, nfzs)
        route2 = RouteManager.a_star_search(load_pt, unload_pt, nfzs)[1:]
        route3 = RouteManager.a_star_search(unload_pt, end_hm, nfzs)[1:]

        # The folium HTML preview is kept as a debug-side-effect for the
        # legacy CLI workflow; under FastAPI we suppress it unless the env
        # variable `DRONE_WRITE_MAP_HTML=1` is set.
        import os
        if os.environ.get("DRONE_WRITE_MAP_HTML") == "1":
            try:
                m = folium.Map(
                    location=load_pt,
                    zoom_start=12,
                    tiles="https://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
                    attr="AutoNavi",
                )
                folium.Marker(start_hm, popup="起点机库", icon=folium.Icon(color="green", icon="home")).add_to(m)
                for home in HOMES:
                    if home == end_hm:
                        folium.Marker(home, popup="终点机库", icon=folium.Icon(color="red", icon="flag")).add_to(m)
                    else:
                        folium.Marker(home, popup="备选机库", icon=folium.Icon(color="gray", icon="home", opacity=0.5)).add_to(m)
                folium.Marker(load_pt, popup="装货点", icon=folium.Icon(color="blue", icon="shopping-cart")).add_to(m)
                folium.Marker(unload_pt, popup="卸货点", icon=folium.Icon(color="orange", icon="log-out")).add_to(m)
                for nfz in nfzs:
                    geom = nfz.get("geometry")
                    if not geom:
                        continue
                    if geom["type"] == "circle":
                        folium.Circle(location=geom["center"], radius=geom["radius"], color="red", fill=True, fill_color="red", fill_opacity=0.25, tooltip=nfz['name']).add_to(m)
                    elif geom["type"] == "polygon":
                        folium.Polygon(locations=geom["points"], color="red", fill=True, fill_color="red", fill_opacity=0.25, tooltip=nfz['name']).add_to(m)
                folium.PolyLine(route1, color="blue", weight=4, opacity=0.85, tooltip="航线 1").add_to(m)
                folium.PolyLine(route2, color="blue", weight=4, opacity=0.85, tooltip="航线 2").add_to(m)
                folium.PolyLine(route3, color="blue", weight=4, opacity=0.85, tooltip="航线 3").add_to(m)
                m.save("dynamic_drone_route.html")
            except Exception as exc:  # noqa: BLE001
                print(f"[folium] 写入地图失败：{exc}")
        return route1, route2, route3

    @staticmethod
    def plan_route(start, end):
        """Plan a 3-leg delivery route. Returns a plain dict suitable for JSON."""
        start_hm = START
        end_hm = RouteManager.find_closest_home(end, HOMES)
        lats = [start_hm[0], start[0], end[0], end_hm[0]]
        lngs = [start_hm[1], start[1], end[1], end_hm[1]]
        ltlat, rblat = max(lats) + 0.04, min(lats) - 0.04
        ltlng, rblng = min(lngs) - 0.04, max(lngs) + 0.04
        nfzs = RouteManager.get_nfz(ltlat, ltlng, rblat, rblng)
        leg1 = RouteManager.a_star_search(start_hm, start, nfzs)
        leg2 = RouteManager.a_star_search(start, end, nfzs)[1:]
        leg3 = RouteManager.a_star_search(end, end_hm, nfzs)[1:]
        return {
            "legs": [leg1, leg2, leg3],
            "no_fly_zones": nfzs,
            "homes": [{"lat": h[0], "lng": h[1]} for h in HOMES],
            "start_home": {"lat": start_hm[0], "lng": start_hm[1]},
            "end_home": {"lat": end_hm[0], "lng": end_hm[1]},
            "load_pt": {"lat": start[0], "lng": start[1]},
            "unload_pt": {"lat": end[0], "lng": end[1]},
        }