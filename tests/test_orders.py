"""
MERRIGE ERP - Orders app-ийн тестүүд
Захиалгын 12 төлөвт Finite State Machine, RBAC, Агуулахтай интеграцийг
бүрэн хамруулна.
"""

import pytest

from apps.inventory.services import InventoryService
from apps.orders.models import Order, OrderStatus
from apps.orders.services import GroupedOrderService, OrderService
from apps.shared.exceptions import БизнесАлдаа

pytestmark = pytest.mark.django_db


@pytest.fixture
def stocked_variant(admin_user, variant, stock):
    InventoryService.stock_in(variant, 50, admin_user, reason="Анхны орлого")
    return variant


@pytest.fixture
def order(main_seller, stocked_variant):
    return OrderService.create_order(
        seller=main_seller,
        items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 5}],
    )


# ------------------------------------------------------------------
# Unit Tests — Order number generation
# ------------------------------------------------------------------
class TestOrderNumberGeneration:
    def test_order_number_has_correct_prefix(self, order):
        assert order.order_number.startswith("ORD-")

    def test_sequential_order_numbers_increment(self, main_seller, stocked_variant):
        order1 = OrderService.create_order(
            seller=main_seller, items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 1}]
        )
        order2 = OrderService.create_order(
            seller=main_seller, items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 1}]
        )
        seq1 = int(order1.order_number.split("-")[-1])
        seq2 = int(order2.order_number.split("-")[-1])
        assert seq2 == seq1 + 1


# ------------------------------------------------------------------
# Integration Tests — OrderService (FSM + Inventory)
# ------------------------------------------------------------------
class TestOrderFSM:
    def test_create_order_status_is_requested(self, order):
        assert order.status == OrderStatus.REQUESTED

    def test_cannot_approve_before_review(self, admin_user, order):
        with pytest.raises(БизнесАлдаа):
            OrderService.approve(order, admin_user)

    def test_full_happy_path_to_completed(
        self, admin_user, order, stocked_variant, stock, product_cost
    ):
        order = OrderService.start_review(order, admin_user)
        assert order.status == OrderStatus.UNDER_REVIEW

        order = OrderService.approve(order, admin_user)
        assert order.status == OrderStatus.PAYMENT_PENDING
        stock.refresh_from_db()
        assert stock.reserved_quantity == 5

        order = OrderService.transition_status(order, OrderStatus.PAYMENT_REVIEW, admin_user)
        order = OrderService.transition_status(order, OrderStatus.PAYMENT_CONFIRMED, admin_user)

        grouped = GroupedOrderService.create(admin_user)
        order = OrderService.group(order, grouped, admin_user)
        assert order.status == OrderStatus.GROUPED_ORDER
        assert order.grouped_order_id == grouped.id

        order = OrderService.mark_arrived(order, admin_user)
        assert order.status == OrderStatus.ARRIVED

        order = OrderService.ship(order, admin_user)
        assert order.status == OrderStatus.SHIPPING
        stock.refresh_from_db()
        assert stock.quantity == 45  # 50 - 5 зарлагадсан
        assert stock.reserved_quantity == 0

        order = OrderService.complete(order, admin_user)
        assert order.status == OrderStatus.COMPLETED

        # Захиалгын түүх бүрэн бичигдсэн эсэх: REQUESTED, UNDER_REVIEW,
        # APPROVED, PAYMENT_PENDING, PAYMENT_REVIEW, PAYMENT_CONFIRMED,
        # GROUPED_ORDER, ARRIVED, SHIPPING, COMPLETED — 10 шилжилт
        assert order.status_history.count() == 10

    def test_reject_requires_reason(self, admin_user, order):
        order = OrderService.start_review(order, admin_user)
        with pytest.raises(БизнесАлдаа):
            OrderService.reject(order, admin_user, reason="")

    def test_reject_sets_status_and_reason(self, admin_user, order):
        order = OrderService.start_review(order, admin_user)
        order = OrderService.reject(order, admin_user, reason="Нөөц хүрэлцэхгүй")
        assert order.status == OrderStatus.REJECTED
        assert order.rejected_reason == "Нөөц хүрэлцэхгүй"

    def test_cancel_after_approval_releases_reservation(self, admin_user, order, stock):
        order = OrderService.start_review(order, admin_user)
        order = OrderService.approve(order, admin_user)
        stock.refresh_from_db()
        assert stock.reserved_quantity == 5

        order = OrderService.cancel(order, admin_user, reason="Хэрэглэгч цуцаллаа")
        assert order.status == OrderStatus.CANCELLED
        stock.refresh_from_db()
        assert stock.reserved_quantity == 0

    def test_cancel_without_reservation_does_not_touch_stock(self, admin_user, order, stock):
        # REQUESTED төлөвт байхад цуцлах — нөөцлөлт хараахан хийгдээгүй
        order = OrderService.cancel(order, admin_user, reason="Шалтгаан")
        assert order.status == OrderStatus.CANCELLED
        stock.refresh_from_db()
        assert stock.reserved_quantity == 0

    def test_invalid_transition_raises_business_error(self, order):
        with pytest.raises(БизнесАлдаа):
            OrderService.transition_status(order, OrderStatus.COMPLETED, None)


