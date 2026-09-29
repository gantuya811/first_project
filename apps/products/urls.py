"""
MERRIGE ERP - Барааны API URL-ууд
"""

from django.urls import path

from apps.products.views import (
    ProductDetailView,
    ProductExportView,
    ProductImageDeleteView,
    ProductImageUploadView,
    ProductImportView,
    ProductListCreateView,
    ProductVariantCreateView,
    ProductVariantDeleteView,
)

app_name = "products"

urlpatterns = [
    path("", ProductListCreateView.as_view(), name="list-create"),
    path("import/", ProductImportView.as_view(), name="import"),
    path("export/", ProductExportView.as_view(), name="export"),
    path("<uuid:product_uuid>/", ProductDetailView.as_view(), name="detail"),
    path(
        "<uuid:product_uuid>/images/",
        ProductImageUploadView.as_view(),
        name="image-upload",
    ),
    path(
        "<uuid:product_uuid>/images/<uuid:image_uuid>/",
        ProductImageDeleteView.as_view(),
        name="image-delete",
    ),
    path(
        "<uuid:product_uuid>/variants/",
        ProductVariantCreateView.as_view(),
        name="variant-create",
    ),
    path(
        "<uuid:product_uuid>/variants/<uuid:variant_uuid>/",
        ProductVariantDeleteView.as_view(),
        name="variant-delete",
    ),
]
