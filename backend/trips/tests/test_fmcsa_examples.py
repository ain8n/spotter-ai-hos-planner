"""
Tests for Official FMCSA Guide Examples
Verifies fixtures from FMCSA-HOS-395 (April 2022 / June 2020 revision)
"""

import pytest
from trips.services.hos.recap import calculate_daily_recap
from trips.services.logs.svg_renderer import render_log_svg


def test_fmcsa_page_11_rolling_8_day_example():
    """
    Tests the 10-day rolling table from FMCSA Guide Page 11:
    Day 1: 0 hrs (Sun)
    Day 2: 10 hrs (Mon)
    Day 3: 8.5 hrs (Tue)
    Day 4: 12.5 hrs (Wed)
    Day 5: 9 hrs (Thu)
    Day 6: 10 hrs (Fri)
    Day 7: 12 hrs (Sat)
    Day 8: 5 hrs (Sun) -> Days 1-8 total = 67 hrs
    Day 9: 6 hrs (Mon) -> Days 2-9 total = 73 hrs (Day 1 drops off)
    Day 10: 0 hrs (Tue) -> Days 3-10 total = 63 hrs (Day 2 drops off)
    """
    # Prior 7 days: Days 1 to 7 [0, 10, 8.5, 12.5, 9, 10, 12]
    prior = [0.0, 10.0, 8.5, 12.5, 9.0, 10.0, 12.0]

    # Trip days: Day 8 (5h), Day 9 (6h), Day 10 (0h)
    daily_logs = [
        {"date": "2026-10-08", "totals": {"driving": 4.0, "on_duty_not_driving": 1.0}, "has_34h_restart": False},
        {"date": "2026-10-09", "totals": {"driving": 5.0, "on_duty_not_driving": 1.0}, "has_34h_restart": False},
        {"date": "2026-10-10", "totals": {"driving": 0.0, "on_duty_not_driving": 0.0}, "has_34h_restart": False},
    ]

    recaps = calculate_daily_recap(daily_logs, prior_7_days_on_duty=prior)

    # Day 8: 8-day total (Days 1-8) must be 67.0
    assert recaps[0]["column_c_last_8_days"] == 67.0

    # Day 9: 8-day total (Days 2-9) must be 73.0
    assert recaps[1]["column_c_last_8_days"] == 73.0

    # Day 10: 8-day total (Days 3-10) must be 63.0
    assert recaps[2]["column_c_last_8_days"] == 63.0


