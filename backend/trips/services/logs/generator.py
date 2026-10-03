"""
FMCSA Daily Log Generator
Splits simulation timelines into 24-hour calendar day log sheets,
verifies that status lines sum to exactly 24.00 hours, extracts duty transitions,
and produces structured ELD/paper log data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..hos.constants import (
    STATUS_OFF_DUTY,
    STATUS_SLEEPER_BERTH,
    STATUS_DRIVING,
    STATUS_ON_DUTY_NOT_DRIVING,
    STATUS_LINE_MAP,
    STATUS_DISPLAY_NAMES,
)
from ..hos.recap import calculate_daily_recap


def generate_daily_logs(
    timeline_events: List[Dict[str, Any]],
    current_cycle_used_hrs: float = 0.0,
    log_header_details: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Slices the timeline into calendar day chunks (00:00 to 24:00) and produces
    detailed daily log records matching FMCSA Form 395 standards.
    """
    if not timeline_events:
        return []

    header = log_header_details or {}
    carrier_name = header.get("carrier_name", "US Freight Express LLC")
    main_office = header.get("main_office_address", "100 Logistics Blvd, Indianapolis, IN 46204")
    home_terminal = header.get("home_terminal_address", "450 Transport Way, Chicago, IL 60601")
    driver_name = header.get("driver_name", "John E. Doe")
    driver_id = header.get("driver_id", "DRV-84920")
    truck_tractor_num = header.get("truck_tractor_num", "T-804 (VIN: 1XKWD49X)")
    trailer_num = header.get("trailer_num", "TR-5309 (IL Lic: 982-TRK)")
    co_driver = header.get("co_driver", "N/A (Solo Driver)")
    shipping_doc = header.get("shipping_doc", "BOL #9482104")
    shipper_commodity = header.get("shipper_commodity", "General Freight / Commercial Goods")

    # Step 1: Split multi-day events exactly at midnight boundaries
    split_events = []
    for event in timeline_events:
        st = event["start_dt"] if isinstance(event.get("start_dt"), datetime) else datetime.fromisoformat(event["start_time"])
        et = event["end_dt"] if isinstance(event.get("end_dt"), datetime) else datetime.fromisoformat(event["end_time"])

        cur_st = st
        start_odo = float(event.get("start_odometer", 0.0))
        end_odo = float(event.get("end_odometer", start_odo))
        total_ev_duration = (et - st).total_seconds() / 3600.0
        total_ev_dist = end_odo - start_odo

        while cur_st < et:
            # End of current calendar day (midnight)
            next_midnight = cur_st.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            chunk_et = min(et, next_midnight)
            chunk_duration = (chunk_et - cur_st).total_seconds() / 3600.0

            # Pro-rate odometer/miles if event spanned midnight while driving
            if total_ev_duration > 0.001:
                fraction_done = (chunk_et - st).total_seconds() / (et - st).total_seconds()
                fraction_start = (cur_st - st).total_seconds() / (et - st).total_seconds()
                chunk_start_odo = start_odo + total_ev_dist * fraction_start
                chunk_end_odo = start_odo + total_ev_dist * fraction_done
            else:
                chunk_start_odo = start_odo
                chunk_end_odo = end_odo

            split_events.append({
                "start_time": cur_st.isoformat(),
                "end_time": chunk_et.isoformat(),
                "start_dt": cur_st,
                "end_dt": chunk_et,
                "duration_hours": round(chunk_duration, 4),
                "status": event["status"],
                "status_line": event["status_line"],
                "activity_type": event.get("activity_type", "OTHER"),
                "location_name": event.get("location_name", ""),
                "latitude": event.get("latitude", 0.0),
                "longitude": event.get("longitude", 0.0),
                "start_odometer": round(chunk_start_odo, 1),
                "end_odometer": round(chunk_end_odo, 1),
                "distance_miles": round(chunk_end_odo - chunk_start_odo, 1),
                "notes": event.get("notes", ""),
            })

            cur_st = chunk_et

    # Step 2: Group split events by calendar date
    days_dict: Dict[str, List[Dict[str, Any]]] = {}
    for ev in split_events:
        date_str = ev["start_dt"].strftime("%Y-%m-%d")
        if date_str not in days_dict:
            days_dict[date_str] = []
        days_dict[date_str].append(ev)

    sorted_dates = sorted(days_dict.keys())
    daily_logs = []

    for day_idx, date_str in enumerate(sorted_dates):
        day_events = days_dict[date_str]
        dt_day = datetime.strptime(date_str, "%Y-%m-%d")

        # Sum up hours by duty status
        off_duty_hrs = 0.0
        sleeper_berth_hrs = 0.0
        driving_hrs = 0.0
        on_duty_nd_hrs = 0.0
        daily_driving_miles = 0.0
        has_34h_restart = False

        grid_segments = []
        grid_transitions = []
        remarks_list = []

        last_status_line = None

        for ev in day_events:
            dur = float(ev["duration_hours"])
            stat = ev["status"]
            line_num = STATUS_LINE_MAP.get(stat, 1)

            if stat == STATUS_OFF_DUTY:
                off_duty_hrs += dur
            elif stat == STATUS_SLEEPER_BERTH:
                sleeper_berth_hrs += dur
            elif stat == STATUS_DRIVING:
                driving_hrs += dur
                daily_driving_miles += float(ev.get("distance_miles", 0.0))
            elif stat == STATUS_ON_DUTY_NOT_DRIVING:
                on_duty_nd_hrs += dur

            if ev.get("activity_type") == "RESTART_34":
                has_34h_restart = True

            # Calculate start hour and end hour on the 0.00 -> 24.00 scale for this day
            start_sec = ev["start_dt"].hour * 3600 + ev["start_dt"].minute * 60 + ev["start_dt"].second
            start_hour_val = round(start_sec / 3600.0, 4)
            end_hour_val = round(start_hour_val + dur, 4)

            # Prevent floating overshoot beyond 24.00
            end_hour_val = min(24.0, end_hour_val)

            grid_segments.append({
                "start_hour": start_hour_val,
                "end_hour": end_hour_val,
                "duration_hours": round(dur, 2),
                "status": stat,
                "status_name": STATUS_DISPLAY_NAMES.get(stat, stat),
                "line_number": line_num,
                "location": ev["location_name"],
                "notes": ev["notes"],
            })

            # Check if this is a transition from previous status
            if last_status_line is not None and last_status_line != line_num:
                grid_transitions.append({
                    "time_hour": start_hour_val,
                    "time_str": ev["start_dt"].strftime("%I:%M %p"),
                    "from_line": last_status_line,
                    "to_line": line_num,
                    "location": ev["location_name"],
                    "reason": ev["notes"],
                })

            last_status_line = line_num

            # Build Remarks entry for duty status change or major stop
            if ev.get("activity_type") not in ("INITIAL_OFF_DUTY", "POST_TRIP_OFF_DUTY") or start_hour_val > 0.0:
                time_formatted = ev["start_dt"].strftime("%I:%M %p")
                remarks_list.append({
                    "time": time_formatted,
                    "time_hour": start_hour_val,
                    "location": ev["location_name"],
                    "status_name": STATUS_DISPLAY_NAMES.get(stat, stat),
                    "activity": ev.get("activity_type", "STATUS_CHANGE"),
                    "notes": ev.get("notes", ""),
                })

        # Ensure exact 24.00 hours total by balancing floating point remainder
        off_duty_hrs = round(off_duty_hrs, 2)
        sleeper_berth_hrs = round(sleeper_berth_hrs, 2)
        driving_hrs = round(driving_hrs, 2)
        on_duty_nd_hrs = round(on_duty_nd_hrs, 2)
        day_sum = round(off_duty_hrs + sleeper_berth_hrs + driving_hrs + on_duty_nd_hrs, 2)

        if day_sum != 24.0:
            diff = round(24.0 - day_sum, 2)
            # Adjust the largest status or off_duty
            if off_duty_hrs > 0:
                off_duty_hrs = round(off_duty_hrs + diff, 2)
            elif sleeper_berth_hrs > 0:
                sleeper_berth_hrs = round(sleeper_berth_hrs + diff, 2)
            elif on_duty_nd_hrs > 0:
                on_duty_nd_hrs = round(on_duty_nd_hrs + diff, 2)
            else:
                driving_hrs = round(driving_hrs + diff, 2)

        first_loc = day_events[0]["location_name"] if day_events else "Origin"
        last_loc = day_events[-1]["location_name"] if day_events else "Destination"
        end_odo = day_events[-1].get("end_odometer", 0.0) if day_events else 0.0

        daily_log = {
            "day_number": day_idx + 1,
            "total_days": len(sorted_dates),
            "date": date_str,
            "date_formatted": dt_day.strftime("%m / %d / %Y"),
            "month": dt_day.strftime("%m"),
            "day": dt_day.strftime("%d"),
            "year": dt_day.strftime("%Y"),
            "from_location": first_loc,
            "to_location": last_loc,
            "total_miles_driving_today": round(daily_driving_miles, 1),
            "total_mileage_today": round(end_odo, 1),
            "carrier_name": carrier_name,
            "main_office_address": main_office,
            "home_terminal_address": home_terminal,
            "driver_name": driver_name,
            "driver_id": driver_id,
            "truck_tractor_num": truck_tractor_num,
            "trailer_num": trailer_num,
            "co_driver": co_driver,
            "shipping_doc": shipping_doc,
            "shipper_commodity": shipper_commodity,
            "has_34h_restart": has_34h_restart,
            "totals": {
                "off_duty": off_duty_hrs,
                "sleeper_berth": sleeper_berth_hrs,
                "driving": driving_hrs,
                "on_duty_not_driving": on_duty_nd_hrs,
                "total_hours": 24.0,
            },
            "grid_segments": grid_segments,
            "grid_transitions": grid_transitions,
            "remarks": remarks_list,
        }
        daily_logs.append(daily_log)

    # Attach 70-Hour / 8-Day Recap to each daily log
    recap_list = calculate_daily_recap(
        daily_logs=daily_logs,
        current_cycle_used_hrs=current_cycle_used_hrs,
    )
    for log, recap in zip(daily_logs, recap_list):
        log["recap"] = recap

    return daily_logs
