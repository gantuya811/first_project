"""
MERRIGE ERP - Core Views
Системийн нийтлэг алдааны хуудсууд болон эрүүл мэндийн шалгалт (health
check)-ийг Монгол хэл дээр харуулна.
"""

from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def handler_404(request, exception=None):
    """Хуудас олдоогүй үеийн алдааны дэлгэц (404)."""
    return render(request, "errors/404.html", status=404)


def handler_500(request):
    """Серверийн дотоод алдааны дэлгэц (500)."""
    return render(request, "errors/500.html", status=500)


class HealthCheckView(APIView):
    """GET /health/ — Сервер, өгөгдлийн сан, кэш (Redis)-ийн холболтыг
    шалгана. Эрх баталгаажуулалт шаардахгүй (load balancer/Docker
    HEALTHCHECK-д ашиглагдана)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        checks = {"database": self._check_database(), "cache": self._check_cache()}
        is_healthy = all(checks.values())
        message = "Систем хэвийн ажиллаж байна" if is_healthy else "Систем эрсдэлтэй байна"
        return Response(
            {
                "success": is_healthy,
                "message": message,
                "data": {
                    "status": "ok" if is_healthy else "degraded",
                    "checks": checks,
                },
            },
            status=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @staticmethod
    def _check_database():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except OperationalError:
            return False

    @staticmethod
    def _check_cache():
        try:
            cache.set("health_check_probe", "1", timeout=5)
            return cache.get("health_check_probe") == "1"
        except Exception:
            return False
