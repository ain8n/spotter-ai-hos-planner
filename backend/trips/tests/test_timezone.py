"""
Tests for Geolocation Timezone Resolution and Timezone-Aware Trip Planning
"""

import pytest
from datetime import datetime
from trips.services.geocoding.timezone import determine_timezone_from_coords
from trips.services.hos.engine import HOSEngine
from trips.services.logs.generator import generate_daily_logs


def test_timezone_determination():
    """Verify coordinate-to-timezone mapping across US regions and worldwide."""
    # Eastern
    assert determine_timezone_from_coords(40.7128, -74.0060) == "America/New_York"
    assert determine_timezone_from_coords(37.5407, -77.4360) == "America/New_York"

    # Central
    assert determine_timezone_from_coords(41.8781, -87.6298) == "America/Chicago"
    assert determine_timezone_from_coords(29.7604, -95.3698) == "America/Chicago"

    # Mountain
    assert determine_timezone_from_coords(39.7392, -104.9903) == "America/Denver"

    # Pacific
    assert determine_timezone_from_coords(34.0522, -118.2437) == "America/Los_Angeles"
    assert determine_timezone_from_coords(47.6062, -122.3321) == "America/Los_Angeles"

    # Alaska & Hawaii
    assert determine_timezone_from_coords(61.2181, -149.9003) == "America/Anchorage"
    assert determine_timezone_from_coords(21.3069, -157.8583) == "Pacific/Honolulu"


def test_hos_engine_with_timezone():
    """Verify HOSEngine schedules with proper timezone-aware datetimes."""
    engine = HOSEngine(
        current_cycle_used_hrs=10.0,
        start_datetime=datetime(2026, 10, 5, 6, 0),
        timezone_name="America/Chicago",
    )
    c_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL", "timezone": "America/Chicago"}
    p_loc = {"lat": 41.6021, "lng": -87.3371, "name": "Gary, IN", "timezone": "America/Chicago"}
    d_loc = {"lat": 39.9612, "lng": -82.9988, "name": "Columbus, OH", "timezone": "America/New_York"}

    leg1 = {"distance_miles": 30.0, "waypoints": []}
    leg2 = {"distance_miles": 320.0, "waypoints": []}

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    assert plan.summary["timezone"] == "America/Chicago"
    assert "start_time" in plan.summary

    logs = generate_daily_logs(plan.timeline_events, current_cycle_used_hrs=10.0)
    assert len(logs) >= 1
    assert logs[0]["totals"]["total_hours"] == 24.0
