"""
MERRIGE ERP - Агуулахын API URL-ууд
"""

from django.urls import path

from apps.inventory.views import (
    LowStockView,
    StockAdjustView,
    StockDetailView,
    StockInView,
    StockListView,
    StockMovementListView,
    StockOutView,
    StockReleaseView,
    StockReserveView,
)

app_name = "inventory"

urlpatterns = [
    path("stock/", StockListView.as_view(), name="stock-list"),
    path("low-stock/", LowStockView.as_view(), name="low-stock"),
    path("stock/<uuid:variant_uuid>/", StockDetailView.as_view(), name="stock-detail"),
    path(
        "stock/<uuid:variant_uuid>/stock-in/",
        StockInView.as_view(),
        name="stock-in",
    ),
    path(
        "stock/<uuid:variant_uuid>/stock-out/",
        StockOutView.as_view(),
        name="stock-out",
    ),
    path(
        "stock/<uuid:variant_uuid>/reserve/",
        StockReserveView.as_view(),
        name="stock-reserve",
    ),
    path(
        "stock/<uuid:variant_uuid>/release/",
        StockReleaseView.as_view(),
        name="stock-release",
    ),
    path(
        "stock/<uuid:variant_uuid>/adjust/",
        StockAdjustView.as_view(),
        name="stock-adjust",
    ),
    path(
        "stock/<uuid:variant_uuid>/movements/",
        StockMovementListView.as_view(),
        name="stock-movements",
    ),
]
