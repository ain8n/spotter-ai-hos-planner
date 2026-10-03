/**
 * Geographic coordinate to IANA Timezone determination utility.
 * Resolves accurate IANA timezone identifiers (e.g. 'America/Chicago', 'America/New_York')
 * from latitude & longitude coordinates.
 */

export function getTimezoneFromCoordinates(lat, lng) {
  if (lat == null || lng == null || isNaN(lat) || isNaN(lng)) {
    return 'America/Chicago';
  }

  const latF = parseFloat(lat);
  const lngF = parseFloat(lng);

  // Continental United States & Canada / Mexico
  if (latF >= 24.0 && latF <= 50.0) {
    if (lngF < -114.5) {
      return 'America/Los_Angeles'; // Pacific Time (PT)
    } else if (lngF < -102.0) {
      if (latF >= 31.0 && latF <= 37.0 && lngF >= -114.8 && lngF <= -109.0) {
        return 'America/Phoenix'; // Mountain Standard Time (no DST)
      }
      return 'America/Denver'; // Mountain Time (MT)
    } else if (lngF < -85.0) {
      return 'America/Chicago'; // Central Time (CT)
    } else {
      if (latF >= 37.8 && latF <= 41.8 && lngF >= -88.0 && lngF <= -84.7) {
        return 'America/Indiana/Indianapolis';
      }
      return 'America/New_York'; // Eastern Time (ET)
    }
  } else if (latF > 50.0 && lngF < -130.0) {
    return 'America/Anchorage'; // Alaska Time
  } else if (latF >= 18.0 && latF <= 23.0 && lngF >= -161.0 && lngF <= -154.0) {
    return 'Pacific/Honolulu'; // Hawaii Time
  }

  // International coordinates approximation by longitude
  if (lngF >= -12.0 && lngF <= 2.0 && latF >= 49.0 && latF <= 60.0) {
    return 'Europe/London';
  } else if (lngF >= 2.0 && lngF <= 25.0 && latF >= 35.0 && latF <= 70.0) {
    return 'Europe/Paris';
  } else if (lngF >= 60.0 && lngF <= 76.0 && latF >= 23.0 && latF <= 37.0) {
    return 'Asia/Karachi';
  } else if (lngF >= 68.0 && lngF <= 90.0 && latF >= 8.0 && latF <= 35.0) {
    return 'Asia/Kolkata';
  }

  return 'America/Chicago';
}
