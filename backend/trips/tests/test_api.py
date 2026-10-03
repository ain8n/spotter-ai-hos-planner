"""
API Integration Tests
Tests /api/health/ and /api/trips/plan/ endpoints.
"""

import pytest
from rest_framework.test import APIClient
from django.urls import reverse


@pytest.fixture
def api_client():
    return APIClient()


def test_health_check_endpoint(api_client):
    url = reverse("health_check")
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_trip_plan_validation_error(api_client):
    url = reverse("plan_trip")
    # Missing required fields
    resp = api_client.post(url, {}, format="json")
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_trip_plan_cycle_overflow_error(api_client):
    url = reverse("plan_trip")
    payload = {
        "current_location": "Chicago, IL",
        "pickup_location": "Gary, IN",
        "dropoff_location": "Columbus, OH",
        "current_cycle_used_hrs": 75.0,  # exceeds 70
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert "current_cycle_used_hrs" in data["error"]["fields"]


def test_trip_plan_successful_response(api_client):
    url = reverse("plan_trip")
    payload = {
        "current_location": "Chicago, IL",
        "pickup_location": "Gary, IN",
        "dropoff_location": "Columbus, OH",
        "current_cycle_used_hrs": 12.5,
        "options": {
            "start_datetime": "2026-10-05T06:00:00",
            "header": {
                "driver_name": "Test Driver",
                "carrier_name": "Logistics Express",
            },
        },
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 200
    data = resp.json()

    assert "summary" in data
    assert "route" in data
    assert "stops" in data
    assert "timeline" in data
    assert "logs" in data

    # Check logs structure
    logs = data["logs"]
    assert len(logs) >= 1
    log1 = logs[0]
    assert log1["totals"]["total_hours"] == 24.0
    assert "svg_content" in log1
    assert "<svg" in log1["svg_content"]
    assert log1["driver_name"] == "Test Driver"


def test_gps_coordinates_source_of_truth_routing(api_client):
    """
    Verifies that when exact GPS coordinates are passed for 'Your Location',
    the route starts directly from those exact coordinates and does not geocode 'Your Location'.
    """
    url = reverse("plan_trip")
    exact_gps_lat = 33.61841
    exact_gps_lng = 72.99576

    payload = {
        "current_location": "Your Location",
        "pickup_location": "Islamabad",
        "dropoff_location": "Lahore",
        "current_cycle_used_hrs": 10.0,
        "coordinates": {
            "current": {
                "lat": exact_gps_lat,
                "lng": exact_gps_lng,
                "name": "Your Location",
                "source": "gps",
            },
            "pickup": {"lat": 33.6844, "lng": 73.0479, "name": "Islamabad"},
            "dropoff": {"lat": 31.5204, "lng": 74.3587, "name": "Lahore"},
        },
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 200
    data = resp.json()

    # Route current location must match exact coordinates
    curr_loc = data["route"]["locations"]["current"]
    assert curr_loc["lat"] == exact_gps_lat
    assert curr_loc["lng"] == exact_gps_lng
    assert curr_loc["name"] == "Your Location"
    assert curr_loc["source"] == "gps"

    # Start stop must have exact coordinates
    start_stop = data["stops"][0]
    assert start_stop["stop_type"] == "START"
    assert start_stop["latitude"] == exact_gps_lat
    assert start_stop["longitude"] == exact_gps_lng
    assert start_stop["name"] == "Your Location"


def test_manual_override_coordinates_routing(api_client):
    """
    Verifies that when a manual location search is chosen, its coordinates are used.
    """
    url = reverse("plan_trip")
    manual_lat = 33.6000
    manual_lng = 73.0500

    payload = {
        "current_location": "Rawalpindi Saddar",
        "pickup_location": "Islamabad",
        "dropoff_location": "Lahore",
        "current_cycle_used_hrs": 5.0,
        "coordinates": {
            "current": {
                "lat": manual_lat,
                "lng": manual_lng,
                "name": "Rawalpindi Saddar",
                "source": "manual",
            },
        },
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 200
    data = resp.json()

    curr_loc = data["route"]["locations"]["current"]
    assert curr_loc["lat"] == manual_lat
    assert curr_loc["lng"] == manual_lng
    assert curr_loc["name"] == "Rawalpindi Saddar"
    assert curr_loc["source"] == "manual"
