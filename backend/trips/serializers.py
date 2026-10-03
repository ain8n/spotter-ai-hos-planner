"""
Serializers for Trip Planning API
"""

from rest_framework import serializers


class LogHeaderSerializer(serializers.Serializer):
    driver_name = serializers.CharField(required=False, default="John E. Doe")
    driver_id = serializers.CharField(required=False, default="DRV-84920")
    carrier_name = serializers.CharField(required=False, default="US Freight Express LLC")
    main_office_address = serializers.CharField(required=False, default="100 Logistics Blvd, Indianapolis, IN 46204")
    home_terminal_address = serializers.CharField(required=False, default="450 Transport Way, Chicago, IL 60601")
    truck_tractor_num = serializers.CharField(required=False, default="T-804 (VIN: 1XKWD49X)")
    trailer_num = serializers.CharField(required=False, default="TR-5309 (IL Lic: 982-TRK)")
    co_driver = serializers.CharField(required=False, default="N/A (Solo Driver)")
    shipping_doc = serializers.CharField(required=False, default="BOL #9482104")
    shipper_commodity = serializers.CharField(required=False, default="General Freight / Commercial Goods")


class TripOptionsSerializer(serializers.Serializer):
    start_datetime = serializers.DateTimeField(required=False, allow_null=True)
    average_speed_mph = serializers.FloatField(required=False, min_value=30.0, max_value=75.0, default=55.0)
    header = LogHeaderSerializer(required=False, default=dict)
    coordinates = serializers.DictField(required=False, default=dict)


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(
        required=True,
        min_length=2,
        max_length=255,
        error_messages={"blank": "Current location is required.", "required": "Current location is required."},
    )
    pickup_location = serializers.CharField(
        required=True,
        min_length=2,
        max_length=255,
        error_messages={"blank": "Pickup location is required.", "required": "Pickup location is required."},
    )
    dropoff_location = serializers.CharField(
        required=True,
        min_length=2,
        max_length=255,
        error_messages={"blank": "Dropoff location is required.", "required": "Dropoff location is required."},
    )
    current_cycle_used_hrs = serializers.FloatField(
        required=True,
        min_value=0.0,
        max_value=70.0,
        error_messages={
            "min_value": "Current cycle used hours cannot be negative.",
            "max_value": "Current cycle used cannot exceed 70.0 hours (70-hour / 8-day limit).",
            "required": "Current cycle used (in hours) is required.",
            "invalid": "Please enter a valid numeric value for cycle used hours.",
        },
    )
    coordinates = serializers.DictField(required=False, default=dict)
    options = TripOptionsSerializer(required=False, default=dict)
