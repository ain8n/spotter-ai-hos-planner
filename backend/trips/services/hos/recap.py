"""
FMCSA 70-Hour / 8-Day Rolling Recap Calculator
Calculates daily on-duty totals and rolling 7-day and 8-day cumulative duty hours
in compliance with 49 CFR § 395.3(b) and standard FMCSR Driver's Daily Log recap table.
"""

from typing import List, Dict, Any
from .constants import CYCLE_LIMIT_HOURS


def calculate_daily_recap(
    daily_logs: List[Dict[str, Any]],
    prior_7_days_on_duty: List[float] = None,
    current_cycle_used_hrs: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Computes the 70-hour / 8-day recap table for each day of the trip.

    For each day d:
      - on_duty_today: Total Line 3 (Driving) + Line 4 (On Duty Not Driving) today
      - total_7_days (Column A): Total hours on duty last 7 days including today
      - available_tomorrow (Column B): 70.0 - Column A (or 70.0 if 34-hr restart taken)
      - total_8_days (Column C): Total hours on duty last 8 days including today

    Args:
        daily_logs: List of daily log dicts for the trip
        prior_7_days_on_duty: List of 7 numbers representing on-duty hours for days D-7 through D-1
        current_cycle_used_hrs: Fallback if prior_7_days_on_duty not provided
    """
    num_days = len(daily_logs)
    if num_days == 0:
        return []

    # If prior 7 days not explicitly provided, distribute current_cycle_used_hrs across prior 7 days
    if not prior_7_days_on_duty or len(prior_7_days_on_duty) < 7:
        avg_prior = max(0.0, current_cycle_used_hrs) / 7.0
        history = [round(avg_prior, 2)] * 7
        # Adjust last day so exact sum matches current_cycle_used_hrs
        diff = current_cycle_used_hrs - sum(history)
        history[-1] = round(history[-1] + diff, 2)
    else:
        history = [round(float(h), 2) for h in prior_7_days_on_duty[-7:]]

    # Combined full list of daily on-duty hours: historical 7 days + trip days
    # History corresponds to days [-7, -6, -5, -4, -3, -2, -1] (0-indexed 0..6)
    all_on_duty = list(history)
    recap_results = []
    restart_active = False

    for i, log in enumerate(daily_logs):
        driving_hrs = float(log.get("totals", {}).get("driving", 0.0))
        on_duty_nd_hrs = float(log.get("totals", {}).get("on_duty_not_driving", 0.0))
        on_duty_today = round(driving_hrs + on_duty_nd_hrs, 2)
        all_on_duty.append(on_duty_today)

        # Check if a 34-hour restart was completed on or before this day
        had_restart = log.get("has_34h_restart", False)
        if had_restart:
            restart_active = True

        # Index of today in all_on_duty is 7 + i
        today_idx = 7 + i

        # Column A: Last 7 days including today -> indices [today_idx - 6 : today_idx + 1]
        last_7_days_window = all_on_duty[max(0, today_idx - 6) : today_idx + 1]
        total_last_7_days = round(sum(last_7_days_window), 2)

        # Column C: Last 8 days including today -> indices [today_idx - 7 : today_idx + 1]
        last_8_days_window = all_on_duty[max(0, today_idx - 7) : today_idx + 1]
        total_last_8_days = round(sum(last_8_days_window), 2)

        # Column B: Total hours available tomorrow = 70.0 - Column A (or 70.0 if restart reset)
        if restart_active:
            # If restart happened, only count hours accumulated since the restart
            hours_since_restart = on_duty_today
            available_tomorrow = round(max(0.0, CYCLE_LIMIT_HOURS - hours_since_restart), 2)
        else:
            available_tomorrow = round(max(0.0, CYCLE_LIMIT_HOURS - total_last_7_days), 2)

        recap = {
            "day_number": i + 1,
            "date": log.get("date"),
            "on_duty_today": on_duty_today,
            "total_lines_3_and_4": on_duty_today,
            "column_a_last_7_days": total_last_7_days,
            "column_b_available_tomorrow": available_tomorrow,
            "column_c_last_8_days": total_last_8_days,
            "restart_applied": restart_active or had_restart,
            "is_in_compliance": total_last_8_days <= CYCLE_LIMIT_HOURS or restart_active,
        }
        recap_results.append(recap)

    return recap_results
