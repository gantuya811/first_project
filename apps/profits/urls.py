"""
MERRIGE ERP - Ашгийн API URL-ууд
"""

from django.urls import path

from apps.profits.views import (
    ProductCostView,
    ProductProfitView,
    ProfitDistributionView,
)

app_name = "profits"

urlpatterns = [
    path("distribution/", ProfitDistributionView.as_view(), name="distribution"),
    path(
        "products/<uuid:product_uuid>/",
        ProductProfitView.as_view(),
        name="product-profit",
    ),
    path(
        "products/<uuid:product_uuid>/cost/",
        ProductCostView.as_view(),
        name="product-cost",
    ),
]
