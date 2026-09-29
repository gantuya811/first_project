"""
MERRIGE ERP - Dashboard app-ийн тестүүд
"""

from decimal import Decimal

import pytest

from apps.dashboard.services import DashboardService
from apps.inventory.services import InventoryService
from apps.orders.models import OrderStatus
from apps.orders.services import GroupedOrderService, OrderService

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


class TestDashboardService:
    def test_kpi_summary_with_no_data(self, admin_user):
        kpi = DashboardService.kpi_summary(admin_user)
        assert kpi["today_orders"] == 0
        assert kpi["today_sales"] == Decimal("0")

    def test_kpi_summary_reflects_completed_order(self, admin_user, completed_order):
        kpi = DashboardService.kpi_summary(admin_user)
        assert kpi["today_orders"] == 1
        assert kpi["today_sales"] == Decimal("200000.00")
        assert kpi["owner_profit"] == Decimal("50000.00")
        assert kpi["main_seller_profit"] == Decimal("20000.00")

    def test_low_stock_counted_in_kpi(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 2, admin_user)  # threshold=5-аас бага
        kpi = DashboardService.kpi_summary(admin_user)
        assert kpi["low_stock_items"] == 1

    def test_province_report_groups_by_seller_province(self, admin_user, main_seller, completed_order):
        main_seller.province = "Улаанбаатар"
        main_seller.save(update_fields=["province"])
        report = DashboardService.province_report()
        assert any(row["province"] == "Улаанбаатар" for row in report)


class TestDashboardAPI:
    def test_seller_cannot_view_kpi(self, main_seller_client):
        response = main_seller_client.get("/api/v1/dashboard/kpi/")
        assert response.status_code == 403

    def test_admin_can_view_kpi(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/dashboard/kpi/")
        assert response.status_code == 200
        assert response.data["data"]["today_orders"] == 1

    def test_admin_charts_endpoint(self, admin_client, completed_order):
        response = admin_client.get("/api/v1/dashboard/charts/?days=7")
        assert response.status_code == 200
        assert "sales_trend" in response.data["data"]
        assert "province_report" in response.data["data"]

    def test_admin_alerts_endpoint(self, admin_client, variant, stock, admin_user):
        InventoryService.stock_in(variant, 1, admin_user)
        response = admin_client.get("/api/v1/dashboard/alerts/")
        assert response.status_code == 200
        assert len(response.data["data"]["low_stock_items"]) == 1
