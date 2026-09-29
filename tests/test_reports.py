"""
MERRIGE ERP - Reports app-ийн тестүүд
"""

from decimal import Decimal

import pytest

from apps.inventory.services import InventoryService
from apps.orders.models import OrderStatus
from apps.orders.services import GroupedOrderService, OrderService
from apps.reports.services import ReportService

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_order(admin_user, main_seller, variant, stock, product_cost, profit_distribution):
    InventoryService.stock_in(variant, 20, admin_user)
    order = OrderService.create_order(
        seller=main_seller, items_data=[{"variant_uuid": variant.uuid, "quantity": 2}]
    )
    order = OrderService.start_review(order, admin_user)
    order = OrderService.approve(order, admin_user)
    order = OrderService.transition_status(order, OrderStatus.PAYMENT_REVIEW, admin_user)
    order = OrderService.transition_status(order, OrderStatus.PAYMENT_CONFIRMED, admin_user)
    grouped = GroupedOrderService.create(admin_user)
    order = OrderService.group(order, grouped, admin_user)
    order = OrderService.mark_arrived(order, admin_user)
    order = OrderService.ship(order, admin_user)
    return OrderService.complete(order, admin_user)


class TestReportService:
    def test_sales_report_totals(self, admin_user, completed_order):
        data = ReportService.sales_report(admin_user)
        assert data["total_orders"] == 1
        assert data["total_sales"] == Decimal("200000.00")  # 2 x 100000

    def test_profit_report_totals(self, completed_order):
        data = ReportService.profit_report()
        assert data["total_revenue"] == Decimal("200000.00")
        assert data["total_cost"] == Decimal("100000.00")  # 2 x 50000
        assert data["total_net_profit"] == Decimal("100000.00")
        assert data["total_owner_profit"] == Decimal("50000.00")  # 50%

    def test_inventory_report_uses_rrp_not_cost(self, variant, stock, product_cost, admin_user):
        InventoryService.stock_in(variant, 10, admin_user)
        data = ReportService.inventory_report()
        # RRP=100000, 10 ширхэг -> 1,000,000 (Анхны үнэ 40000 биш)
        assert data["total_retail_value"] == Decimal("1000000.00")

    def test_top_products_ranked_by_quantity(self, admin_user, completed_order):
        data = ReportService.top_products(admin_user)
        assert len(data) == 1
        assert data[0]["quantity_sold"] == 2

    def test_date_range_validation(self, admin_user):
        from apps.shared.exceptions import БизнесАлдаа

        with pytest.raises(БизнесАлдаа):
            ReportService.sales_report(admin_user, start_date="2026-02-01", end_date="2026-01-01")


class TestReportAPI:
    def test_seller_cannot_view_profit_report(self, main_seller_client):
        response = main_seller_client.get("/api/v1/reports/profit/")
        assert response.status_code == 403

    def test_admin_sales_report_excel_export(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/sales/?export=excel")
        assert response.status_code == 200
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_admin_sales_report_pdf_export(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/sales/?export=pdf")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

    def test_admin_profit_report_json(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/profit/")
        assert response.status_code == 200
        assert response.data["data"]["total_net_profit"] == "100000.00"

    def test_admin_profit_report_excel_export(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/profit/?export=excel")
        assert response.status_code == 200

    def test_commission_report_json(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/commissions/")
        assert response.status_code == 200
        assert response.data["data"]["total_amount"] == "20000.00"

    def test_commission_report_pdf_export(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/commissions/?export=pdf")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

    def test_inventory_report_json(self, admin_client, variant, stock, admin_user):
        from apps.inventory.services import InventoryService

        InventoryService.stock_in(variant, 5, admin_user)
        response = admin_client.get("/api/v1/reports/inventory/")
        assert response.status_code == 200
        assert response.data["data"]["total_quantity"] == 5

    def test_seller_report_json(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/sellers/")
        assert response.status_code == 200
        assert len(response.data["data"]) == 1

    def test_top_products_json(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/top-products/")
        assert response.status_code == 200
        assert response.data["data"][0]["quantity_sold"] == 2

    def test_top_sellers_excel_export(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/reports/top-sellers/?export=excel")
        assert response.status_code == 200
