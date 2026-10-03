/**
 * API client for HOS Trip Planner
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health/`);
    return await res.json();
  } catch (err) {
    console.error('Health check failed', err);
    return { status: 'offline' };
  }
}

export async function planTrip(payload) {
  const res = await fetch(`${API_BASE}/trips/plan/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || 'Failed to plan trip. Please check your inputs.';
    const fieldErrors = data?.error?.fields || {};
    const error = new Error(errorMsg);
    error.fields = fieldErrors;
    error.code = data?.error?.code || 'API_ERROR';
    throw error;
  }

  return data;
}

export async function geocodeLocation(query) {
  const res = await fetch(`${API_BASE}/trips/geocode/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });

  return await res.json();
}

export async function searchLocations(query) {
  if (!query || query.trim().length < 2) return [];
  try {
    const res = await fetch(`${API_BASE}/trips/geocode/?q=${encodeURIComponent(query.trim())}`);
    if (res.ok) {
      const data = await res.json();
      return data.suggestions || (data.location ? [data.location] : []);
    }
  } catch (err) {
    console.warn('Geocode search failed', err);
  }
  return [];
}

export async function reverseGeocodeLocation(lat, lng) {
  try {
    const res = await fetch(`${API_BASE}/trips/geocode/?lat=${lat}&lng=${lng}`);
    if (res.ok) {
      const data = await res.json();
      return data.name || data.display_name || `${Number(lat).toFixed(4)}, ${Number(lng).toFixed(4)}`;
    }
  } catch (err) {
    console.warn('Reverse geocode failed', err);
  }
  return `${Number(lat).toFixed(4)}, ${Number(lng).toFixed(4)}`;
}
