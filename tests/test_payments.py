"""
MERRIGE ERP - Payments app-ийн тестүүд
"""

from decimal import Decimal
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.inventory.services import InventoryService
from apps.orders.models import OrderStatus
from apps.orders.services import OrderService
from apps.payments.models import PaymentStatus
from apps.payments.services import PaymentService
from apps.shared.exceptions import БизнесАлдаа, ЭрхийнАлдаа

pytestmark = pytest.mark.django_db


def _receipt_file():
    buffer = BytesIO()
    Image.new("RGB", (10, 10), color="blue").save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("receipt.jpg", buffer.read(), content_type="image/jpeg")


@pytest.fixture
def approved_order(admin_user, main_seller, variant, stock):
    InventoryService.stock_in(variant, 20, admin_user)
    order = OrderService.create_order(
        seller=main_seller, items_data=[{"variant_uuid": variant.uuid, "quantity": 2}]
    )
    order = OrderService.start_review(order, admin_user)
    order = OrderService.approve(order, admin_user)  # -> PAYMENT_PENDING
    return order


# ------------------------------------------------------------------
# Integration Tests — services.py
# ------------------------------------------------------------------
class TestPaymentService:
    def test_submit_payment_moves_order_to_review(self, main_seller, approved_order):
        payment = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        approved_order.refresh_from_db()
        assert approved_order.status == OrderStatus.PAYMENT_REVIEW
        assert payment.status == PaymentStatus.PENDING

    def test_submit_payment_wrong_owner_raises(self, another_main_seller, approved_order):
        with pytest.raises(ЭрхийнАлдаа):
            PaymentService.submit_payment(
                approved_order, another_main_seller, _receipt_file(), Decimal("100000")
            )

    def test_double_submit_blocked_by_order_status(self, main_seller, approved_order):
        PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        approved_order.refresh_from_db()
        with pytest.raises(БизнесАлдаа):
            PaymentService.submit_payment(
                approved_order, main_seller, _receipt_file(), Decimal("100000")
            )

    def test_confirm_moves_order_to_confirmed(self, admin_user, main_seller, approved_order):
        payment = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        payment = PaymentService.confirm(payment, admin_user)
        approved_order.refresh_from_db()
        assert payment.status == PaymentStatus.CONFIRMED
        assert approved_order.status == OrderStatus.PAYMENT_CONFIRMED

    def test_confirm_twice_raises(self, admin_user, main_seller, approved_order):
        payment = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        PaymentService.confirm(payment, admin_user)
        with pytest.raises(БизнесАлдаа):
            PaymentService.confirm(payment, admin_user)

    def test_reject_requires_reason(self, admin_user, main_seller, approved_order):
        payment = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        with pytest.raises(БизнесАлдаа):
            PaymentService.reject(payment, admin_user, reason="")

    def test_reject_returns_order_to_payment_pending(self, admin_user, main_seller, approved_order):
        payment = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        payment = PaymentService.reject(payment, admin_user, reason="Дүн таарахгүй")
        approved_order.refresh_from_db()
        assert payment.status == PaymentStatus.REJECTED
        assert approved_order.status == OrderStatus.PAYMENT_PENDING

    def test_resubmit_after_rejection_allowed(self, admin_user, main_seller, approved_order):
        payment1 = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        PaymentService.reject(payment1, admin_user, reason="Буруу")
        approved_order.refresh_from_db()
        payment2 = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        assert payment2.id != payment1.id
        assert approved_order.payments.count() == 2


# ------------------------------------------------------------------
# API Tests
# ------------------------------------------------------------------
class TestPaymentAPI:
    def test_submit_rejects_invalid_extension(self, main_seller_client, approved_order):
        bad_file = SimpleUploadedFile("x.exe", b"bad", content_type="application/octet-stream")
        response = main_seller_client.post(
            f"/api/v1/payments/orders/{approved_order.uuid}/submit/",
            {"receipt_file": bad_file, "amount": "100000"},
            format="multipart",
        )
        assert response.status_code == 400

    def test_submit_success(self, main_seller_client, approved_order):
        response = main_seller_client.post(
            f"/api/v1/payments/orders/{approved_order.uuid}/submit/",
            {"receipt_file": _receipt_file(), "amount": "100000"},
            format="multipart",
        )
        assert response.status_code == 201

    def test_seller_cannot_confirm_payment(self, main_seller_client, main_seller, approved_order):
        payment = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        response = main_seller_client.post(f"/api/v1/payments/{payment.uuid}/confirm/")
        assert response.status_code == 403

    def test_admin_confirm_success(self, admin_client, main_seller, approved_order):
        payment = PaymentService.submit_payment(
            approved_order, main_seller, _receipt_file(), Decimal("100000")
        )
        response = admin_client.post(f"/api/v1/payments/{payment.uuid}/confirm/")
        assert response.status_code == 200
        assert response.data["data"]["status"] == "CONFIRMED"
