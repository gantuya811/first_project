"""
MERRIGE ERP - Notifications app-ийн тестүүд
Signal-ээр автоматаар үүсэх мэдэгдлийг (STEP12) шалгана.
"""

import pytest
from django.core import mail

from apps.inventory.services import InventoryService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.orders.services import OrderService

pytestmark = pytest.mark.django_db


class TestNotificationService:
    def test_notify_creates_record_and_sends_email(self, main_seller):
        notification = NotificationService.notify(
            recipient=main_seller,
            notification_type="ORDER_APPROVED",
            title="Захиалга батлагдлаа",
            message="Тест мессеж",
        )
        assert notification.is_read is False
        assert len(mail.outbox) == 1
        assert main_seller.email in mail.outbox[0].to

    def test_notify_without_email_skips_sending(self, main_seller):
        main_seller.email = ""
        main_seller.save(update_fields=["email"])
        NotificationService.notify(
            recipient=main_seller,
            notification_type="ORDER_APPROVED",
            title="Т",
            message="Т",
        )
        assert len(mail.outbox) == 0

    def test_mark_as_read(self, main_seller):
        notification = NotificationService.notify(
            recipient=main_seller, notification_type="ORDER_APPROVED", title="Т", message="Т"
        )
        NotificationService.mark_as_read(notification)
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_mark_all_as_read(self, main_seller):
        for _ in range(3):
            NotificationService.notify(
                recipient=main_seller, notification_type="ORDER_APPROVED", title="Т", message="Т"
            )
        NotificationService.mark_all_as_read(main_seller)
        assert Notification.objects.filter(recipient=main_seller, is_read=False).count() == 0


class TestOrderApprovalTriggersNotification:
    def test_approve_creates_notification_for_seller(
        self, admin_user, main_seller, variant, stock
    ):
        InventoryService.stock_in(variant, 10, admin_user)
        order = OrderService.create_order(
            seller=main_seller, items_data=[{"variant_uuid": variant.uuid, "quantity": 1}]
        )
        order = OrderService.start_review(order, admin_user)
        OrderService.approve(order, admin_user)

        notifications = Notification.objects.filter(recipient=main_seller)
        titles = set(notifications.values_list("title", flat=True))
        assert "Захиалга батлагдлаа" in titles


class TestNotificationAPI:
    def test_list_own_notifications_only(self, main_seller_client, main_seller, another_main_seller):
        NotificationService.notify(
            recipient=main_seller, notification_type="ORDER_APPROVED", title="Миний", message="М"
        )
        NotificationService.notify(
            recipient=another_main_seller, notification_type="ORDER_APPROVED", title="Бусдын", message="Б"
        )
        response = main_seller_client.get("/api/v1/notifications/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 1
        assert response.data["data"]["results"][0]["title"] == "Миний"

    def test_cannot_read_others_notification(self, main_seller_client, another_main_seller):
        notification = NotificationService.notify(
            recipient=another_main_seller, notification_type="ORDER_APPROVED", title="Б", message="Б"
        )
        response = main_seller_client.post(f"/api/v1/notifications/{notification.uuid}/read/")
        assert response.status_code == 404

    def test_unread_count(self, main_seller_client, main_seller):
        NotificationService.notify(
            recipient=main_seller, notification_type="ORDER_APPROVED", title="Т", message="Т"
        )
        response = main_seller_client.get("/api/v1/notifications/unread-count/")
        assert response.status_code == 200
        assert response.data["data"]["unread_count"] == 1
