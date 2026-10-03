/**
 * Helper formatting utilities with IANA timezone support.
 */

export function formatHours(hours) {
  if (hours == null || isNaN(hours)) return '0.0h';
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export function formatMiles(miles) {
  if (miles == null || isNaN(miles)) return '0.0 mi';
  return `${Number(miles).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mi`;
}

export function formatDateTime(isoString, timeZone) {
  if (!isoString) return '--';
  try {
    const dt = new Date(isoString);
    if (isNaN(dt.getTime())) return String(isoString);
    const options = {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    };
    if (timeZone) {
      options.timeZone = timeZone;
    }
    return dt.toLocaleString('en-US', options);
  } catch (e) {
    return String(isoString);
  }
}

export function formatTimeOnly(isoString, timeZone) {
  if (!isoString) return '--';
  try {
    const dt = new Date(isoString);
    if (isNaN(dt.getTime())) return String(isoString);
    const options = {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    };
    if (timeZone) {
      options.timeZone = timeZone;
    }
    return dt.toLocaleTimeString('en-US', options);
  } catch (e) {
    return String(isoString);
  }
}
