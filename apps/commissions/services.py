"""
MERRIGE ERP - Шимтгэлийн Service Layer
Захиалга COMPLETED болоход (apps.commissions.signals-ээр автоматаар,
эсвэл Админ гараар дахин бодуулахад) шимтгэлийг apps.profits-ийн Ашгийн
задаргаанаас (main_seller_profit / contract_seller_profit) тооцоолно.
"""

from decimal import Decimal

from django.db import transaction

from apps.commissions.models import Commission
from apps.commissions.repositories import CommissionRepository
from apps.orders.models import OrderStatus
from apps.profits.services import ProfitService
from apps.shared.exceptions import БизнесАлдаа


class CommissionService:
    @staticmethod
    @transaction.atomic
    def generate_for_order(order, actor=None):
        """Зөвхөн COMPLETED захиалганд, давхардуулахгүйгээр шимтгэл үүсгэнэ.
        `actor` нь бичлэгийг үүсгэсэн хэрэглэгч (Админ гараар дуудвал
        request.user, автомат signal-аас бол COMPLETED болгосон Админ)."""
        if order.status != OrderStatus.COMPLETED:
            raise БизнесАлдаа(
                "Шимтгэл зөвхөн дууссан (COMPLETED) захиалганд бодогдоно."
            )

        if CommissionRepository.exists_for_order(order):
            raise БизнесАлдаа("Энэ захиалганд шимтгэл аль хэдийн бодогдсон байна.")

        total_commission = Decimal("0")
        for item in order.items.select_related("variant__product"):
            breakdown = ProfitService.calculate_breakdown(item.variant.product)
            if order.seller.is_main_seller:
                unit_profit = breakdown["main_seller_profit"]
            else:
                unit_profit = breakdown["contract_seller_profit"]
            total_commission += unit_profit * item.quantity

        return Commission.objects.create(
            order=order,
            seller=order.seller,
            amount=total_commission,
            created_by=actor,
        )
