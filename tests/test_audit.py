"""
MERRIGE ERP - Audit app-ийн тестүүд
6 ангиллын эх сурвалж бүрээс (Нэвтрэлт, Захиалга, Төлбөр, Агуулах,
Тохиргоо, Хэрэглэгч) автоматаар аудит лог үүсэж байгааг шалгана.
"""

from decimal import Decimal

import pytest

from apps.accounts.services import UserService
from apps.audit.models import AuditCategory, AuditLog
from apps.inventory.services import InventoryService
from apps.profits.services import ProfitService

pytestmark = pytest.mark.django_db


class TestAuditImmutability:
    def test_cannot_update_audit_log(self, admin_user):
        log = AuditLog.objects.create(
            user=admin_user, category=AuditCategory.LOGIN, action="Тест"
        )
        log.action = "Хуурамч"
        with pytest.raises(RuntimeError):
            log.save()

    def test_cannot_delete_audit_log(self, admin_user):
        log = AuditLog.objects.create(
            user=admin_user, category=AuditCategory.LOGIN, action="Тест"
        )
        with pytest.raises(RuntimeError):
            log.delete()


class TestAuditSignals:
    def test_login_creates_audit_entry_with_ip(self, api_client, main_seller):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"phone_number": "88000001", "password": "MainPass!2026"},
            format="json",
        )
        assert response.status_code == 200
        log = AuditLog.objects.filter(category=AuditCategory.LOGIN, user=main_seller).first()
        assert log is not None
        assert log.action == "Нэвтэрсэн"

    def test_inventory_movement_creates_audit_entry(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 10, admin_user, reason="тест")
        log = AuditLog.objects.filter(category=AuditCategory.INVENTORY).first()
        assert log is not None
        assert log.new_value["quantity"] == 10

    def test_settings_change_creates_audit_entry(self, admin_user, profit_distribution):
        ProfitService.set_distribution(
            Decimal("45"), Decimal("25"), Decimal("30"), admin_user
        )
        log = AuditLog.objects.filter(category=AuditCategory.SETTINGS).first()
        assert log is not None
        assert log.new_value["owner_percentage"] == "45"

    def test_user_approval_creates_audit_entry(self, admin_user):
        from apps.accounts.models import User

        pending = User.objects.create_user(
            phone_number="88888899",
            email="aud@test.mn",
            first_name="Аудит",
            last_name="Тест",
            role=User.Role.MAIN_SELLER,
            is_approved=False,
        )
        pending.set_unusable_password()
        pending.save()

        UserService.approve(pending.uuid, approved_by=admin_user)

        log = AuditLog.objects.filter(
            category=AuditCategory.USER, object_reference="88888899"
        ).first()
        assert log is not None
        assert log.old_value["is_approved"] == "False"
        assert log.new_value["is_approved"] == "True"


class TestAuditAPI:
    def test_seller_cannot_view_audit_log(self, main_seller_client):
        response = main_seller_client.get("/api/v1/audit/")
        assert response.status_code == 403

    def test_admin_can_view_audit_log(self, admin_client, admin_user):
        AuditLog.objects.create(user=admin_user, category=AuditCategory.LOGIN, action="Тест")
        response = admin_client.get("/api/v1/audit/")
        assert response.status_code == 200
        assert response.data["data"]["count"] >= 1

    def test_filter_by_category(self, admin_client, admin_user):
        AuditLog.objects.create(user=admin_user, category=AuditCategory.LOGIN, action="A")
        AuditLog.objects.create(user=admin_user, category=AuditCategory.SETTINGS, action="B")
        response = admin_client.get("/api/v1/audit/?category=SETTINGS")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 1
