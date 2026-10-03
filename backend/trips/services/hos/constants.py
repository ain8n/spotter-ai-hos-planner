"""
FMCSA Hours of Service (HOS) Constants for Property-Carrying CMV Drivers
Under 49 CFR Part 395 (70-hour / 8-day rule, no adverse conditions)
"""

# Maximum driving hours permitted within a duty window before requiring a 10-hour reset
MAX_DRIVING_HOURS_PER_SHIFT = 11.0

# Maximum consecutive duty window (hours) from shift start in which driving is permitted
MAX_DUTY_WINDOW_HOURS = 14.0

# Cumulative driving hours before a mandatory 30-minute break is required
DRIVING_HOURS_BEFORE_BREAK = 8.0

# Mandatory rest break duration in hours (30 minutes)
MANDATORY_BREAK_DURATION_HOURS = 0.5

# Standard consecutive rest duration to reset 11-hour driving and 14-hour window (10 hours)
DAILY_REST_DURATION_HOURS = 10.0

# Maximum on-duty hours in any rolling 8-consecutive-day period
CYCLE_LIMIT_HOURS = 70.0

# Number of rolling days for the cycle
CYCLE_DAYS = 8

# Consecutive off-duty hours required for a 34-hour restart (resets 70-hour cycle)
RESTART_DURATION_HOURS = 34.0

# Maximum distance in statute miles between fueling stops
MAX_FUEL_INTERVAL_MILES = 1000.0

# Standard duration for a fuel stop in hours (30 minutes)
FUELING_DURATION_HOURS = 0.5

# Mandatory loading / pickup duration in hours (1 hour)
PICKUP_DURATION_HOURS = 1.0

# Mandatory unloading / dropoff duration in hours (1 hour)
DROPOFF_DURATION_HOURS = 1.0

# Pre-trip vehicle inspection duration in hours (15 minutes)
PRE_TRIP_INSPECTION_HOURS = 0.25

# Post-trip inspection duration in hours (15 minutes)
POST_TRIP_INSPECTION_HOURS = 0.25

# Average commercial truck cruising speed (mph) on highways when route duration not provided
DEFAULT_TRUCK_SPEED_MPH = 55.0

# Duty Status Constants matching FMCSR 4-line Grid
STATUS_OFF_DUTY = "OFF_DUTY"
STATUS_SLEEPER_BERTH = "SLEEPER_BERTH"
STATUS_DRIVING = "DRIVING"
STATUS_ON_DUTY_NOT_DRIVING = "ON_DUTY_NOT_DRIVING"

STATUS_LINE_MAP = {
    STATUS_OFF_DUTY: 1,
    STATUS_SLEEPER_BERTH: 2,
    STATUS_DRIVING: 3,
    STATUS_ON_DUTY_NOT_DRIVING: 4,
}

STATUS_DISPLAY_NAMES = {
    STATUS_OFF_DUTY: "Off Duty",
    STATUS_SLEEPER_BERTH: "Sleeper Berth",
    STATUS_DRIVING: "Driving",
    STATUS_ON_DUTY_NOT_DRIVING: "On Duty (Not Driving)",
}
