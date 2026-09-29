"""
MERRIGE ERP - Тайлангийн API URL-ууд
"""

from django.urls import path

from apps.reports.views import (
    CommissionReportView,
    InventoryReportView,
    ProfitReportView,
    SalesReportView,
    SellerReportView,
    TopProductsView,
    TopSellersView,
)

app_name = "reports"

urlpatterns = [
    path("sales/", SalesReportView.as_view(), name="sales"),
    path("profit/", ProfitReportView.as_view(), name="profit"),
    path("commissions/", CommissionReportView.as_view(), name="commissions"),
    path("inventory/", InventoryReportView.as_view(), name="inventory"),
    path("sellers/", SellerReportView.as_view(), name="sellers"),
    path("top-products/", TopProductsView.as_view(), name="top-products"),
    path("top-sellers/", TopSellersView.as_view(), name="top-sellers"),
]
