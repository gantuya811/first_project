"""
MERRIGE ERP - Accounts app-ийн тестүүд
Unit: User модель, бизнес дүрмийн шалгалт (clean(), Soft Delete Only).
Integration: AuthService, UserService.
API: Бүртгэл, Нэвтрэлт, Батлах, RBAC.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.accounts.services import AuthService, UserService
from apps.shared.exceptions import БизнесАлдаа

pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Unit Tests — models.py
# ------------------------------------------------------------------
class TestUserModel:
    def test_contract_seller_requires_parent_seller(self, main_seller):
        user = User(
            phone_number="87111111",
            email="x@test.mn",
            first_name="Тест",
            last_name="Хэрэглэгч",
            role=User.Role.CONTRACT_SELLER,
        )
        user.set_password("x")
        with pytest.raises(ValidationError):
            user.full_clean(exclude=["password"])

    def test_contract_seller_with_parent_passes(self, main_seller):
        user = User(
            phone_number="87111112",
            email="y@test.mn",
            first_name="Тест",
            last_name="Хэрэглэгч",
            role=User.Role.CONTRACT_SELLER,
            parent_seller=main_seller,
        )
        user.set_password("x")
        user.full_clean(exclude=["password"])  # ValidationError шидэхгүй байх ёстой

    def test_main_seller_cannot_have_parent_seller(self, main_seller):
        user = User(
            phone_number="88111113",
            email="z@test.mn",
            first_name="Тест",
            last_name="Хэрэглэгч",
            role=User.Role.MAIN_SELLER,
            parent_seller=main_seller,
        )
        user.set_password("x")
        with pytest.raises(ValidationError):
            user.full_clean(exclude=["password"])

    def test_delete_is_soft_delete_only(self, main_seller):
        main_seller.delete()
        assert not User.objects.filter(id=main_seller.id).exists()
        refreshed = User.all_objects.get(id=main_seller.id)
        assert refreshed.is_deleted is True
        assert refreshed.deleted_at is not None

    def test_get_full_name(self, main_seller):
        assert main_seller.get_full_name() == "Борлуулагч Үндсэн"


# ------------------------------------------------------------------
# Integration Tests — services.py
# ------------------------------------------------------------------
class TestAuthService:
    def test_authenticate_success(self, main_seller):
        user = AuthService.authenticate("88000001", "MainPass!2026")
        assert user.id == main_seller.id

    def test_authenticate_wrong_password(self, main_seller):
        with pytest.raises(БизнесАлдаа):
            AuthService.authenticate("88000001", "buruu-nuuts-ug")

    def test_authenticate_unapproved_user_blocked(self, admin_user):
        pending = User.objects.create_user(
            phone_number="88999999",
            email="pending@test.mn",
            first_name="Хүлээгдэж",
            last_name="Буй",
            role=User.Role.MAIN_SELLER,
            is_approved=False,
        )
        pending.set_unusable_password()
        pending.save()
        with pytest.raises(БизнесАлдаа):
            AuthService.authenticate("88999999", "whatever")

    def test_change_password_clears_must_change_flag(self, main_seller):
        main_seller.must_change_password = True
        main_seller.save(update_fields=["must_change_password"])
        AuthService.change_password(main_seller, "NewSecurePass!2026")
        main_seller.refresh_from_db()
        assert main_seller.must_change_password is False
        assert main_seller.check_password("NewSecurePass!2026")


class TestUserService:
    def test_register_contract_seller_requires_approved_main_seller(self, main_seller):
        data = {
            "phone_number": "87222222",
            "email": "new@test.mn",
            "first_name": "Шинэ",
            "last_name": "Хэрэглэгч",
            "role": User.Role.CONTRACT_SELLER,
            "parent_seller_phone": "88000001",
            "store_name": "",
            "province": "",
            "soum": "",
            "district": "",
            "address": "",
            "bank_name": "",
            "account_number": "",
        }
        user = UserService.register(data)
        assert user.parent_seller_id == main_seller.id
        assert user.is_approved is False
        assert user.has_usable_password() is False

    def test_register_contract_seller_unapproved_parent_fails(self, admin_user):
        pending_main = User.objects.create_user(
            phone_number="88333333",
            email="pm@test.mn",
            first_name="Батлагдаагүй",
            last_name="Үндсэн",
            role=User.Role.MAIN_SELLER,
            is_approved=False,
        )
        pending_main.set_unusable_password()
        pending_main.save()

        data = {
            "phone_number": "87333333",
            "email": "cs@test.mn",
            "first_name": "Гэрээт",
            "last_name": "Тест",
            "role": User.Role.CONTRACT_SELLER,
            "parent_seller_phone": "88333333",
            "store_name": "",
            "province": "",
            "soum": "",
            "district": "",
            "address": "",
            "bank_name": "",
            "account_number": "",
        }
        with pytest.raises(БизнесАлдаа):
            UserService.register(data)

    def test_approve_generates_usable_password(self, admin_user):
        pending = User.objects.create_user(
            phone_number="88444444",
            email="ap@test.mn",
            first_name="Батлах",
            last_name="Тест",
            role=User.Role.MAIN_SELLER,
            is_approved=False,
        )
        pending.set_unusable_password()
        pending.save()

        user, password = UserService.approve(pending.uuid, approved_by=admin_user)
        assert user.is_approved is True
        assert user.approved_by_id == admin_user.id
        assert user.check_password(password)

    def test_approve_twice_fails(self, main_seller, admin_user):
        with pytest.raises(БизнесАлдаа):
            UserService.approve(main_seller.uuid, approved_by=admin_user)

    def test_list_visible_rbac_hierarchy(self, admin_user, main_seller, contract_seller, another_main_seller):
        admin_visible = UserService.list_visible(admin_user)
        assert admin_visible.count() >= 4

        main_visible = UserService.list_visible(main_seller)
        visible_ids = set(main_visible.values_list("id", flat=True))
        assert main_seller.id in visible_ids
        assert contract_seller.id in visible_ids
        assert another_main_seller.id not in visible_ids

        contract_visible = UserService.list_visible(contract_seller)
        assert set(contract_visible.values_list("id", flat=True)) == {contract_seller.id}


# ------------------------------------------------------------------
# API Tests
# ------------------------------------------------------------------
class TestAuthAPI:
    def test_login_missing_fields_returns_mongolian_errors(self, api_client):
        response = api_client.post("/api/v1/auth/login/", {}, format="json")
        assert response.status_code == 400
        assert response.data["success"] is False
        assert "phone_number" in response.data["errors"]

    def test_login_success(self, api_client, main_seller):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"phone_number": "88000001", "password": "MainPass!2026"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["success"] is True
        assert "access" in response.data["data"]
        assert response.data["data"]["must_change_password"] is False

    def test_login_wrong_password_mongolian_message(self, api_client, main_seller):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"phone_number": "88000001", "password": "buruu"},
            format="json",
        )
        assert response.status_code == 400
        assert "буруу" in response.data["message"]

    def test_me_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == 401

    def test_me_returns_own_profile(self, main_seller_client, main_seller):
        response = main_seller_client.get("/api/v1/auth/me/")
        assert response.status_code == 200
        assert response.data["data"]["phone_number"] == main_seller.phone_number


class TestUserManagementAPI:
    def test_register_creates_pending_user(self, api_client, main_seller):
        response = api_client.post(
            "/api/v1/users/register/",
            {
                "phone_number": "87555555",
                "email": "reg@test.mn",
                "first_name": "Бүртгэл",
                "last_name": "Тест",
                "role": "CONTRACT_SELLER",
                "parent_seller_phone": "88000001",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["data"]["is_approved"] is False

    def test_register_as_admin_role_forbidden(self, api_client):
        response = api_client.post(
            "/api/v1/users/register/",
            {
                "phone_number": "87666666",
                "email": "adm@test.mn",
                "first_name": "Тест",
                "last_name": "Админ",
                "role": "ADMIN",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_seller_cannot_approve_users(self, main_seller_client, contract_seller):
        response = main_seller_client.post(
            f"/api/v1/users/{contract_seller.uuid}/approve/"
        )
        assert response.status_code == 403

    def test_admin_can_approve_user(self, admin_client, admin_user):
        pending = User.objects.create_user(
            phone_number="88777777",
            email="p2@test.mn",
            first_name="Хүлээгдэж",
            last_name="Буй2",
            role=User.Role.MAIN_SELLER,
            is_approved=False,
        )
        pending.set_unusable_password()
        pending.save()

        response = admin_client.post(f"/api/v1/users/{pending.uuid}/approve/")
        assert response.status_code == 200
        assert response.data["data"]["user"]["is_approved"] is True
        assert "generated_password" in response.data["data"]

    def test_contract_seller_sees_only_self(self, contract_seller_client, contract_seller):
        response = contract_seller_client.get("/api/v1/users/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 1
