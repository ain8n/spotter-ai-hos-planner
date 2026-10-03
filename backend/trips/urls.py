"""
URL routing for trips app
"""

from django.urls import path
from .views import HealthCheckView, PlanTripView, GeocodeView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health_check"),
    path("trips/plan/", PlanTripView.as_view(), name="plan_trip"),
    path("trips/geocode/", GeocodeView.as_view(), name="geocode_location"),
]
