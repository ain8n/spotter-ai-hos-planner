"""
Unit Tests for 70-Hour / 8-Day Rolling Recap Calculation
Tests compliance with 49 CFR § 395.3(b)
"""

import pytest
from trips.services.hos.recap import calculate_daily_recap


def test_recap_rolling_8_day_calculation():
    """Test standard 8-day rolling window on-duty accounting."""
    # 7 historical days of 7.0 hours each -> 49.0 hours used
    prior_7_days = [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0]

    daily_logs = [
        {"date": "2026-10-01", "totals": {"driving": 8.0, "on_duty_not_driving": 2.0}, "has_34h_restart": False},
        {"date": "2026-10-02", "totals": {"driving": 6.0, "on_duty_not_driving": 1.5}, "has_34h_restart": False},
    ]

    recaps = calculate_daily_recap(daily_logs, prior_7_days_on_duty=prior_7_days)

    assert len(recaps) == 2

    # Day 1: on_duty = 10.0
    # Last 7 days: [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 10.0] = 52.0
    # Available tomorrow: 70 - 52 = 18.0
    # Last 8 days: [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 10.0] = 59.0
    r1 = recaps[0]
    assert r1["on_duty_today"] == 10.0
    assert r1["column_a_last_7_days"] == 52.0
    assert r1["column_b_available_tomorrow"] == 18.0
    assert r1["column_c_last_8_days"] == 59.0

    # Day 2: on_duty = 7.5
    # Last 7 days: [7.0, 7.0, 7.0, 7.0, 7.0, 10.0, 7.5] = 52.5
    # Available tomorrow: 70 - 52.5 = 17.5
    # Last 8 days: [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 10.0, 7.5] = 59.5
    r2 = recaps[1]
    assert r2["on_duty_today"] == 7.5
    assert r2["column_a_last_7_days"] == 52.5
    assert r2["column_b_available_tomorrow"] == 17.5
    assert r2["column_c_last_8_days"] == 59.5


def test_recap_reset_after_34_hour_restart():
    """Verify available hours resets to 70 after 34-hour restart."""
    prior_7_days = [9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0]  # 63.0 hrs
    daily_logs = [
        {"date": "2026-10-01", "totals": {"driving": 0.0, "on_duty_not_driving": 0.0}, "has_34h_restart": True},
        {"date": "2026-10-02", "totals": {"driving": 8.0, "on_duty_not_driving": 1.0}, "has_34h_restart": False},
    ]

    recaps = calculate_daily_recap(daily_logs, prior_7_days_on_duty=prior_7_days)
    assert recaps[0]["column_b_available_tomorrow"] == 70.0
    assert recaps[1]["column_b_available_tomorrow"] == 61.0  # 70 - 9 = 61
