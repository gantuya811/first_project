"""
MERRIGE ERP - Admin Dashboard Views
Views нимгэн байна. Зөвхөн Админ-д зориулагдсан 3 endpoint: KPI, Графикууд,
Анхаарах зүйлс (хүлээгдэж буй төлбөр, нөөц бага бараа).
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.dashboard.serializers import (
    KPISerializer,
    ProvinceReportEntrySerializer,
    TrendPointSerializer,
)
from apps.dashboard.services import DashboardService
from apps.inventory.repositories import InventoryRepository
from apps.inventory.serializers import StockSerializer
from apps.payments.repositories import PaymentRepository
from apps.payments.serializers import PaymentListSerializer
from apps.reports.serializers import SellerReportEntrySerializer, TopProductSerializer
from apps.reports.services import ReportService
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


class DashboardKPIView(APIView):
    """GET /api/v1/dashboard/kpi/ — 10 KPI (Өнөөдрийн захиалга, борлуулалт,
    ашиг, Энэ сарын борлуулалт/ашиг, Эзний/Үндсэн/Гэрээт Борлуулагчийн
    ашиг, Хүлээгдэж буй төлбөр, Нөөц багатай бараа)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        data = DashboardService.kpi_summary(request.user)
        return success_response(data=KPISerializer(data).data)


class DashboardChartsView(APIView):
    """GET /api/v1/dashboard/charts/?days=30 — Борлуулалтын тренд, Ашгийн
    тренд, Топ бараанууд, Топ борлуулагчид, Аймгийн тайлан."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30

        data = {
            "sales_trend": TrendPointSerializer(
                DashboardService.sales_trend(days), many=True
            ).data,
            "profit_trend": TrendPointSerializer(
                DashboardService.profit_trend(days), many=True
            ).data,
            "top_products": TopProductSerializer(
                ReportService.top_products(request.user, limit=10), many=True
            ).data,
            "top_sellers": SellerReportEntrySerializer(
                ReportService.top_sellers(request.user, limit=10), many=True
            ).data,
            "province_report": ProvinceReportEntrySerializer(
                DashboardService.province_report(), many=True
            ).data,
        }
        return success_response(data=data)


class DashboardAlertsView(APIView):
    """GET /api/v1/dashboard/alerts/ — "Ямар төлбөр шалгах шаардлагатай
    байна вэ" болон "Ямар барааны нөөц дуусах гэж байна вэ" асуултуудад
    хариулна."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        pending_payments = PaymentRepository.list_pending()[:20]
        low_stock_items = InventoryRepository.list_low_stock()[:20]

        data = {
            "pending_payments": PaymentListSerializer(pending_payments, many=True).data,
            "low_stock_items": StockSerializer(low_stock_items, many=True).data,
        }
        return success_response(data=data)
