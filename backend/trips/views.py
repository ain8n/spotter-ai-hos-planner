"""
Views for Trips API
Handles Health Checks, Location Search/Geocoding, and Trip Planning & ELD Generation.
"""

import logging
from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripPlanRequestSerializer
from .services.routing.router import RouteCalculator
from .services.hos.engine import HOSEngine
from .services.logs.generator import generate_daily_logs
from .services.logs.svg_renderer import render_log_svg
from .services.geocoding.geocoder import search_locations, geocode_location
from .services.geocoding.timezone import determine_timezone_from_coords

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint returning service status and UTC timestamp.
    """
    def get(self, request):
        return Response(
            {
                "status": "healthy",
                "service": "HOS Trip Planner & ELD Log Generator",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class GeocodeView(APIView):
    """
    Provides location search and coordinates lookups.
    """
    def get(self, request):
        lat_param = request.query_params.get("lat")
        lng_param = request.query_params.get("lng")
        if lat_param is not None and lng_param is not None:
            try:
                lat_val = float(lat_param)
                lng_val = float(lng_param)
                from .services.geocoding.geocoder import reverse_geocode
                name = reverse_geocode(lat_val, lng_val)
                tz = determine_timezone_from_coords(lat_val, lng_val)
                return Response(
                    {
                        "lat": lat_val,
                        "lng": lng_val,
                        "name": name,
                        "display_name": name,
                        "timezone": tz,
                    },
                    status=status.HTTP_200_OK,
                )
            except ValueError:
                pass

        query = request.query_params.get("q", "").strip() or request.query_params.get("query", "").strip()
        if not query:
            return Response({"error": "Query parameter 'q' or ('lat' and 'lng') is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Never search OSM for "Your Location" / "Current Location"
        if query.lower() in ["your location", "current location", "my location", "gps"]:
            return Response(
                {
                    "query": query,
                    "location": {"lat": 38.8951, "lng": -77.0364, "name": "Your Location", "state": "", "timezone": "America/New_York"},
                    "suggestions": [],
                },
                status=status.HTTP_200_OK,
            )

        suggestions = search_locations(query, limit=5)
        for s in suggestions:
            s["timezone"] = determine_timezone_from_coords(s.get("lat"), s.get("lng"))
        best_match = geocode_location(query)
        best_match["timezone"] = determine_timezone_from_coords(best_match.get("lat"), best_match.get("lng"))
        return Response(
            {
                "query": query,
                "location": best_match,
                "suggestions": suggestions,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        query = request.data.get("query", "").strip() or request.data.get("q", "").strip()
        if not query:
            return Response(
                {"error": {"code": "INVALID_QUERY", "message": "Location query is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if query.lower() in ["your location", "current location", "my location", "gps"]:
            return Response(
                {
                    "query": query,
                    "location": {"lat": 38.8951, "lng": -77.0364, "name": "Your Location", "state": "", "timezone": "America/New_York"},
                    "suggestions": [],
                },
                status=status.HTTP_200_OK,
            )

        suggestions = search_locations(query, limit=5)
        for s in suggestions:
            s["timezone"] = determine_timezone_from_coords(s.get("lat"), s.get("lng"))
        best_match = geocode_location(query)
        best_match["timezone"] = determine_timezone_from_coords(best_match.get("lat"), best_match.get("lng"))
        return Response(
            {
                "query": query,
                "location": best_match,
                "suggestions": suggestions,
            },
            status=status.HTTP_200_OK,
        )


class PlanTripView(APIView):
    """
    Core Trip Planning & ELD Log generation endpoint.
    Calculates route, simulates HOS schedule, generates daily ELD logs, and renders SVG log sheets.
    """
    def post(self, request):
        serializer = TripPlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Format field errors cleanly
            field_errors = {}
            for field, errs in serializer.errors.items():
                field_errors[field] = errs[0] if isinstance(errs, list) else str(errs)

            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid trip parameters provided. Please check the fields and try again.",
                        "fields": field_errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        curr_query = data["current_location"]
        pickup_query = data["pickup_location"]
        dropoff_query = data["dropoff_location"]
        cycle_used = float(data["current_cycle_used_hrs"])
        options = data.get("options", {}) or {}

        start_dt = options.get("start_datetime")
        avg_speed = options.get("average_speed_mph", 55.0)
        header_details = options.get("header", {}) or {}

        # Support coordinates passed either in options.coordinates or top-level coordinates
        custom_coords = (
            options.get("coordinates")
            or data.get("coordinates")
            or request.data.get("coordinates")
            or (request.data.get("options", {}).get("coordinates") if isinstance(request.data.get("options"), dict) else {})
            or {}
        )

        try:
            # 1. Direct coordinates check (Source of Truth: GPS or manually selected coordinates)
            curr_coord_input = custom_coords.get("current")
            if (
                curr_coord_input
                and "lat" in curr_coord_input
                and "lng" in curr_coord_input
                and curr_coord_input["lat"] is not None
                and curr_coord_input["lng"] is not None
            ):
                current_loc = {
                    "lat": float(curr_coord_input["lat"]),
                    "lng": float(curr_coord_input["lng"]),
                    "name": curr_coord_input.get("name") or curr_query or "Your Location",
                    "source": curr_coord_input.get("source", "gps" if curr_query == "Your Location" else "manual"),
                    "state": curr_coord_input.get("state", ""),
                }
            else:
                if curr_query.strip().lower() in ["your location", "current location", "my location", "gps"]:
                    # Fallback default if coordinates were somehow missing
                    current_loc = {"lat": 38.8951, "lng": -77.0364, "name": "Your Location", "state": "DC", "source": "gps"}
                else:
                    current_loc = geocode_location(curr_query)

            pickup_coord_input = custom_coords.get("pickup")
            if (
                pickup_coord_input
                and "lat" in pickup_coord_input
                and "lng" in pickup_coord_input
                and pickup_coord_input["lat"] is not None
                and pickup_coord_input["lng"] is not None
            ):
                pickup_loc = {
                    "lat": float(pickup_coord_input["lat"]),
                    "lng": float(pickup_coord_input["lng"]),
                    "name": pickup_coord_input.get("name") or pickup_query,
                    "state": pickup_coord_input.get("state", ""),
                    "source": pickup_coord_input.get("source", "manual"),
                }
            else:
                pickup_loc = geocode_location(pickup_query)

            dropoff_coord_input = custom_coords.get("dropoff")
            if (
                dropoff_coord_input
                and "lat" in dropoff_coord_input
                and "lng" in dropoff_coord_input
                and dropoff_coord_input["lat"] is not None
                and dropoff_coord_input["lng"] is not None
            ):
                dropoff_loc = {
                    "lat": float(dropoff_coord_input["lat"]),
                    "lng": float(dropoff_coord_input["lng"]),
                    "name": dropoff_coord_input.get("name") or dropoff_query,
                    "state": dropoff_coord_input.get("state", ""),
                    "source": dropoff_coord_input.get("source", "manual"),
                }
            else:
                dropoff_loc = geocode_location(dropoff_query)

            # 2. Calculate route legs
            router = RouteCalculator()
            leg1 = router.calculate_leg(
                start_lat=current_loc["lat"],
                start_lng=current_loc["lng"],
                start_name=current_loc["name"],
                end_lat=pickup_loc["lat"],
                end_lng=pickup_loc["lng"],
                end_name=pickup_loc["name"],
            )

            leg2 = router.calculate_leg(
                start_lat=pickup_loc["lat"],
                start_lng=pickup_loc["lng"],
                start_name=pickup_loc["name"],
                end_lat=dropoff_loc["lat"],
                end_lng=dropoff_loc["lng"],
                end_name=dropoff_loc["name"],
            )

            # Unified route geometry
            full_geometry = leg1.get("geometry", []) + leg2.get("geometry", [])
            total_route_distance = round(leg1.get("distance_miles", 0.0) + leg2.get("distance_miles", 0.0), 1)
            total_route_duration = round(leg1.get("duration_hours", 0.0) + leg2.get("duration_hours", 0.0), 2)

            # 3. Determine timezones based on exact geographic coordinates
            current_tz = determine_timezone_from_coords(current_loc["lat"], current_loc["lng"])
            current_loc["timezone"] = current_tz
            pickup_loc["timezone"] = determine_timezone_from_coords(pickup_loc["lat"], pickup_loc["lng"])
            dropoff_loc["timezone"] = determine_timezone_from_coords(dropoff_loc["lat"], dropoff_loc["lng"])

            # 4. Simulate HOS schedule in Current Location timezone
            engine = HOSEngine(
                current_cycle_used_hrs=cycle_used,
                start_datetime=start_dt,
                average_speed_mph=avg_speed,
                timezone_name=current_tz,
            )
            plan_result = engine.plan_trip(
                current_loc=current_loc,
                pickup_loc=pickup_loc,
                dropoff_loc=dropoff_loc,
                leg1_info=leg1,
                leg2_info=leg2,
            )

            # 5. Generate Daily Logs & SVG sheets
            daily_logs = generate_daily_logs(
                timeline_events=plan_result.timeline_events,
                current_cycle_used_hrs=cycle_used,
                log_header_details=header_details,
            )

            # Render SVG for each day
            for log in daily_logs:
                log["svg_content"] = render_log_svg(log)

            # Format instructions grouped by leg
            instructions = {
                "leg1_current_to_pickup": {
                    "from": current_loc["name"],
                    "to": pickup_loc["name"],
                    "distance_miles": leg1.get("distance_miles", 0.0),
                    "steps": leg1.get("instructions", []),
                },
                "leg2_pickup_to_dropoff": {
                    "from": pickup_loc["name"],
                    "to": dropoff_loc["name"],
                    "distance_miles": leg2.get("distance_miles", 0.0),
                    "steps": leg2.get("instructions", []),
                },
            }

            response_data = {
                "timezone": current_tz,
                "summary": plan_result.summary,
                "route": {
                    "total_distance_miles": total_route_distance,
                    "total_driving_duration_hours": total_route_duration,
                    "locations": {
                        "current": current_loc,
                        "pickup": pickup_loc,
                        "dropoff": dropoff_loc,
                    },
                    "leg1": leg1,
                    "leg2": leg2,
                    "full_geometry": full_geometry,
                },
                "instructions": instructions,
                "stops": plan_result.stops,
                "timeline": plan_result.timeline_events,
                "logs": daily_logs,
                "warnings": plan_result.warnings,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error planning trip: %s", str(e))
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_PLANNING_ERROR",
                        "message": f"An error occurred while calculating the trip: {str(e)}",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
