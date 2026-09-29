"""
MERRIGE ERP - Commissions app-ийн тестүүд
Дүрэм: Шимтгэл зөвхөн COMPLETED захиалганд, давхардуулахгүйгээр бодогдоно.
"""

from decimal import Decimal

import pytest

from apps.commissions.models import Commission
from apps.commissions.services import CommissionService
from apps.inventory.services import InventoryService
from apps.orders.models import OrderStatus
from apps.orders.services import GroupedOrderService, OrderService
from apps.shared.exceptions import БизнесАлдаа

pytestmark = pytest.mark.django_db


def _advance_order_to_completed(order, admin_user):
    order = OrderService.start_review(order, admin_user)
    order = OrderService.approve(order, admin_user)
    order = OrderService.transition_status(order, OrderStatus.PAYMENT_REVIEW, admin_user)
    order = OrderService.transition_status(order, OrderStatus.PAYMENT_CONFIRMED, admin_user)
    grouped = GroupedOrderService.create(admin_user)
    order = OrderService.group(order, grouped, admin_user)
    order = OrderService.mark_arrived(order, admin_user)
    order = OrderService.ship(order, admin_user)
    return OrderService.complete(order, admin_user)


@pytest.fixture
def completed_order(admin_user, main_seller, variant, stock, product_cost, profit_distribution):
    InventoryService.stock_in(variant, 20, admin_user)
    order = OrderService.create_order(
        seller=main_seller, items_data=[{"variant_uuid": variant.uuid, "quantity": 2}]
    )
    return _advance_order_to_completed(order, admin_user)


class TestCommissionModel:
    def test_duplicate_commission_blocked_at_db_level(self, completed_order, main_seller):
        # completed_order-ийн COMPLETED signal аль хэдийн 1 Commission үүсгэсэн
        assert Commission.objects.filter(order=completed_order).count() == 1
        with pytest.raises(Exception):
            Commission.objects.create(
                order=completed_order, seller=main_seller, amount=Decimal("1")
            )

    def test_commission_immutable_save(self, completed_order):
        commission = Commission.objects.get(order=completed_order)
        commission.amount = Decimal("999999")
        with pytest.raises(RuntimeError):
            commission.save()

    def test_commission_immutable_delete(self, completed_order):
        commission = Commission.objects.get(order=completed_order)
        with pytest.raises(RuntimeError):
            commission.delete()


class TestCommissionService:
    def test_auto_generated_on_completion_with_correct_amount(self, completed_order):
        # RRP=100000, Нийт зардал=50000, Цэвэр ашиг/нэгж=50000
        # Үндсэн Борлуулагчийн хувь 20% = 10000/нэгж x 2 ширхэг = 20000
        commission = Commission.objects.get(order=completed_order)
        assert commission.amount == Decimal("20000.00")

    def test_generate_for_non_completed_order_raises(self, admin_user, main_seller, variant, stock):
        InventoryService.stock_in(variant, 10, admin_user)
        order = OrderService.create_order(
            seller=main_seller, items_data=[{"variant_uuid": variant.uuid, "quantity": 1}]
        )
        with pytest.raises(БизнесАлдаа):
            CommissionService.generate_for_order(order, actor=admin_user)

    def test_generate_twice_raises(self, completed_order, admin_user):
        with pytest.raises(БизнесАлдаа):
            CommissionService.generate_for_order(completed_order, actor=admin_user)


class TestCommissionAPI:
    def test_seller_sees_own_commission(self, main_seller_client, completed_order):
        response = main_seller_client.get("/api/v1/commissions/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 1

    def test_unrelated_seller_sees_no_commission(self, another_main_seller, api_client, completed_order):
        api_client.force_authenticate(user=another_main_seller)
        response = api_client.get("/api/v1/commissions/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 0