# ------------------------------------------------------------------
# API Tests
# ------------------------------------------------------------------
class TestOrderAPI:
    def test_seller_creates_order(self, main_seller_client, stocked_variant):
        response = main_seller_client.post(
            "/api/v1/orders/",
            {"items": [{"variant_uuid": str(stocked_variant.uuid), "quantity": 2}]},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["data"]["status"] == "REQUESTED"

    def test_empty_items_rejected(self, main_seller_client):
        response = main_seller_client.post(
            "/api/v1/orders/", {"items": []}, format="json"
        )
        assert response.status_code == 400

    def test_admin_cannot_create_order(self, admin_client, stocked_variant):
        response = admin_client.post(
            "/api/v1/orders/",
            {"items": [{"variant_uuid": str(stocked_variant.uuid), "quantity": 1}]},
            format="json",
        )
        assert response.status_code == 403

    def test_contract_seller_sees_only_own_orders(
        self, contract_seller_client, contract_seller, main_seller, stocked_variant
    ):
        OrderService.create_order(
            seller=contract_seller, items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 1}]
        )
        OrderService.create_order(
            seller=main_seller, items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 1}]
        )
        response = contract_seller_client.get("/api/v1/orders/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 1

    def test_main_seller_sees_own_and_contract_sellers_orders(
        self, main_seller_client, main_seller, contract_seller, another_main_seller, stocked_variant
    ):
        OrderService.create_order(
            seller=main_seller, items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 1}]
        )
        OrderService.create_order(
            seller=contract_seller, items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 1}]
        )
        OrderService.create_order(
            seller=another_main_seller, items_data=[{"variant_uuid": stocked_variant.uuid, "quantity": 1}]
        )
        response = main_seller_client.get("/api/v1/orders/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 2

    def test_seller_cannot_review_order(self, main_seller_client, order):
        response = main_seller_client.post(f"/api/v1/orders/{order.uuid}/review/")
        assert response.status_code == 403

    def test_seller_can_cancel_own_order(self, main_seller_client, order):
        response = main_seller_client.post(
            f"/api/v1/orders/{order.uuid}/cancel/",
            {"reason": "Хэрэгцээгүй боллоо"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["data"]["status"] == "CANCELLED"

    def test_unrelated_seller_gets_not_found_not_403(self, another_main_seller, api_client, order):
        """RBAC-ийн дагуу харах эрхгүй захиалга дээр 403 (эрхийн татгалзал)
        биш 404 (олдсонгүй) буцаана — захиалгын оршин байгааг ил гаргахгүй."""
        api_client.force_authenticate(user=another_main_seller)
        response = api_client.post(
            f"/api/v1/orders/{order.uuid}/cancel/", {"reason": "x"}, format="json"
        )
        assert response.status_code == 404

    def test_order_detail_endpoint(self, main_seller_client, order):
        response = main_seller_client.get(f"/api/v1/orders/{order.uuid}/")
        assert response.status_code == 200
        assert response.data["data"]["order_number"] == order.order_number

    def test_order_history_endpoint(self, admin_client, order):
        response = admin_client.post(f"/api/v1/orders/{order.uuid}/review/")
        assert response.status_code == 200
        response = admin_client.get(f"/api/v1/orders/{order.uuid}/history/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 2  # REQUESTED + UNDER_REVIEW

    def test_admin_approve_then_reject_flow(self, admin_client, order):
        admin_client.post(f"/api/v1/orders/{order.uuid}/review/")
        response = admin_client.post(
            f"/api/v1/orders/{order.uuid}/reject/",
            {"reason": "Нөөц дууссан"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["data"]["status"] == "REJECTED"
        assert response.data["data"]["rejected_reason"] == "Нөөц дууссан"

    def test_reject_without_reason_returns_400(self, admin_client, order):
        admin_client.post(f"/api/v1/orders/{order.uuid}/review/")
        response = admin_client.post(
            f"/api/v1/orders/{order.uuid}/reject/", {}, format="json"
        )
        assert response.status_code == 400

    def test_group_before_payment_confirmed_rejected(self, admin_client, order):
        admin_client.post(f"/api/v1/orders/{order.uuid}/review/")
        admin_client.post(f"/api/v1/orders/{order.uuid}/approve/")

        grouped_resp = admin_client.post(
            "/api/v1/orders/grouped/", {"note": "тест"}, format="json"
        )
        assert grouped_resp.status_code == 201
        grouped_uuid = grouped_resp.data["data"]["uuid"]

        # PAYMENT_PENDING -> шууд group хийх боломжгүй (FSM хамгаалалт)
        response = admin_client.post(
            f"/api/v1/orders/{order.uuid}/group/",
            {"grouped_order_uuid": grouped_uuid},
            format="json",
        )
        assert response.status_code == 400

        grouped_detail = admin_client.get(f"/api/v1/orders/grouped/{grouped_uuid}/")
        assert grouped_detail.status_code == 200
        assert grouped_detail.data["data"]["order_count"] == 0

    def test_grouped_order_list_admin_only(self, main_seller_client):
        response = main_seller_client.get("/api/v1/orders/grouped/")
        assert response.status_code == 403
