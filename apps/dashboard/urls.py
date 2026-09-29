"""
MERRIGE ERP - Dashboard API URL-ууд
"""

from django.urls import path

from apps.dashboard.views import (
    DashboardAlertsView,
    DashboardChartsView,
    DashboardKPIView,
)

app_name = "dashboard"

urlpatterns = [
    path("kpi/", DashboardKPIView.as_view(), name="kpi"),
    path("charts/", DashboardChartsView.as_view(), name="charts"),
    path("alerts/", DashboardAlertsView.as_view(), name="alerts"),
]
