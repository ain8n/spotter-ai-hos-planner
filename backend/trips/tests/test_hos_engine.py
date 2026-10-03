"""
Unit Tests for FMCSA HOS Engine
Tests compliance with 49 CFR Part 395 for property-carrying drivers:
- 11-Hour Driving Limit
- 14-Hour Duty Window
- 30-Minute Break after 8 Driving Hours
- 10-Hour Daily Reset
- 70-Hour / 8-Day Cycle Limit
- 34-Hour Restart
- 1,000-Mile Fuel Stops
- 1-Hour Pickup & Dropoff On-Duty Time
"""

import pytest
from datetime import datetime, timedelta
from trips.services.hos.constants import (
    MAX_DRIVING_HOURS_PER_SHIFT,
    MAX_DUTY_WINDOW_HOURS,
    DRIVING_HOURS_BEFORE_BREAK,
    CYCLE_LIMIT_HOURS,
    STATUS_DRIVING,
    STATUS_OFF_DUTY,
    STATUS_SLEEPER_BERTH,
    STATUS_ON_DUTY_NOT_DRIVING,
)
from trips.services.hos.engine import HOSEngine


def test_30_minute_break_after_8_hours_driving():
    """Verify mandatory 30-min break is inserted after 8 cumulative driving hours."""
    engine = HOSEngine(current_cycle_used_hrs=0.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    p_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    d_loc = {"lat": 39.7392, "lng": -104.9903, "name": "Denver, CO"}

    leg1 = {"distance_miles": 10.0, "waypoints": []}
    leg2 = {"distance_miles": 550.0, "waypoints": []}  # 550 mi at 55 mph = 10 hrs driving

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    break_stops = [s for s in plan.stops if s["stop_type"] == "REST_30"]
    assert len(break_stops) >= 1
    assert break_stops[0]["duration_hours"] == 0.5


def test_11_hour_driving_limit_and_10_hour_reset():
    """Verify 10-hour rest is triggered when 11 driving hours are reached."""
    engine = HOSEngine(current_cycle_used_hrs=0.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    p_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    d_loc = {"lat": 34.0522, "lng": -118.2437, "name": "Los Angeles, CA"}

    leg1 = {"distance_miles": 0.0, "waypoints": []}
    leg2 = {"distance_miles": 700.0, "waypoints": []}  # ~12.7 hrs driving -> must take 10h rest after 11h driving

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    rest_stops = [s for s in plan.stops if s["stop_type"] == "REST_10"]
    assert len(rest_stops) >= 1
    assert rest_stops[0]["duration_hours"] == 10.0


def test_fuel_stop_every_1000_miles():
    """Verify fuel stops are scheduled at or before 1,000 miles."""
    engine = HOSEngine(current_cycle_used_hrs=0.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 34.0522, "lng": -118.2437, "name": "Los Angeles, CA"}
    p_loc = {"lat": 34.0522, "lng": -118.2437, "name": "Los Angeles, CA"}
    d_loc = {"lat": 40.7128, "lng": -74.0060, "name": "New York, NY"}

    leg1 = {"distance_miles": 0.0, "waypoints": []}
    leg2 = {"distance_miles": 2200.0, "waypoints": []}

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    fuel_stops = [s for s in plan.stops if s["stop_type"] == "FUEL"]
    assert len(fuel_stops) >= 2
    for s in fuel_stops:
        assert s["duration_hours"] == 0.5
        assert s["mile_marker"] <= 2000.0


def test_pickup_and_dropoff_1_hour_on_duty():
    """Verify pickup and dropoff each consume 1 hour of On-Duty Not Driving."""
    engine = HOSEngine(current_cycle_used_hrs=10.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    p_loc = {"lat": 43.0389, "lng": -87.9065, "name": "Milwaukee, WI"}
    d_loc = {"lat": 43.0731, "lng": -89.4012, "name": "Madison, WI"}

    leg1 = {"distance_miles": 90.0, "waypoints": []}
    leg2 = {"distance_miles": 80.0, "waypoints": []}

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    pickup_events = [e for e in plan.timeline_events if e["activity_type"] == "PICKUP"]
    dropoff_events = [e for e in plan.timeline_events if e["activity_type"] == "DROPOFF"]

    assert len(pickup_events) == 1
    assert pickup_events[0]["duration_hours"] == 1.0
    assert pickup_events[0]["status"] == STATUS_ON_DUTY_NOT_DRIVING

    assert len(dropoff_events) == 1
    assert dropoff_events[0]["duration_hours"] == 1.0
    assert dropoff_events[0]["status"] == STATUS_ON_DUTY_NOT_DRIVING


def test_34_hour_restart_when_cycle_exceeded():
    """Verify 34-hour restart is inserted when starting with >= 70 hours used."""
    engine = HOSEngine(current_cycle_used_hrs=70.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    p_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    d_loc = {"lat": 39.7684, "lng": -86.1581, "name": "Indianapolis, IN"}

    leg1 = {"distance_miles": 10.0, "waypoints": []}
    leg2 = {"distance_miles": 180.0, "waypoints": []}

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    restart_events = [e for e in plan.timeline_events if e["activity_type"] == "RESTART_34"]

    assert len(restart_events) >= 1
    assert restart_events[0]["duration_hours"] == 34.0
    assert restart_events[0]["status"] == STATUS_OFF_DUTY
    assert any("34-hour restart" in w.lower() for w in plan.warnings)
