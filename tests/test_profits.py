"""
MERRIGE ERP - Profits app-ийн тестүүд
Томьёо: Нийт зардал = Анхны+Тээвэр+Савлагаа+Шимтгэл+Эрсдэл+Маркетинг
        Цэвэр ашиг = RRP - Нийт зардал
        Хувь тус бүр = Цэвэр ашиг × (DB-ээс уншсан хувь)
"""

from decimal import Decimal

import pytest

from apps.profits.models import ProfitDistributionConfig
from apps.profits.services import ProfitService
from apps.shared.exceptions import БизнесАлдаа

pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Unit Tests — models.py
# ------------------------------------------------------------------
class TestProductCostModel:
    def test_total_cost_formula(self, product_cost):
        assert product_cost.total_cost == Decimal("50000.00")

    def test_net_profit_formula(self, product, product_cost):
        # RRP(product.price)=100000, Нийт зардал=50000
        assert product_cost.net_profit == Decimal("50000.00")


# ------------------------------------------------------------------
# Integration Tests — services.py
# ------------------------------------------------------------------
class TestProfitService:
    def test_calculate_breakdown_without_cost_raises(self, product):
        with pytest.raises(БизнесАлдаа):
            ProfitService.calculate_breakdown(product)

    def test_calculate_breakdown_correct_split(self, product, product_cost, profit_distribution):
        breakdown = ProfitService.calculate_breakdown(product)
        assert breakdown["total_cost"] == Decimal("50000.00")
        assert breakdown["net_profit"] == Decimal("50000.00")
        assert breakdown["owner_profit"] == Decimal("25000.00")  # 50%
        assert breakdown["main_seller_profit"] == Decimal("10000.00")  # 20%
        assert breakdown["contract_seller_profit"] == Decimal("15000.00")  # 30%
        assert breakdown["main_seller_price"] == Decimal("90000.00")  # 100000-10000
        assert breakdown["contract_seller_price"] == Decimal("85000.00")  # 100000-15000

    def test_three_shares_always_sum_to_net_profit(self, product, product_cost, profit_distribution):
        """Дугуйлалтын алдаанаас үл хамааран 3 хэсгийн нийлбэр яг цэвэр
        ашигтай тэнцэх ёстой (contract_seller_profit-ийг хасалтаар олдог)."""
        breakdown = ProfitService.calculate_breakdown(product)
        total = (
            breakdown["owner_profit"]
            + breakdown["main_seller_profit"]
            + breakdown["contract_seller_profit"]
        )
        assert total == breakdown["net_profit"]

    def test_seller_view_hides_secret_fields(self, product, product_cost, profit_distribution):
        from apps.accounts.models import User

        view = ProfitService.calculate_seller_view(product, User.Role.MAIN_SELLER)
        assert set(view.keys()) == {"rrp", "own_price", "own_profit"}
        assert view["own_profit"] == Decimal("10000.00")

    def test_set_distribution_requires_sum_100(self, admin_user):
        with pytest.raises(БизнесАлдаа):
            ProfitService.set_distribution(
                Decimal("50"), Decimal("20"), Decimal("40"), admin_user
            )

    def test_set_distribution_deactivates_previous(self, admin_user, profit_distribution):
        new_config = ProfitService.set_distribution(
            Decimal("40"), Decimal("25"), Decimal("35"), admin_user
        )
        profit_distribution.refresh_from_db()
        assert profit_distribution.is_active is False
        assert new_config.is_active is True
        assert ProfitService.get_active_config().id == new_config.id

    def test_get_active_config_missing_raises(self, db):
        # STEP9-ийн migration нь анхны 50/20/30 тохиргоог автоматаар суулгадаг
        # тул "тохиргоо огт байхгүй" нөхцлийг шалгахын тулд идэвхгүй болгоно.
        ProfitDistributionConfig.objects.update(is_active=False)
        with pytest.raises(БизнесАлдаа):
            ProfitService.get_active_config()


# ------------------------------------------------------------------
# API Tests
# ------------------------------------------------------------------
class TestProfitAPI:
    def test_admin_sees_full_breakdown(self, admin_client, product, product_cost, profit_distribution):
        response = admin_client.get(f"/api/v1/profits/products/{product.uuid}/")
        assert response.status_code == 200
        assert "original_price" in response.data["data"]
        assert "owner_profit" in response.data["data"]

    def test_seller_sees_limited_view_only(
        self, main_seller_client, product, product_cost, profit_distribution
    ):
        response = main_seller_client.get(f"/api/v1/profits/products/{product.uuid}/")
        assert response.status_code == 200
        data = response.data["data"]
        assert set(data.keys()) == {"rrp", "own_price", "own_profit"}
        assert "original_price" not in data
        assert "owner_profit" not in data

    def test_seller_cannot_set_cost(self, main_seller_client, product):
        response = main_seller_client.put(
            f"/api/v1/profits/products/{product.uuid}/cost/",
            {"original_price": "1"},
            format="json",
        )
        assert response.status_code == 403

    def test_seller_cannot_view_distribution(self, main_seller_client, profit_distribution):
        response = main_seller_client.get("/api/v1/profits/distribution/")
        assert response.status_code == 403

    def test_admin_update_distribution_wrong_sum_rejected(self, admin_client, profit_distribution):
        response = admin_client.put(
            "/api/v1/profits/distribution/",
            {
                "owner_percentage": "60",
                "main_seller_percentage": "20",
                "contract_seller_percentage": "30",
            },
            format="json",
        )
        assert response.status_code == 400