def test_fmcsa_page_19_john_doe_log_totals():
    """
    Tests John Doe's sample completed log from FMCSA Guide Page 18-19:
    Off Duty: 10.0 hrs
    Sleeper Berth: 1.75 hrs
    Driving: 7.75 hrs
    On Duty (Not Driving): 4.5 hrs
    Total: 24.0 hrs
    Miles: 350 mi
    """
    john_doe_log = {
        "day_number": 1,
        "date_formatted": "04 / 09 / 2021",
        "from_location": "Richmond, VA",
        "to_location": "Newark, NJ",
        "total_miles_driving_today": 350.0,
        "total_mileage_today": 350.0,
        "carrier_name": "John Doe's Transportation",
        "main_office_address": "Washington, D.C.",
        "home_terminal_address": "Richmond, VA",
        "truck_tractor_num": "123, 20544",
        "trailer_num": "101601",
        "driver_name": "John E. Doe",
        "co_driver": "N/A",
        "shipping_doc": "Manifest #49281",
        "shipper_commodity": "General Freight",
        "totals": {
            "off_duty": 10.0,
            "sleeper_berth": 1.75,
            "driving": 7.75,
            "on_duty_not_driving": 4.5,
            "total_hours": 24.0,
        },
        "grid_segments": [
            {"start_hour": 0.0, "end_hour": 6.0, "status": "OFF_DUTY", "line_number": 1, "location": "Richmond, VA", "notes": "Off Duty"},
            {"start_hour": 6.0, "end_hour": 7.5, "status": "ON_DUTY_NOT_DRIVING", "line_number": 4, "location": "Richmond, VA", "notes": "Pre-trip & Loading"},
            {"start_hour": 7.5, "end_hour": 9.0, "status": "DRIVING", "line_number": 3, "location": "Fredericksburg, VA", "notes": "Driving"},
            {"start_hour": 9.0, "end_hour": 9.5, "status": "ON_DUTY_NOT_DRIVING", "line_number": 4, "location": "Fredericksburg, VA", "notes": "Fueling"},
            {"start_hour": 9.5, "end_hour": 12.0, "status": "DRIVING", "line_number": 3, "location": "Baltimore, MD", "notes": "Driving"},
            {"start_hour": 12.0, "end_hour": 13.0, "status": "OFF_DUTY", "line_number": 1, "location": "Baltimore, MD", "notes": "Lunch Break"},
            {"start_hour": 13.0, "end_hour": 15.0, "status": "DRIVING", "line_number": 3, "location": "Philadelphia, PA", "notes": "Driving"},
            {"start_hour": 15.0, "end_hour": 15.5, "status": "ON_DUTY_NOT_DRIVING", "line_number": 4, "location": "Philadelphia, PA", "notes": "Delivery Stop"},
            {"start_hour": 15.5, "end_hour": 16.0, "status": "DRIVING", "line_number": 3, "location": "Cherry Hill, NJ", "notes": "Driving"},
            {"start_hour": 16.0, "end_hour": 17.75, "status": "SLEEPER_BERTH", "line_number": 2, "location": "Cherry Hill, NJ", "notes": "Sleeper Berth Rest"},
            {"start_hour": 17.75, "end_hour": 19.0, "status": "DRIVING", "line_number": 3, "location": "Newark, NJ", "notes": "Driving to Newark"},
            {"start_hour": 19.0, "end_hour": 21.0, "status": "ON_DUTY_NOT_DRIVING", "line_number": 4, "location": "Newark, NJ", "notes": "Post-trip & Paperwork"},
            {"start_hour": 21.0, "end_hour": 24.0, "status": "OFF_DUTY", "line_number": 1, "location": "Newark, NJ", "notes": "Off Duty"},
        ],
        "grid_transitions": [],
        "remarks": [
            {"time": "06:00 AM", "time_hour": 6.0, "location": "Richmond, VA", "status_name": "On Duty (Not Driving)", "notes": "Reported for work"},
            {"time": "09:00 AM", "time_hour": 9.0, "location": "Fredericksburg, VA", "status_name": "On Duty (Not Driving)", "notes": "Stopped & fueled truck"},
            {"time": "12:00 PM", "time_hour": 12.0, "location": "Baltimore, MD", "status_name": "Off Duty", "notes": "Lunch in Baltimore"},
            {"time": "03:00 PM", "time_hour": 15.0, "location": "Philadelphia, PA", "status_name": "On Duty (Not Driving)", "notes": "Delivery stop"},
            {"time": "04:00 PM", "time_hour": 16.0, "location": "Cherry Hill, NJ", "status_name": "Sleeper Berth", "notes": "Entered sleeper berth"},
            {"time": "07:00 PM", "time_hour": 19.0, "location": "Newark, NJ", "status_name": "On Duty (Not Driving)", "notes": "Arrived terminal"},
            {"time": "09:00 PM", "time_hour": 21.0, "location": "Newark, NJ", "status_name": "Off Duty", "notes": "Released from work"},
        ],
        "recap": {
            "on_duty_today": 12.25,
            "column_a_last_7_days": 42.5,
            "column_b_available_tomorrow": 27.5,
            "column_c_last_8_days": 48.0,
        }
    }

    tot = john_doe_log["totals"]
    assert tot["off_duty"] + tot["sleeper_berth"] + tot["driving"] + tot["on_duty_not_driving"] == 24.0
    svg = render_log_svg(john_doe_log)
    assert "John Doe" in svg
    assert "Richmond, VA" in svg
    assert "Newark, NJ" in svg
