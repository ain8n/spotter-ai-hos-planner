"""
Routing Service for Commercial Trucks
Integrates OSRM / OpenRouteService with resilient fallback highway routing engine.
"""

import math
import os
import requests
from typing import Dict, Any, List, Tuple, Optional
from ..geocoding.geocoder import reverse_geocode


def haversine_distance_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculates great-circle distance in statute miles between two points.
    """
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class RouteCalculator:
    """
    Calculates driving route between two geographic points.
    """

    def __init__(self, ors_api_key: str = None):
        self.ors_api_key = ors_api_key or os.environ.get("ORS_API_KEY", "")

    def calculate_leg(
        self,
        start_lat: float,
        start_lng: float,
        start_name: str,
        end_lat: float,
        end_lng: float,
        end_name: str,
    ) -> Dict[str, Any]:
        """
        Calculates route details for a single leg.
        """
        # Try OSRM public API first
        osrm_result = self._try_osrm(start_lat, start_lng, start_name, end_lat, end_lng, end_name)
        if osrm_result:
            return osrm_result

        # Try OpenRouteService if API key is present
        if self.ors_api_key:
            ors_result = self._try_ors(start_lat, start_lng, start_name, end_lat, end_lng, end_name)
            if ors_result:
                return ors_result

        # Resilient highway synthesizer fallback
        return self._synthesize_highway_route(start_lat, start_lng, start_name, end_lat, end_lng, end_name)

    def _try_osrm(
        self,
        lat1: float,
        lng1: float,
        name1: str,
        lat2: float,
        lng2: float,
        name2: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://router.project-osrm.org/route/v1/driving/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson&steps=true"
            headers = {"User-Agent": "HOS-Trip-Planner/1.0"}
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    dist_meters = float(route.get("distance", 0.0))
                    duration_sec = float(route.get("duration", 0.0))
                    dist_miles = dist_meters * 0.000621371
                    # Heavy commercial trucks average ~55-60 mph
                    duration_hours = dist_miles / 55.0 if dist_miles > 0 else 0.0

                    coords = route.get("geometry", {}).get("coordinates", [])
                    # OSRM returns [lng, lat], convert to [lat, lng]
                    leaflet_coords = [[c[1], c[0]] for c in coords]

                    instructions = []
                    for leg in route.get("legs", []):
                        for step in leg.get("steps", []):
                            maneuver = step.get("maneuver", {})
                            step_name = step.get("name") or "Highway"
                            step_dist_mi = step.get("distance", 0.0) * 0.000621371
                            step_dur_min = step_dist_mi / 55.0 * 60.0
                            step_type = maneuver.get("type", "drive")
                            mod = maneuver.get("modifier", "")
                            text = f"{step_type.capitalize()} {mod} on {step_name}".strip()
                            instructions.append({
                                "text": text,
                                "distance_miles": round(step_dist_mi, 1),
                                "duration_mins": round(step_dur_min, 1),
                            })

                    waypoints = self._sample_waypoints(leaflet_coords, name1, name2)

                    return {
                        "distance_miles": round(dist_miles, 1),
                        "duration_hours": round(duration_hours, 2),
                        "geometry": leaflet_coords,
                        "instructions": instructions[:15] if instructions else self._default_instructions(name1, name2, dist_miles),
                        "waypoints": waypoints,
                        "source": "OSRM",
                    }
        except Exception:
            pass
        return None

    def _try_ors(
        self,
        lat1: float,
        lng1: float,
        name1: str,
        lat2: float,
        lng2: float,
        name2: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            url = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"
            headers = {
                "Authorization": self.ors_api_key,
                "Content-Type": "application/json",
            }
            body = {"coordinates": [[lng1, lat1], [lng2, lat2]]}
            resp = requests.post(url, json=body, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    feature = features[0]
                    props = feature.get("properties", {}).get("summary", {})
                    dist_meters = float(props.get("distance", 0.0))
                    dist_miles = dist_meters * 0.000621371
                    duration_hours = dist_miles / 55.0

                    coords = feature.get("geometry", {}).get("coordinates", [])
                    leaflet_coords = [[c[1], c[0]] for c in coords]
                    waypoints = self._sample_waypoints(leaflet_coords, name1, name2)

                    return {
                        "distance_miles": round(dist_miles, 1),
                        "duration_hours": round(duration_hours, 2),
                        "geometry": leaflet_coords,
                        "instructions": self._default_instructions(name1, name2, dist_miles),
                        "waypoints": waypoints,
                        "source": "OpenRouteService",
                    }
        except Exception:
            pass
        return None

    def _synthesize_highway_route(
        self,
        lat1: float,
        lng1: float,
        name1: str,
        lat2: float,
        lng2: float,
        name2: str,
    ) -> Dict[str, Any]:
        """
        Synthesizes realistic commercial highway route with road detour ratio (~1.18x haversine)
        and intermediate waypoint sampling.
        """
        direct_miles = haversine_distance_miles(lat1, lng1, lat2, lng2)
        road_miles = max(5.0, direct_miles * 1.18)
        duration_hours = road_miles / 55.0

        num_points = max(10, min(100, int(road_miles / 15.0)))
        leaflet_coords = []
        waypoints = []

        for i in range(num_points + 1):
            t = float(i) / float(num_points)
            curvature = math.sin(t * math.pi) * 0.15 * ((lat1 + lng1) % 1.0 - 0.5)
            cur_lat = lat1 + (lat2 - lat1) * t + curvature * 0.5
            cur_lng = lng1 + (lng2 - lng1) * t + curvature * 0.8
            leaflet_coords.append([round(cur_lat, 5), round(cur_lng, 5)])

            if i % max(1, int(num_points / 8)) == 0 or i == num_points:
                sub_name = name1 if i == 0 else (name2 if i == num_points else f"{name1} to {name2}")
                waypoints.append({
                    "lat": round(cur_lat, 5),
                    "lng": round(cur_lng, 5),
                    "name": sub_name,
                    "fraction": round(t, 3),
                })

        instructions = self._default_instructions(name1, name2, road_miles)

        return {
            "distance_miles": round(road_miles, 1),
            "duration_hours": round(duration_hours, 2),
            "geometry": leaflet_coords,
            "instructions": instructions,
            "waypoints": waypoints,
            "source": "Synthesized Highway Route",
        }

    def _sample_waypoints(self, leaflet_coords: List[List[float]], name1: str, name2: str) -> List[Dict[str, Any]]:
        n = len(leaflet_coords)
        if n == 0:
            return []
        if n == 1:
            return [{"lat": leaflet_coords[0][0], "lng": leaflet_coords[0][1], "name": name1, "fraction": 0.0}]

        samples = []
        step = max(1, int(n / 10))
        for i in range(0, n, step):
            pt = leaflet_coords[i]
            frac = float(i) / float(n - 1)
            p_name = name1 if i == 0 else (name2 if i == n - 1 else f"{name1} to {name2}")
            samples.append({"lat": pt[0], "lng": pt[1], "name": p_name, "fraction": round(frac, 3)})

        last_pt = leaflet_coords[-1]
        if not samples or samples[-1]["fraction"] < 0.99:
            samples.append({"lat": last_pt[0], "lng": last_pt[1], "name": name2, "fraction": 1.0})

        return samples

    def _default_instructions(self, name1: str, name2: str, dist_miles: float) -> List[Dict[str, Any]]:
        return [
            {
                "text": f"Depart from {name1} on main commercial route",
                "distance_miles": round(dist_miles * 0.1, 1),
                "duration_mins": round((dist_miles * 0.1) / 55.0 * 60.0, 1),
            },
            {
                "text": f"Continue on highway toward {name2}",
                "distance_miles": round(dist_miles * 0.8, 1),
                "duration_mins": round((dist_miles * 0.8) / 55.0 * 60.0, 1),
            },
            {
                "text": f"Arrive at {name2} destination",
                "distance_miles": round(dist_miles * 0.1, 1),
                "duration_mins": round((dist_miles * 0.1) / 55.0 * 60.0, 1),
            },
        ]
