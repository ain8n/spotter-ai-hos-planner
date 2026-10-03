"""
FMCSA Hours of Service (HOS) Simulation Engine
Deterministic HOS planning for US Property-Carrying CMV Drivers under 70-hour / 8-day rules.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import math

from .constants import (
    MAX_DRIVING_HOURS_PER_SHIFT,
    MAX_DUTY_WINDOW_HOURS,
    DRIVING_HOURS_BEFORE_BREAK,
    MANDATORY_BREAK_DURATION_HOURS,
    DAILY_REST_DURATION_HOURS,
    CYCLE_LIMIT_HOURS,
    RESTART_DURATION_HOURS,
    MAX_FUEL_INTERVAL_MILES,
    FUELING_DURATION_HOURS,
    PICKUP_DURATION_HOURS,
    DROPOFF_DURATION_HOURS,
    PRE_TRIP_INSPECTION_HOURS,
    POST_TRIP_INSPECTION_HOURS,
    DEFAULT_TRUCK_SPEED_MPH,
    STATUS_OFF_DUTY,
    STATUS_SLEEPER_BERTH,
    STATUS_DRIVING,
    STATUS_ON_DUTY_NOT_DRIVING,
    STATUS_LINE_MAP,
)
from ..geocoding.timezone import get_zoneinfo, determine_timezone_from_coords


class HOSPlanResult:
    def __init__(
        self,
        timeline_events: List[Dict[str, Any]],
        stops: List[Dict[str, Any]],
        summary: Dict[str, Any],
        warnings: List[str],
    ):
        self.timeline_events = timeline_events
        self.stops = stops
        self.summary = summary
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeline_events": self.timeline_events,
            "stops": self.stops,
            "summary": self.summary,
            "warnings": self.warnings,
        }


class HOSEngine:
    """
    Simulates a compliant HOS trip schedule for property-carrying drivers.
    Evaluates limiting constraints continuously along route legs.
    """

    def __init__(
        self,
        current_cycle_used_hrs: float = 0.0,
        start_datetime: datetime = None,
        average_speed_mph: float = DEFAULT_TRUCK_SPEED_MPH,
        timezone_name: str = None,
    ):
        self.initial_cycle_used = max(0.0, min(70.0, float(current_cycle_used_hrs)))
        self.timezone_name = timezone_name or "America/Chicago"
        self.tz = get_zoneinfo(self.timezone_name)

        if start_datetime is not None:
            if start_datetime.tzinfo is None:
                self.start_datetime = start_datetime.replace(tzinfo=self.tz)
            else:
                self.start_datetime = start_datetime.astimezone(self.tz)
        else:
            now_in_tz = datetime.now(self.tz)
            self.start_datetime = now_in_tz.replace(hour=6, minute=0, second=0, microsecond=0)

        self.average_speed = max(30.0, min(75.0, float(average_speed_mph)))
        self.warnings: List[str] = []
        self.stops: List[Dict[str, Any]] = []
        self.timeline_events: List[Dict[str, Any]] = []

    def plan_trip(
        self,
        current_loc: Dict[str, Any],
        pickup_loc: Dict[str, Any],
        dropoff_loc: Dict[str, Any],
        leg1_info: Dict[str, Any],  # current -> pickup
        leg2_info: Dict[str, Any],  # pickup -> dropoff
    ) -> HOSPlanResult:
        """
        Plans the complete journey through all legs with compliant HOS stops.
        """
        self.warnings = []
        self.stops = []
        self.timeline_events = []

        # Current simulation state
        sim_time = self.start_datetime
        current_lat = current_loc.get("lat", 0.0)
        current_lng = current_loc.get("lng", 0.0)
        current_name = current_loc.get("name", "Origin")

        # Start Day 1 with initial off-duty from midnight if start_datetime is after midnight
        midnight_today = sim_time.replace(hour=0, minute=0, second=0, microsecond=0)
        if sim_time > midnight_today:
            initial_off_hrs = (sim_time - midnight_today).total_seconds() / 3600.0
            self._add_event(
                start_time=midnight_today,
                end_time=sim_time,
                duration_hrs=initial_off_hrs,
                status=STATUS_OFF_DUTY,
                activity_type="INITIAL_OFF_DUTY",
                location_name=current_name,
                lat=current_lat,
                lng=current_lng,
                start_odo=0.0,
                end_odo=0.0,
                notes="Initial off-duty rest prior to dispatch",
            )

        cycle_used = self.initial_cycle_used
        shift_driving_hrs = 0.0
        shift_window_elapsed = 0.0
        driving_since_break = 0.0
        miles_since_fuel = 0.0
        total_odometer = 0.0

        # Check if driver starts with high cycle used (>= 70 hours or < 1.5 hrs remaining)
        if cycle_used >= CYCLE_LIMIT_HOURS - 1.0:
            self.warnings.append(
                f"Driver began trip with {cycle_used:.1f} hours on the 70-hour cycle. A mandatory 34-hour restart was inserted before departure."
            )
            restart_end = sim_time + timedelta(hours=RESTART_DURATION_HOURS)
            self._add_event(
                start_time=sim_time,
                end_time=restart_end,
                duration_hrs=RESTART_DURATION_HOURS,
                status=STATUS_OFF_DUTY,
                activity_type="RESTART_34",
                location_name=current_name,
                lat=current_lat,
                lng=current_lng,
                start_odo=total_odometer,
                end_odo=total_odometer,
                notes="34-Hour Restart (Cycle reset to 0.0 hrs)",
            )
            self._add_stop(
                stop_type="RESTART_34",
                name=current_name,
                lat=current_lat,
                lng=current_lng,
                arrival_time=sim_time,
                departure_time=restart_end,
                duration_hrs=RESTART_DURATION_HOURS,
                mile_marker=total_odometer,
                reason="34-Hour Restart to reset 70-hour / 8-day cycle",
            )
            sim_time = restart_end
            cycle_used = 0.0
            shift_driving_hrs = 0.0
            shift_window_elapsed = 0.0
            driving_since_break = 0.0

        # Initial Pre-Trip Inspection (15 min On Duty Not Driving)
        pre_trip_end = sim_time + timedelta(hours=PRE_TRIP_INSPECTION_HOURS)
        self._add_event(
            start_time=sim_time,
            end_time=pre_trip_end,
            duration_hrs=PRE_TRIP_INSPECTION_HOURS,
            status=STATUS_ON_DUTY_NOT_DRIVING,
            activity_type="PRE_TRIP",
            location_name=current_name,
            lat=current_lat,
            lng=current_lng,
            start_odo=total_odometer,
            end_odo=total_odometer,
            notes="Pre-trip vehicle inspection & paperwork",
        )
        self._add_stop(
            stop_type="START",
            name=current_name,
            lat=current_lat,
            lng=current_lng,
            arrival_time=sim_time,
            departure_time=pre_trip_end,
            duration_hrs=PRE_TRIP_INSPECTION_HOURS,
            mile_marker=total_odometer,
            reason="Trip start / Pre-trip inspection",
        )
        sim_time = pre_trip_end
        shift_window_elapsed += PRE_TRIP_INSPECTION_HOURS
        cycle_used += PRE_TRIP_INSPECTION_HOURS

        # === LEG 1: Current -> Pickup ===
        leg1_miles = float(leg1_info.get("distance_miles", 0.0))
        leg1_waypoints = leg1_info.get("waypoints", [])
        leg1_geometry = leg1_info.get("geometry", [])
        if not leg1_waypoints:
            leg1_waypoints = [
                {"lat": current_lat, "lng": current_lng, "name": current_name, "fraction": 0.0},
                {"lat": pickup_loc.get("lat", 0.0), "lng": pickup_loc.get("lng", 0.0), "name": pickup_loc.get("name", "Pickup"), "fraction": 1.0},
            ]

        sim_time, cycle_used, shift_driving_hrs, shift_window_elapsed, driving_since_break, miles_since_fuel, total_odometer, current_lat, current_lng, current_name = self._simulate_driving_leg(
            leg_name="Current to Pickup",
            leg_miles=leg1_miles,
            waypoints=leg1_waypoints,
            geometry=leg1_geometry,
            sim_time=sim_time,
            cycle_used=cycle_used,
            shift_driving_hrs=shift_driving_hrs,
            shift_window_elapsed=shift_window_elapsed,
            driving_since_break=driving_since_break,
            miles_since_fuel=miles_since_fuel,
            total_odometer=total_odometer,
            start_loc_name=current_name,
            end_loc_name=pickup_loc.get("name", "Pickup"),
        )

        # === PICKUP STOP: 1 Hour On Duty Not Driving ===
        # Ensure we have enough 14-hr window / cycle for pickup.
        if (shift_window_elapsed + PICKUP_DURATION_HOURS > MAX_DUTY_WINDOW_HOURS) or (cycle_used + PICKUP_DURATION_HOURS > CYCLE_LIMIT_HOURS):
            # If 14-hour window would be exceeded, take a 10-hour rest before pickup
            rest_end = sim_time + timedelta(hours=DAILY_REST_DURATION_HOURS)
            self._add_event(
                start_time=sim_time,
                end_time=rest_end,
                duration_hrs=DAILY_REST_DURATION_HOURS,
                status=STATUS_SLEEPER_BERTH,
                activity_type="DAILY_REST",
                location_name=pickup_loc.get("name", "Pickup Location"),
                lat=pickup_loc.get("lat", current_lat),
                lng=pickup_loc.get("lng", current_lng),
                start_odo=total_odometer,
                end_odo=total_odometer,
                notes="10-Hour Daily Rest prior to loading",
            )
            self._add_stop(
                stop_type="REST_10",
                name=pickup_loc.get("name", "Pickup Location"),
                lat=pickup_loc.get("lat", current_lat),
                lng=pickup_loc.get("lng", current_lng),
                arrival_time=sim_time,
                departure_time=rest_end,
                duration_hrs=DAILY_REST_DURATION_HOURS,
                mile_marker=total_odometer,
                reason="10-Hour Daily Rest reset",
            )
            sim_time = rest_end
            shift_driving_hrs = 0.0
            shift_window_elapsed = 0.0
            driving_since_break = 0.0

        pickup_name = pickup_loc.get("name", "Pickup Location")
        pickup_lat = pickup_loc.get("lat", current_lat)
        pickup_lng = pickup_loc.get("lng", current_lng)
        pickup_end = sim_time + timedelta(hours=PICKUP_DURATION_HOURS)

        self._add_event(
            start_time=sim_time,
            end_time=pickup_end,
            duration_hrs=PICKUP_DURATION_HOURS,
            status=STATUS_ON_DUTY_NOT_DRIVING,
            activity_type="PICKUP",
            location_name=pickup_name,
            lat=pickup_lat,
            lng=pickup_lng,
            start_odo=total_odometer,
            end_odo=total_odometer,
            notes="Loading freight at pickup facility (1.0 hr On Duty)",
        )
        self._add_stop(
            stop_type="PICKUP",
            name=pickup_name,
            lat=pickup_lat,
            lng=pickup_lng,
            arrival_time=sim_time,
            departure_time=pickup_end,
            duration_hrs=PICKUP_DURATION_HOURS,
            mile_marker=total_odometer,
            reason="Pickup / Loading cargo (1 hr On-Duty)",
        )
        sim_time = pickup_end
        shift_window_elapsed += PICKUP_DURATION_HOURS
        cycle_used += PICKUP_DURATION_HOURS
        driving_since_break = 0.0  # 1 hour non-driving satisfies >= 30 min break rule
        current_lat, current_lng, current_name = pickup_lat, pickup_lng, pickup_name

        # === LEG 2: Pickup -> Dropoff ===
        leg2_miles = float(leg2_info.get("distance_miles", 0.0))
        leg2_waypoints = leg2_info.get("waypoints", [])
        leg2_geometry = leg2_info.get("geometry", [])
        if not leg2_waypoints:
            leg2_waypoints = [
                {"lat": pickup_lat, "lng": pickup_lng, "name": pickup_name, "fraction": 0.0},
                {"lat": dropoff_loc.get("lat", 0.0), "lng": dropoff_loc.get("lng", 0.0), "name": dropoff_loc.get("name", "Dropoff"), "fraction": 1.0},
            ]

        sim_time, cycle_used, shift_driving_hrs, shift_window_elapsed, driving_since_break, miles_since_fuel, total_odometer, current_lat, current_lng, current_name = self._simulate_driving_leg(
            leg_name="Pickup to Dropoff",
            leg_miles=leg2_miles,
            waypoints=leg2_waypoints,
            geometry=leg2_geometry,
            sim_time=sim_time,
            cycle_used=cycle_used,
            shift_driving_hrs=shift_driving_hrs,
            shift_window_elapsed=shift_window_elapsed,
            driving_since_break=driving_since_break,
            miles_since_fuel=miles_since_fuel,
            total_odometer=total_odometer,
            start_loc_name=pickup_name,
            end_loc_name=dropoff_loc.get("name", "Dropoff"),
        )

        # === DROPOFF STOP: 1 Hour On Duty Not Driving ===
        dropoff_name = dropoff_loc.get("name", "Dropoff Location")
        dropoff_lat = dropoff_loc.get("lat", current_lat)
        dropoff_lng = dropoff_loc.get("lng", current_lng)
        dropoff_end = sim_time + timedelta(hours=DROPOFF_DURATION_HOURS)

        self._add_event(
            start_time=sim_time,
            end_time=dropoff_end,
            duration_hrs=DROPOFF_DURATION_HOURS,
            status=STATUS_ON_DUTY_NOT_DRIVING,
            activity_type="DROPOFF",
            location_name=dropoff_name,
            lat=dropoff_lat,
            lng=dropoff_lng,
            start_odo=total_odometer,
            end_odo=total_odometer,
            notes="Unloading freight at destination facility (1.0 hr On Duty)",
        )
        self._add_stop(
            stop_type="DROPOFF",
            name=dropoff_name,
            lat=dropoff_lat,
            lng=dropoff_lng,
            arrival_time=sim_time,
            departure_time=dropoff_end,
            duration_hrs=DROPOFF_DURATION_HOURS,
            mile_marker=total_odometer,
            reason="Dropoff / Unloading cargo (1 hr On-Duty)",
        )
        sim_time = dropoff_end
        shift_window_elapsed += DROPOFF_DURATION_HOURS
        cycle_used += DROPOFF_DURATION_HOURS

        # Post-Trip Inspection (15 min)
        post_trip_end = sim_time + timedelta(hours=POST_TRIP_INSPECTION_HOURS)
        self._add_event(
            start_time=sim_time,
            end_time=post_trip_end,
            duration_hrs=POST_TRIP_INSPECTION_HOURS,
            status=STATUS_ON_DUTY_NOT_DRIVING,
            activity_type="POST_TRIP",
            location_name=dropoff_name,
            lat=dropoff_lat,
            lng=dropoff_lng,
            start_odo=total_odometer,
            end_odo=total_odometer,
            notes="Post-trip inspection, paperwork & sign-off",
        )
        sim_time = post_trip_end
        shift_window_elapsed += POST_TRIP_INSPECTION_HOURS
        cycle_used += POST_TRIP_INSPECTION_HOURS

        # Complete final day with Off-Duty until midnight so log is a complete 24-hour day
        next_midnight = sim_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        remaining_day_hrs = (next_midnight - sim_time).total_seconds() / 3600.0
        if remaining_day_hrs > 0.001:
            self._add_event(
                start_time=sim_time,
                end_time=next_midnight,
                duration_hrs=remaining_day_hrs,
                status=STATUS_OFF_DUTY,
                activity_type="POST_TRIP_OFF_DUTY",
                location_name=dropoff_name,
                lat=dropoff_lat,
                lng=dropoff_lng,
                start_odo=total_odometer,
                end_odo=total_odometer,
                notes="Released from duty - Off Duty",
            )
            sim_time = next_midnight

        # Calculate trip summary
        total_miles = round(total_odometer, 1)
        total_driving_hrs = round(
            sum(e["duration_hours"] for e in self.timeline_events if e["status"] == STATUS_DRIVING), 2
        )
        total_on_duty_hrs = round(
            sum(
                e["duration_hours"]
                for e in self.timeline_events
                if e["status"] in (STATUS_DRIVING, STATUS_ON_DUTY_NOT_DRIVING)
            ),
            2,
        )
        total_duration_hrs = round((sim_time - self.start_datetime).total_seconds() / 3600.0, 2)
        num_fuel_stops = sum(1 for s in self.stops if s["stop_type"] == "FUEL")
        num_rest_breaks = sum(1 for s in self.stops if s["stop_type"] == "REST_30")
        num_daily_rests = sum(1 for s in self.stops if s["stop_type"] == "REST_10")
        num_restarts = sum(1 for s in self.stops if s["stop_type"] == "RESTART_34")

        summary = {
            "timezone": self.timezone_name,
            "total_distance_miles": total_miles,
            "total_driving_hours": total_driving_hrs,
            "total_on_duty_hours": total_on_duty_hrs,
            "total_trip_duration_hours": total_duration_hrs,
            "start_time": self.start_datetime.isoformat(),
            "end_time": sim_time.isoformat(),
            "fuel_stops_count": num_fuel_stops,
            "rest_breaks_30m_count": num_rest_breaks,
            "daily_rests_10h_count": num_daily_rests,
            "restarts_34h_count": num_restarts,
            "initial_cycle_used_hrs": self.initial_cycle_used,
            "final_cycle_used_hrs": round(cycle_used, 2),
        }

        return HOSPlanResult(
            timeline_events=self.timeline_events,
            stops=self.stops,
            summary=summary,
            warnings=self.warnings,
        )

    def _simulate_driving_leg(
        self,
        leg_name: str,
        leg_miles: float,
        waypoints: List[Dict[str, Any]],
        geometry: List[List[float]],
        sim_time: datetime,
        cycle_used: float,
        shift_driving_hrs: float,
        shift_window_elapsed: float,
        driving_since_break: float,
        miles_since_fuel: float,
        total_odometer: float,
        start_loc_name: str,
        end_loc_name: str,
    ) -> Tuple[datetime, float, float, float, float, float, float, float, float, str]:
        """
        Drives along a route leg, stopping for breaks, fuel, 10h rest, and 34h restart as required.
        """
        remaining_leg_miles = float(leg_miles)
        leg_start_odo = total_odometer
        cur_lat = waypoints[0]["lat"] if waypoints else 0.0
        cur_lng = waypoints[0]["lng"] if waypoints else 0.0
        cur_loc_name = start_loc_name

        if remaining_leg_miles <= 0.01:
            return (
                sim_time,
                cycle_used,
                shift_driving_hrs,
                shift_window_elapsed,
                driving_since_break,
                miles_since_fuel,
                total_odometer,
                cur_lat,
                cur_lng,
                cur_loc_name,
            )

        speed = self.average_speed
        step_index = 0

        while remaining_leg_miles > 0.01:
            step_index += 1
            if step_index > 500:  # safety break against infinite loop
                self.warnings.append("Simulation step limit reached; finalizing route leg.")
                break

            # 1. Calculate limiting factors in terms of available driving hours:
            avail_hrs_dest = remaining_leg_miles / speed
            miles_to_fuel = max(0.0, MAX_FUEL_INTERVAL_MILES - miles_since_fuel)
            avail_hrs_fuel = miles_to_fuel / speed if miles_to_fuel > 0 else 0.0
            avail_hrs_break = max(0.0, DRIVING_HOURS_BEFORE_BREAK - driving_since_break)
            avail_hrs_11 = max(0.0, MAX_DRIVING_HOURS_PER_SHIFT - shift_driving_hrs)
            avail_hrs_14 = max(0.0, MAX_DUTY_WINDOW_HOURS - shift_window_elapsed)
            avail_hrs_cycle = max(0.0, CYCLE_LIMIT_HOURS - cycle_used)

            drive_hrs = min(
                avail_hrs_dest,
                avail_hrs_fuel,
                avail_hrs_break,
                avail_hrs_11,
                avail_hrs_14,
                avail_hrs_cycle,
            )

            if drive_hrs > 0.01:
                drive_miles = min(remaining_leg_miles, drive_hrs * speed)
                drive_end_time = sim_time + timedelta(hours=drive_hrs)
                end_odo = total_odometer + drive_miles

                fraction = min(1.0, (end_odo - leg_start_odo) / leg_miles) if leg_miles > 0 else 1.0
                next_lat, next_lng, next_loc_name = self._interpolate_waypoint(
                    waypoints, geometry, fraction, start_loc_name, end_loc_name, end_odo
                )

                self._add_event(
                    start_time=sim_time,
                    end_time=drive_end_time,
                    duration_hrs=drive_hrs,
                    status=STATUS_DRIVING,
                    activity_type="DRIVING",
                    location_name=f"{cur_loc_name} to {next_loc_name}",
                    lat=next_lat,
                    lng=next_lng,
                    start_odo=total_odometer,
                    end_odo=end_odo,
                    notes=f"Driving ({drive_miles:.1f} mi at ~{speed:.0f} mph)",
                )

                sim_time = drive_end_time
                total_odometer = end_odo
                remaining_leg_miles = max(0.0, remaining_leg_miles - drive_miles)
                miles_since_fuel += drive_miles
                shift_driving_hrs += drive_hrs
                shift_window_elapsed += drive_hrs
                driving_since_break += drive_hrs
                cycle_used += drive_hrs
                cur_lat, cur_lng, cur_loc_name = next_lat, next_lng, next_loc_name

            if remaining_leg_miles <= 0.01:
                break

            # Handle hit constraints in order of priority:
            # 1. 70-hour cycle limit reached -> 34-hour restart
            if cycle_used >= CYCLE_LIMIT_HOURS - 0.01:
                restart_end = sim_time + timedelta(hours=RESTART_DURATION_HOURS)
                self.warnings.append(
                    f"Driver reached 70-hour cycle limit at {cur_loc_name} (Mile {total_odometer:.1f}). A 34-hour restart was taken."
                )
                self._add_event(
                    start_time=sim_time,
                    end_time=restart_end,
                    duration_hrs=RESTART_DURATION_HOURS,
                    status=STATUS_OFF_DUTY,
                    activity_type="RESTART_34",
                    location_name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    start_odo=total_odometer,
                    end_odo=total_odometer,
                    notes="34-Hour Restart (Cycle reset)",
                )
                self._add_stop(
                    stop_type="RESTART_34",
                    name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    arrival_time=sim_time,
                    departure_time=restart_end,
                    duration_hrs=RESTART_DURATION_HOURS,
                    mile_marker=total_odometer,
                    reason="34-Hour Restart for 70-hour cycle reset",
                )
                sim_time = restart_end
                cycle_used = 0.0
                shift_driving_hrs = 0.0
                shift_window_elapsed = 0.0
                driving_since_break = 0.0
                continue

            # 2. 11-hour driving or 14-hour window limit reached -> 10-hour daily rest
            if (shift_driving_hrs >= MAX_DRIVING_HOURS_PER_SHIFT - 0.01) or (
                shift_window_elapsed >= MAX_DUTY_WINDOW_HOURS - 0.01
            ):
                reason_text = (
                    "11-Hour Driving Limit reached"
                    if shift_driving_hrs >= MAX_DRIVING_HOURS_PER_SHIFT - 0.01
                    else "14-Hour Duty Window reached"
                )
                rest_end = sim_time + timedelta(hours=DAILY_REST_DURATION_HOURS)
                self._add_event(
                    start_time=sim_time,
                    end_time=rest_end,
                    duration_hrs=DAILY_REST_DURATION_HOURS,
                    status=STATUS_SLEEPER_BERTH,
                    activity_type="DAILY_REST",
                    location_name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    start_odo=total_odometer,
                    end_odo=total_odometer,
                    notes=f"10-Hour Daily Rest ({reason_text})",
                )
                self._add_stop(
                    stop_type="REST_10",
                    name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    arrival_time=sim_time,
                    departure_time=rest_end,
                    duration_hrs=DAILY_REST_DURATION_HOURS,
                    mile_marker=total_odometer,
                    reason=f"10-Hour Daily Rest ({reason_text})",
                )
                sim_time = rest_end
                shift_driving_hrs = 0.0
                shift_window_elapsed = 0.0
                driving_since_break = 0.0
                continue

            # 3. Fuel stop required (at least every 1,000 miles)
            if miles_since_fuel >= MAX_FUEL_INTERVAL_MILES - 1.0:
                fuel_end = sim_time + timedelta(hours=FUELING_DURATION_HOURS)
                self._add_event(
                    start_time=sim_time,
                    end_time=fuel_end,
                    duration_hrs=FUELING_DURATION_HOURS,
                    status=STATUS_ON_DUTY_NOT_DRIVING,
                    activity_type="FUEL_STOP",
                    location_name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    start_odo=total_odometer,
                    end_odo=total_odometer,
                    notes=f"Fuel Stop (1,000 mi requirement reached at Mile {total_odometer:.1f})",
                )
                self._add_stop(
                    stop_type="FUEL",
                    name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    arrival_time=sim_time,
                    departure_time=fuel_end,
                    duration_hrs=FUELING_DURATION_HOURS,
                    mile_marker=total_odometer,
                    reason="Mandatory fuel stop (< 1,000 miles)",
                )
                sim_time = fuel_end
                miles_since_fuel = 0.0
                shift_window_elapsed += FUELING_DURATION_HOURS
                cycle_used += FUELING_DURATION_HOURS
                driving_since_break = 0.0  # 30 min on-duty qualifies as rest break
                continue

            # 4. 8-hour driving limit reached -> 30-minute rest break
            if driving_since_break >= DRIVING_HOURS_BEFORE_BREAK - 0.01:
                break_end = sim_time + timedelta(hours=MANDATORY_BREAK_DURATION_HOURS)
                self._add_event(
                    start_time=sim_time,
                    end_time=break_end,
                    duration_hrs=MANDATORY_BREAK_DURATION_HOURS,
                    status=STATUS_OFF_DUTY,
                    activity_type="REST_BREAK",
                    location_name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    start_odo=total_odometer,
                    end_odo=total_odometer,
                    notes="Mandatory 30-Minute Rest Break (8 cumulative driving hours)",
                )
                self._add_stop(
                    stop_type="REST_30",
                    name=cur_loc_name,
                    lat=cur_lat,
                    lng=cur_lng,
                    arrival_time=sim_time,
                    departure_time=break_end,
                    duration_hrs=MANDATORY_BREAK_DURATION_HOURS,
                    mile_marker=total_odometer,
                    reason="30-Minute Rest Break (after 8h driving)",
                )
                sim_time = break_end
                shift_window_elapsed += MANDATORY_BREAK_DURATION_HOURS
                driving_since_break = 0.0
                continue

        return (
            sim_time,
            cycle_used,
            shift_driving_hrs,
            shift_window_elapsed,
            driving_since_break,
            miles_since_fuel,
            total_odometer,
            cur_lat,
            cur_lng,
            cur_loc_name,
        )

    def _interpolate_waypoint(
        self,
        waypoints: List[Dict[str, Any]],
        geometry: List[List[float]],
        fraction: float,
        start_name: str,
        end_name: str,
        odometer: float,
    ) -> Tuple[float, float, str]:
        """
        Calculates geographic coordinates along route geometry and descriptive location name.
        """
        fraction = max(0.0, min(1.0, fraction))

        # 1. First interpolate exact geographic coordinates along detailed polyline geometry if available
        lat, lng = 0.0, 0.0
        if geometry and len(geometry) > 0:
            if len(geometry) == 1 or fraction <= 0.0:
                lat, lng = geometry[0][0], geometry[0][1]
            elif fraction >= 1.0:
                lat, lng = geometry[-1][0], geometry[-1][1]
            else:
                n_geom = len(geometry) - 1
                scaled_geom = fraction * n_geom
                g_idx1 = int(math.floor(scaled_geom))
                g_idx2 = min(n_geom, g_idx1 + 1)
                g_sub = scaled_geom - g_idx1
                lat = geometry[g_idx1][0] + (geometry[g_idx2][0] - geometry[g_idx1][0]) * g_sub
                lng = geometry[g_idx1][1] + (geometry[g_idx2][1] - geometry[g_idx1][1]) * g_sub
        elif waypoints and len(waypoints) > 0:
            if len(waypoints) == 1 or fraction <= 0.0:
                lat, lng = waypoints[0]["lat"], waypoints[0]["lng"]
            elif fraction >= 1.0:
                lat, lng = waypoints[-1]["lat"], waypoints[-1]["lng"]
            else:
                n_wp = len(waypoints) - 1
                scaled_wp = fraction * n_wp
                w_idx1 = int(math.floor(scaled_wp))
                w_idx2 = min(n_wp, w_idx1 + 1)
                w_sub = scaled_wp - w_idx1
                lat = waypoints[w_idx1]["lat"] + (waypoints[w_idx2]["lat"] - waypoints[w_idx1]["lat"]) * w_sub
                lng = waypoints[w_idx1]["lng"] + (waypoints[w_idx2]["lng"] - waypoints[w_idx1]["lng"]) * w_sub

        # 2. Determine location description
        if not waypoints:
            return round(lat, 5), round(lng, 5), f"En route {start_name} -> {end_name} (Mile {odometer:.1f})"

        n = len(waypoints) - 1
        scaled_idx = fraction * n
        idx1 = int(math.floor(scaled_idx))
        idx2 = min(n, idx1 + 1)
        sub_frac = scaled_idx - idx1

        w1 = waypoints[idx1]
        w2 = waypoints[idx2]

        if sub_frac < 0.3:
            name = w1.get("name") or f"Near {start_name}"
        elif sub_frac > 0.7:
            name = w2.get("name") or f"Near {end_name}"
        else:
            name = f"En route {start_name} -> {end_name} (Mile {odometer:.1f})"

        return round(lat, 5), round(lng, 5), name

    def _add_event(
        self,
        start_time: datetime,
        end_time: datetime,
        duration_hrs: float,
        status: str,
        activity_type: str,
        location_name: str,
        lat: float,
        lng: float,
        start_odo: float,
        end_odo: float,
        notes: str,
    ):
        event_dict = {
            "id": len(self.timeline_events) + 1,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "start_dt": start_time,
            "end_dt": end_time,
            "duration_hours": round(duration_hrs, 2),
            "status": status,
            "status_line": STATUS_LINE_MAP.get(status, 1),
            "activity_type": activity_type,
            "location_name": location_name,
            "latitude": round(lat, 5),
            "longitude": round(lng, 5),
            "start_odometer": round(start_odo, 1),
            "end_odometer": round(end_odo, 1),
            "distance_miles": round(end_odo - start_odo, 1),
            "notes": notes,
        }
        self.timeline_events.append(event_dict)

    def _add_stop(
        self,
        stop_type: str,
        name: str,
        lat: float,
        lng: float,
        arrival_time: datetime,
        departure_time: datetime,
        duration_hrs: float,
        mile_marker: float,
        reason: str,
    ):
        stop_dict = {
            "stop_number": len(self.stops) + 1,
            "stop_type": stop_type,
            "name": name,
            "latitude": round(lat, 5),
            "longitude": round(lng, 5),
            "arrival_time": arrival_time.isoformat(),
            "departure_time": departure_time.isoformat(),
            "duration_hours": round(duration_hrs, 2),
            "mile_marker": round(mile_marker, 1),
            "reason": reason,
        }
        self.stops.append(stop_dict)
