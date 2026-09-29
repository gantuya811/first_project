"""
MERRIGE ERP - Тайлангийн Views
Views нимгэн байна: хүсэлтийг уншиж Service Layer руу дамжуулаад,
`?export=excel` эсвэл `?export=pdf` дамжуулбал файл татаж авах хариу,
эс бөгөөс стандарт JSON success_response буцаана.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.shared.exporters import export_rows_to_excel, export_rows_to_pdf
from apps.reports.serializers import (
    CommissionReportSerializer,
    DateRangeQuerySerializer,
    InventoryReportSerializer,
    ProfitReportSerializer,
    SalesReportSerializer,
    SellerReportEntrySerializer,
    TopProductSerializer,
)
from apps.reports.services import ReportService
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


def _parse_date_range(request):
    serializer = DateRangeQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return (
        serializer.validated_data.get("start_date"),
        serializer.validated_data.get("end_date"),
    )


def _export_format(request):
    value = request.query_params.get("export", "").lower()
    return value if value in ("excel", "pdf") else None


class SalesReportView(APIView):
    """GET /api/v1/reports/sales/?start_date=&end_date=&export=excel|pdf
    — Борлуулалтын тайлан (RBAC)."""

    def get(self, request):
        start_date, end_date = _parse_date_range(request)
        data = ReportService.sales_report(request.user, start_date, end_date)
        export_format = _export_format(request)

        headers = ["Эхлэх огноо", "Дуусах огноо", "Нийт захиалга", "Нийт борлуулалт"]
        rows = [
            [
                str(data["start_date"]),
                str(data["end_date"]),
                data["total_orders"],
                float(data["total_sales"]),
            ]
        ]
        if export_format == "excel":
            return export_rows_to_excel(
                "borluulaltiin_tailan.xlsx", headers, rows, "Борлуулалтын тайлан"
            )
        if export_format == "pdf":
            return export_rows_to_pdf(
                "borluulaltiin_tailan.pdf", "Борлуулалтын тайлан", headers, rows
            )

        return success_response(data=SalesReportSerializer(data).data)


class ProfitReportView(APIView):
    """GET /api/v1/reports/profit/?start_date=&end_date=&export=excel|pdf
    — Ашгийн тайлан (зөвхөн Админ, НУУЦ МЭДЭЭЛЭЛ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        start_date, end_date = _parse_date_range(request)
        data = ReportService.profit_report(start_date, end_date)
        export_format = _export_format(request)

        headers = [
            "Эхлэх огноо",
            "Дуусах огноо",
            "Нийт борлуулалт",
            "Нийт зардал",
            "Цэвэр ашиг",
            "Эзний ашиг",
        ]
        rows = [
            [
                str(data["start_date"]),
                str(data["end_date"]),
                float(data["total_revenue"]),
                float(data["total_cost"]),
                float(data["total_net_profit"]),
                float(data["total_owner_profit"]),
            ]
        ]
        if export_format == "excel":
            return export_rows_to_excel(
                "ashgiin_tailan.xlsx", headers, rows, "Ашгийн тайлан"
            )
        if export_format == "pdf":
            return export_rows_to_pdf(
                "ashgiin_tailan.pdf", "Ашгийн тайлан", headers, rows
            )

        return success_response(data=ProfitReportSerializer(data).data)


class CommissionReportView(APIView):
    """GET /api/v1/reports/commissions/?start_date=&end_date=&export=excel|pdf
    — Шимтгэлийн тайлан (RBAC)."""

    def get(self, request):
        start_date, end_date = _parse_date_range(request)
        data = ReportService.commission_report(request.user, start_date, end_date)
        export_format = _export_format(request)

        headers = ["Борлуулагч", "Шимтгэлийн тоо", "Нийт дүн"]
        rows = [
            [
                f"{row['seller__last_name']} {row['seller__first_name']}",
                row["count"],
                float(row["total"]),
            ]
            for row in data["by_seller"]
        ]
        if export_format == "excel":
            return export_rows_to_excel(
                "shimtgeliin_tailan.xlsx", headers, rows, "Шимтгэлийн тайлан"
            )
        if export_format == "pdf":
            return export_rows_to_pdf(
                "shimtgeliin_tailan.pdf", "Шимтгэлийн тайлан", headers, rows
            )

        return success_response(data=CommissionReportSerializer(data).data)


class InventoryReportView(APIView):
    """GET /api/v1/reports/inventory/?export=excel|pdf — Агуулахын тайлан."""

    def get(self, request):
        data = ReportService.inventory_report()
        export_format = _export_format(request)

        headers = ["Нийт хувилбар", "Нийт үлдэгдэл", "Нийт зах зээлийн үнэ (RRP)", "Нөөц бага"]
        rows = [
            [
                data["total_variants"],
                data["total_quantity"],
                float(data["total_retail_value"]),
                data["low_stock_count"],
            ]
        ]
        if export_format == "excel":
            return export_rows_to_excel(
                "aguulakhiin_tailan.xlsx", headers, rows, "Агуулахын тайлан"
            )
        if export_format == "pdf":
            return export_rows_to_pdf(
                "aguulakhiin_tailan.pdf", "Агуулахын тайлан", headers, rows
            )

        return success_response(data=InventoryReportSerializer(data).data)


class SellerReportView(APIView):
    """GET /api/v1/reports/sellers/?start_date=&end_date=&export=excel|pdf
    — Борлуулагчийн тайлан (RBAC)."""

    def get(self, request):
        start_date, end_date = _parse_date_range(request)
        data = ReportService.seller_report(request.user, start_date, end_date)
        export_format = _export_format(request)

        headers = ["Борлуулагч", "Захиалгын тоо", "Нийт борлуулалт"]
        rows = [
            [row["seller_name"], row["order_count"], float(row["total_sales"])]
            for row in data
        ]
        if export_format == "excel":
            return export_rows_to_excel(
                "borluulagchiin_tailan.xlsx", headers, rows, "Борлуулагчийн тайлан"
            )
        if export_format == "pdf":
            return export_rows_to_pdf(
                "borluulagchiin_tailan.pdf", "Борлуулагчийн тайлан", headers, rows
            )

        return success_response(data=SellerReportEntrySerializer(data, many=True).data)


class TopProductsView(APIView):
    """GET /api/v1/reports/top-products/?start_date=&end_date=&limit=&export=excel|pdf
    — Топ бараа."""

    def get(self, request):
        start_date, end_date = _parse_date_range(request)
        limit = int(request.query_params.get("limit", 10))
        data = ReportService.top_products(request.user, start_date, end_date, limit)
        export_format = _export_format(request)

        headers = ["Код", "Барааны нэр", "Зарагдсан тоо", "Орлого"]
        rows = [
            [row["product_code"], row["product_name"], row["quantity_sold"], float(row["revenue"])]
            for row in data
        ]
        if export_format == "excel":
            return export_rows_to_excel(
                "top_baraa.xlsx", headers, rows, "Топ бараа"
            )
        if export_format == "pdf":
            return export_rows_to_pdf("top_baraa.pdf", "Топ бараа", headers, rows)

        return success_response(data=TopProductSerializer(data, many=True).data)


class TopSellersView(APIView):
    """GET /api/v1/reports/top-sellers/?start_date=&end_date=&limit=&export=excel|pdf
    — Топ борлуулагч."""

    def get(self, request):
        start_date, end_date = _parse_date_range(request)
        limit = int(request.query_params.get("limit", 10))
        data = ReportService.top_sellers(request.user, start_date, end_date, limit)
        export_format = _export_format(request)

        headers = ["Борлуулагч", "Захиалгын тоо", "Нийт борлуулалт"]
        rows = [
            [row["seller_name"], row["order_count"], float(row["total_sales"])]
            for row in data
        ]
        if export_format == "excel":
            return export_rows_to_excel(
                "top_borluulagch.xlsx", headers, rows, "Топ борлуулагч"
            )
        if export_format == "pdf":
            return export_rows_to_pdf(
                "top_borluulagch.pdf", "Топ борлуулагч", headers, rows
            )

        return success_response(data=SellerReportEntrySerializer(data, many=True).data)
