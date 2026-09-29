"""
MERRIGE ERP - Үндсэн URL чиглүүлэлт
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import HealthCheckView

admin.site.site_header = "MERRIGE ERP - Удирдлагын самбар"
admin.site.site_title = "MERRIGE ERP"
admin.site.index_title = "Системийн удирдлага"

urlpatterns = [
    path("admin/", admin.site.urls),
    # --- Health Check (Docker/Load Balancer-д ашиглагдана) ---
    path("health/", HealthCheckView.as_view(), name="health-check"),
    # --- API v1 ---
    path("api/v1/", include("apps.api.urls")),
    # --- API баримт бичиг ---
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "apps.core.views.handler_404"
handler500 = "apps.core.views.handler_500"
