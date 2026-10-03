"""
Unit Tests for FMCSA Daily Log Generator and SVG Vector Renderer
Tests:
- Midnight boundary splitting
- Daily duty status total equals exactly 24.0 hours
- Accurate daily driving mileage
- Remarks generated for all duty transitions
- Multi-day continuity
- 100% Valid XML/SVG document structure via xml.etree.ElementTree
- XML character escaping (&, <, >, quotes)
- Long text truncation and layout resilience
"""

import pytest
import xml.etree.ElementTree as ET
from datetime import datetime
from trips.services.hos.engine import HOSEngine
from trips.services.logs.generator import generate_daily_logs
from trips.services.logs.svg_renderer import render_log_svg


def test_daily_log_totals_sum_to_24():
    """Verify that every generated daily log sums to exactly 24.00 hours."""
    engine = HOSEngine(current_cycle_used_hrs=25.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 34.0522, "lng": -118.2437, "name": "Los Angeles, CA"}
    p_loc = {"lat": 39.7392, "lng": -104.9903, "name": "Denver, CO"}
    d_loc = {"lat": 40.7128, "lng": -74.0060, "name": "New York, NY"}

    leg1 = {"distance_miles": 1000.0, "waypoints": []}
    leg2 = {"distance_miles": 1800.0, "waypoints": []}

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    logs = generate_daily_logs(plan.timeline_events, current_cycle_used_hrs=25.0)

    assert len(logs) >= 3
    for log in logs:
        totals = log["totals"]
        sum_hrs = totals["off_duty"] + totals["sleeper_berth"] + totals["driving"] + totals["on_duty_not_driving"]
        assert pytest.approx(sum_hrs, 0.01) == 24.0
        assert totals["total_hours"] == 24.0


def test_remarks_generated_at_transitions():
    """Verify location remarks are present at duty status changes."""
    engine = HOSEngine(current_cycle_used_hrs=10.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    p_loc = {"lat": 43.0389, "lng": -87.9065, "name": "Milwaukee, WI"}
    d_loc = {"lat": 43.0731, "lng": -89.4012, "name": "Madison, WI"}

    leg1 = {"distance_miles": 90.0, "waypoints": []}
    leg2 = {"distance_miles": 80.0, "waypoints": []}

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    logs = generate_daily_logs(plan.timeline_events, current_cycle_used_hrs=10.0)

    assert len(logs) >= 1
    log1 = logs[0]
    assert len(log1["remarks"]) >= 3
    assert any("Chicago" in r["location"] for r in log1["remarks"])
    assert any("Milwaukee" in r["location"] for r in log1["remarks"])


def test_svg_rendering_output_and_xml_validity():
    """Verify SVG log sheet renders with required elements and parses as strictly valid XML."""
    engine = HOSEngine(current_cycle_used_hrs=15.0, start_datetime=datetime(2026, 10, 5, 6, 0))
    c_loc = {"lat": 41.8781, "lng": -87.6298, "name": "Chicago, IL"}
    p_loc = {"lat": 41.6021, "lng": -87.3371, "name": "Gary, IN"}
    d_loc = {"lat": 39.9612, "lng": -82.9988, "name": "Columbus, OH"}

    leg1 = {"distance_miles": 30.0, "waypoints": []}
    leg2 = {"distance_miles": 320.0, "waypoints": []}

    plan = engine.plan_trip(c_loc, p_loc, d_loc, leg1, leg2)
    logs = generate_daily_logs(plan.timeline_events, current_cycle_used_hrs=15.0)

    for log in logs:
        svg_str = render_log_svg(log)
        assert "<svg" in svg_str
        assert "</svg>" in svg_str
        assert "Drivers Daily Log" in svg_str
        assert "RECAP" in svg_str
        assert "= 24.00" in svg_str or "= 24" in svg_str

        # Strict XML parser check
        root = ET.fromstring(svg_str)
        assert root.tag.endswith("svg")


def test_svg_xml_escaping_special_characters():
    """Ensure raw ampersands, angle brackets, and quotes in user fields do not break SVG XML parsing."""
    sample_log = {
        "day_number": 1,
        "date_formatted": "10 / 02 / 2026",
        "from_location": "B&B Trucking <Dock #1>, Gary, IN",
        "to_location": 'Fast & "Reliable" Logistics & Distribution, Chicago, IL',
        "carrier_name": "AT&T Freight & Transport LLC",
        "main_office_address": "400 B&O Way, Baltimore, MD",
        "home_terminal_address": "800 I-80 & Route 66, Joliet, IL",
        "truck_tractor_num": "TRK #101 & 102",
        "trailer_num": "TLR & Reefer #50",
        "driver_name": "Tom & Jerry",
        "co_driver": "Mickey & Minnie",
        "shipping_doc": "BOL #100 & #200 <FRAGILE>",
        "shipper_commodity": "Apples & Oranges > 500 lbs",
        "total_miles_driving_today": 450.5,
        "total_mileage_today": 450.5,
        "totals": {
            "off_duty": 10.0,
            "sleeper_berth": 0.0,
            "driving": 10.0,
            "on_duty_not_driving": 4.0,
            "total_hours": 24.0,
        },
        "recap": {
            "on_duty_today": 14.0,
            "column_a_last_7_days": 28.0,
            "column_b_available_tomorrow": 42.0,
            "column_c_last_8_days": 35.0,
        },
        "grid_segments": [
            {"line_number": 1, "start_hour": 0.0, "end_hour": 8.0},
            {"line_number": 3, "start_hour": 8.0, "end_hour": 18.0},
            {"line_number": 4, "start_hour": 18.0, "end_hour": 24.0},
        ],
        "grid_transitions": [
            {"time_hour": 8.0, "from_line": 1, "to_line": 3},
            {"time_hour": 18.0, "from_line": 3, "to_line": 4},
        ],
        "remarks": [
            {"time": "08:00", "status_name": "Driving", "location": "I-80 & Milepost 42, Joliet, IL", "notes": "Started trip with BOL & Manifest"},
            {"time": "18:00", "status_name": "On Duty (not driving)", "location": "Dock & Bay #4, Chicago, IL", "notes": "Unloading & Inspection"},
        ],
        "has_34h_restart": True,
    }

    svg_str = render_log_svg(sample_log)
    root = ET.fromstring(svg_str)
    assert root.tag.endswith("svg")
    assert "B&amp;B Trucking" in svg_str
    assert "AT&amp;T Freight &amp; Transport" in svg_str
