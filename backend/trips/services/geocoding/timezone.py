"""
Timezone determination service using geographic coordinates (latitude, longitude).
Maps any coordinate location to its accurate IANA timezone identifier.
"""

import logging
from typing import Optional
from zoneinfo import ZoneInfo

try:
    from timezonefinder import TimezoneFinder
    _tf: Optional[TimezoneFinder] = TimezoneFinder()
except Exception as e:
    _tf = None
    logging.getLogger(__name__).warning("TimezoneFinder initialization failed: %s", str(e))

logger = logging.getLogger(__name__)


def determine_timezone_from_coords(lat: float, lng: float) -> str:
    """
    Determines the official IANA timezone identifier (e.g. 'America/Chicago',
    'America/New_York', 'America/Denver', 'America/Los_Angeles') based on exact geographic coordinates.
    """
    if lat is None or lng is None:
        return "America/Chicago"

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (ValueError, TypeError):
        return "America/Chicago"

    # 1. Use high-accuracy offline polygon lookup
    if _tf is not None:
        try:
            tz = _tf.timezone_at(lat=lat_f, lng=lng_f)
            if tz:
                return tz
        except Exception as e:
            logger.warning("Error looking up timezone for (%s, %s): %s", lat, lng, str(e))

    # 2. Fast bounding-box / longitude fallback for North America
    if 24.0 <= lat_f <= 50.0:
        if lng_f < -114.5:
            return "America/Los_Angeles"
        elif lng_f < -102.0:
            return "America/Denver"
        elif lng_f < -85.0:
            return "America/Chicago"
        else:
            return "America/New_York"
    elif lat_f > 50.0 and lng_f < -130.0:
        return "America/Anchorage"
    elif 18.0 <= lat_f <= 23.0 and -161.0 <= lng_f <= -154.0:
        return "Pacific/Honolulu"

    # Default fallback timezone for US freight network
    return "America/Chicago"


def get_zoneinfo(tz_name: str) -> ZoneInfo:
    """
    Returns a valid ZoneInfo object, falling back safely to America/Chicago if invalid.
    """
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("America/Chicago")
