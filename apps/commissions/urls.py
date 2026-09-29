"""
MERRIGE ERP - Шимтгэлийн API URL-ууд
"""

from django.urls import path

from apps.commissions.views import (
    CommissionDetailView,
    CommissionGenerateView,
    CommissionListView,
)

app_name = "commissions"

urlpatterns = [
    path("", CommissionListView.as_view(), name="list"),
    path(
        "orders/<uuid:order_uuid>/generate/",
        CommissionGenerateView.as_view(),
        name="generate",
    ),
    path("<uuid:commission_uuid>/", CommissionDetailView.as_view(), name="detail"),
]
