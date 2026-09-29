"""
MERRIGE ERP - pytest-ийн нийтлэг fixture-үүд
Бүх app-ийн тест энд тодорхойлсон хэрэглэгч/өгөгдлийн fixture-ийг
дахин ашиглана (Unit/Integration/API тестийн давхардлыг багасгана).
"""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.inventory.models import Stock
from apps.products.models import Product, ProductVariant
from apps.profits.models import ProductCost, ProfitDistributionConfig


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        phone_number="99000001",
        email="admin@test.mn",
        first_name="Админ",
        last_name="Тест",
        password="AdminPass!2026",
    )


@pytest.fixture
def main_seller(db, admin_user):
    return User.objects.create_user(
        phone_number="88000001",
        email="main@test.mn",
        first_name="Үндсэн",
        last_name="Борлуулагч",
        password="MainPass!2026",
        role=User.Role.MAIN_SELLER,
        is_approved=True,
        approved_by=admin_user,
        must_change_password=False,
    )


@pytest.fixture
def contract_seller(db, admin_user, main_seller):
    return User.objects.create_user(
        phone_number="87000001",
        email="contract@test.mn",
        first_name="Гэрээт",
        last_name="Борлуулагч",
        password="ContractPass!2026",
        role=User.Role.CONTRACT_SELLER,
        parent_seller=main_seller,
        is_approved=True,
        approved_by=admin_user,
        must_change_password=False,
    )


@pytest.fixture
def another_main_seller(db, admin_user):
    """RBAC-ийн "надаас өөр" тохиолдлыг шалгахад ашиглана."""
    return User.objects.create_user(
        phone_number="88000002",
        email="main2@test.mn",
        first_name="Хоёрдугаар",
        last_name="Борлуулагч",
        password="MainPass2!2026",
        role=User.Role.MAIN_SELLER,
        is_approved=True,
        approved_by=admin_user,
        must_change_password=False,
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def main_seller_client(api_client, main_seller):
    api_client.force_authenticate(user=main_seller)
    return api_client


@pytest.fixture
def contract_seller_client(api_client, contract_seller):
    api_client.force_authenticate(user=contract_seller)
    return api_client


@pytest.fixture
def profit_distribution(db):
    return ProfitDistributionConfig.objects.create(
        owner_percentage=Decimal("50.00"),
        main_seller_percentage=Decimal("20.00"),
        contract_seller_percentage=Decimal("30.00"),
        is_active=True,
    )


@pytest.fixture
def product(db):
    return Product.objects.create(
        code="TEST001",
        name="Тест бараа",
        price=Decimal("100000.00"),
        status="ACTIVE",
    )


@pytest.fixture
def product_cost(db, product):
    """Нийт зардал = 50000, Цэвэр ашиг = 50000 (RRP=100000)."""
    return ProductCost.objects.create(
        product=product,
        original_price=Decimal("40000.00"),
        shipping_cost=Decimal("3000.00"),
        packaging_cost=Decimal("1000.00"),
        transfer_fee=Decimal("2000.00"),
        risk_reserve=Decimal("1000.00"),
        marketing_cost=Decimal("3000.00"),
    )


@pytest.fixture
def variant(db, product):
    return ProductVariant.objects.create(product=product, color="BLACK", size="M")


@pytest.fixture
def stock(db, variant):
    """ProductVariant үүсэхэд signal-аар автоматаар үүссэн Stock мөрийг буцаана."""
    return Stock.objects.get(variant=variant)
