"""
MERRIGE ERP - Ашгийн Service Layer
Ашиг хуваарилалтын хувь тохируулах, барааны өртөг тохируулах, бүрэн
задаргаа (Админ) болон хязгаарлагдмал харагдац (Борлуулагч) тооцоолох
логик энд байрлана.
"""

from decimal import Decimal

from django.db import transaction

from apps.accounts.models import User
from apps.profits.models import ProductCost, ProfitDistributionConfig
from apps.shared.exceptions import БизнесАлдаа

HUNDRED = Decimal("100")
CENT = Decimal("0.01")


class ProfitService:
    @staticmethod
    def get_active_config():
        config = (
            ProfitDistributionConfig.objects.filter(is_active=True)
            .order_by("-created_at")
            .first()
        )
        if config is None:
            raise БизнесАлдаа("Ашиг хуваарилалтын тохиргоо олдсонгүй.")
        return config

    @staticmethod
    @transaction.atomic
    def set_distribution(owner_pct, main_seller_pct, contract_seller_pct, user):
        """Шинэ ашиг хуваарилалтын хувь тохируулна. Хуучин идэвхтэй
        тохиргоог идэвхгүй болгож, түүхийг хадгална (hardcode хийхгүй)."""
        total = owner_pct + main_seller_pct + contract_seller_pct
        if total != HUNDRED:
            raise БизнесАлдаа(
                f"Гурван хувийн нийлбэр 100% байх ёстой (одоогийн нийлбэр: {total}%)."
            )

        ProfitDistributionConfig.objects.filter(is_active=True).update(is_active=False)
        return ProfitDistributionConfig.objects.create(
            owner_percentage=owner_pct,
            main_seller_percentage=main_seller_pct,
            contract_seller_percentage=contract_seller_pct,
            is_active=True,
            created_by=user,
        )

    @staticmethod
    @transaction.atomic
    def set_product_cost(product, data):
        cost, _ = ProductCost.objects.update_or_create(product=product, defaults=data)
        return cost

    @staticmethod
    def calculate_breakdown(product):
        """Барааны бүрэн ашгийн задаргаа (зөвхөн Админ харна)."""
        cost = getattr(product, "cost", None)
        if cost is None:
            raise БизнесАлдаа("Энэ бараанд өртгийн мэдээлэл оруулаагүй байна.")

        config = ProfitService.get_active_config()
        net_profit = cost.net_profit

        owner_profit = (net_profit * config.owner_percentage / HUNDRED).quantize(CENT)
        main_seller_profit = (
            net_profit * config.main_seller_percentage / HUNDRED
        ).quantize(CENT)
        # Гэрээт Борлуулагчийн хувийг хасалтаар олж, дугуйлалтын алдаанаас
        # болж 3 хэсгийн нийлбэр цэвэр ашгаас зөрөхөөс сэргийлнэ.
        contract_seller_profit = net_profit - owner_profit - main_seller_profit

        return {
            "original_price": cost.original_price,
            "shipping_cost": cost.shipping_cost,
            "packaging_cost": cost.packaging_cost,
            "transfer_fee": cost.transfer_fee,
            "risk_reserve": cost.risk_reserve,
            "marketing_cost": cost.marketing_cost,
            "total_cost": cost.total_cost,
            "supplier_info": cost.supplier_info,
            "rrp": product.price,
            "net_profit": net_profit,
            "owner_profit": owner_profit,
            "main_seller_profit": main_seller_profit,
            "contract_seller_profit": contract_seller_profit,
            "main_seller_price": product.price - main_seller_profit,
            "contract_seller_price": product.price - contract_seller_profit,
        }

    @staticmethod
    def calculate_seller_view(product, role):
        """Борлуулагчид зориулсан хязгаарлагдмал харагдац: RRP, Own Price,
        Own Profit. Анхны үнэ, Нийт зардал, Эзний ашиг ЭНД ОРОХГҮЙ."""
        breakdown = ProfitService.calculate_breakdown(product)

        if role == User.Role.MAIN_SELLER:
            own_price = breakdown["main_seller_price"]
            own_profit = breakdown["main_seller_profit"]
        else:
            own_price = breakdown["contract_seller_price"]
            own_profit = breakdown["contract_seller_profit"]

        return {
            "rrp": breakdown["rrp"],
            "own_price": own_price,
            "own_profit": own_profit,
        }
