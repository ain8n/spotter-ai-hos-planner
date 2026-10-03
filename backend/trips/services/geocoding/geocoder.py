"""
Geocoding Service for Truck Routing and Global Search
Integrates OpenStreetMap Nominatim and Photon with caching and fallback.
Supports multi-language queries (English, Urdu, etc.), small localities, neighborhoods, and coordinate inputs.
"""

import requests
import re
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple

_GEOCODE_CACHE: Dict[str, Dict[str, Any]] = {}
_REVERSE_CACHE: Dict[str, str] = {}


def _clean_display_name(raw_name: str, addr: Dict[str, Any]) -> str:
    """Formats address components into a clean, human-readable place name with fine-grained road/locality context."""
    road = addr.get("road") or addr.get("pedestrian") or addr.get("street")
    neighbourhood = addr.get("neighbourhood") or addr.get("quarter") or addr.get("residential")
    suburb = addr.get("suburb") or addr.get("hamlet") or addr.get("village")
    city = addr.get("city") or addr.get("town") or addr.get("municipality") or addr.get("county") or addr.get("state_district")
    state = addr.get("state") or addr.get("ISO3166-2-lvl4", "").split("-")[-1]
    country = addr.get("country", "")

    parts = []
    if road:
        parts.append(road)
    elif neighbourhood:
        parts.append(neighbourhood)
    elif suburb:
        parts.append(suburb)

    if city and city not in parts:
        parts.append(city)
    elif suburb and suburb not in parts:
        parts.append(suburb)

    if state and state not in parts:
        parts.append(state)
    if country and country not in parts:
        parts.append(country)

    if parts:
        return ", ".join(parts)
    return raw_name.split(",")[0].strip() if raw_name else "Selected Location"


def search_locations(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Returns autocomplete search suggestions for location queries.
    Supports English, Urdu, coordinates, localities, and partial addresses.
    Never searches OSM for 'Your Location' or 'Current Location' labels.
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 2:
        return []

    if clean_q.lower() in ["your location", "current location", "my location", "gps", "gps position"]:
        return []

    results: List[Dict[str, Any]] = []
    seen = set()

    # 1. Coordinate check: e.g. "33.6844, 73.0479"
    coord_match = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*$", clean_q)
    if coord_match:
        lat = round(float(coord_match.group(1)), 5)
        lng = round(float(coord_match.group(2)), 5)
        name = reverse_geocode(lat, lng)
        return [{"name": name, "display_name": name, "lat": lat, "lng": lng}]

    # 2. Query OpenStreetMap Nominatim
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(clean_q)}&format=json&addressdetails=1&limit={limit}"
        headers = {
            "User-Agent": "HOS-Trip-Planner-ELD/1.0 (trucking-navigation)",
            "Accept-Language": "en,ur;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            for item in resp.json():
                lat = round(float(item["lat"]), 5)
                lng = round(float(item["lon"]), 5)
                coord_pair = (round(lat, 3), round(lng, 3))
                if coord_pair not in seen:
                    seen.add(coord_pair)
                    addr = item.get("address", {})
                    clean_name = _clean_display_name(item.get("display_name", clean_q), addr)
                    results.append({
                        "name": clean_name,
                        "display_name": item.get("display_name", clean_name),
                        "lat": lat,
                        "lng": lng,
                    })
                    if len(results) >= limit:
                        break
    except Exception:
        pass

    # 3. Fallback to Photon (OSM search for small localities) if no results found
    if len(results) == 0:
        try:
            url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(clean_q)}&limit={limit}"
            r = requests.get(url, headers={"User-Agent": "HOS-Trip-Planner/1.0"}, timeout=3)
            if r.status_code == 200:
                for f in r.json().get("features", []):
                    props = f.get("properties", {})
                    coords = f.get("geometry", {}).get("coordinates", [])
                    if len(coords) >= 2:
                        lng = round(float(coords[0]), 5)
                        lat = round(float(coords[1]), 5)
                        coord_pair = (round(lat, 3), round(lng, 3))
                        if coord_pair not in seen:
                            seen.add(coord_pair)
                            name_part = props.get("name") or props.get("street") or clean_q
                            city_part = props.get("city") or props.get("state") or ""
                            country_part = props.get("country", "")
                            parts = [p for p in [name_part, city_part, country_part] if p]
                            clean_name = ", ".join(parts)
                            results.append({
                                "name": clean_name,
                                "display_name": clean_name,
                                "lat": lat,
                                "lng": lng,
                            })
                            if len(results) >= limit:
                                break
        except Exception:
            pass

    return results


def geocode_location(query: str) -> Dict[str, Any]:
    """
    Geocodes a single location string into latitude, longitude, and normalized name.
    """
    clean_q = query.strip()
    norm_key = clean_q.lower()

    if norm_key in ["your location", "current location", "my location", "gps position"]:
        return {"lat": 38.8951, "lng": -77.0364, "name": "Your Location", "state": "DC"}

    if norm_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[norm_key]

    # Coordinate check
    coord_match = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*$", clean_q)
    if coord_match:
        lat = round(float(coord_match.group(1)), 5)
        lng = round(float(coord_match.group(2)), 5)
        name = reverse_geocode(lat, lng)
        res = {"lat": lat, "lng": lng, "name": name, "state": ""}
        _GEOCODE_CACHE[norm_key] = res
        return res

    # Search via search_locations
    suggestions = search_locations(clean_q, limit=1)
    if suggestions:
        first = suggestions[0]
        res = {
            "lat": first["lat"],
            "lng": first["lng"],
            "name": first["name"],
            "state": "",
        }
        _GEOCODE_CACHE[norm_key] = res
        return res

    # Fallback to Chicago if totally unknown
    res = {"lat": 41.8781, "lng": -87.6298, "name": clean_q, "state": "IL"}
    _GEOCODE_CACHE[norm_key] = res
    return res


def reverse_geocode(lat: float, lng: float) -> str:
    """
    Turns latitude/longitude into a descriptive City, Region, Country.
    """
    key = f"{lat:.4f},{lng:.4f}"
    if key in _REVERSE_CACHE:
        return _REVERSE_CACHE[key]

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&zoom=18&addressdetails=1"
        headers = {
            "User-Agent": "HOS-Trip-Planner-ELD/1.0 (trucking-navigation)",
            "Accept-Language": "en,ur;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            addr = data.get("address", {})
            clean_name = _clean_display_name(data.get("display_name", ""), addr)
            _REVERSE_CACHE[key] = clean_name
            return clean_name
    except Exception:
        pass

    fallback = f"{lat:.4f}, {lng:.4f}"
    _REVERSE_CACHE[key] = fallback
    return fallback
