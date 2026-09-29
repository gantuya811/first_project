"""
MERRIGE ERP - Агуулахын Service Layer
Барааны бүх хөдөлгөөн (орлого, зарлага, нөөцлөлт, нөөцлөлт цуцлах,
тохируулга) зөвхөн энд, транзакц (transaction.atomic) дотор, мөрийг
түгжиж (select_for_update) гүйцэтгэнэ. "Үлдэгдэл хэзээ ч 0-ээс доош
орохгүй" дүрмийг чанд мөрдөнө. Хөдөлгөөн бүр өөрчлөгдөшгүй
InventoryMovement бичлэг үүсгэж, аудит лог болно.
"""

from django.db import transaction

from apps.inventory.models import InventoryMovement, MovementType
from apps.inventory.repositories import InventoryRepository
from apps.shared.exceptions import БизнесАлдаа


class InventoryService:
    @staticmethod
    @transaction.atomic
    def stock_in(variant, quantity, user, reason="", reference=""):
        """Агуулахад бараа орлого хийнэ (нийт үлдэгдэл нэмэгдэнэ)."""
        if quantity <= 0:
            raise БизнесАлдаа("Орлогын хэмжээ 0-ээс их байх ёстой.")

        stock = InventoryRepository.get_stock_for_update(variant)
        quantity_before, reserved_before = stock.quantity, stock.reserved_quantity

        stock.quantity += quantity
        stock.save(update_fields=["quantity"])

        InventoryService._log_movement(
            stock,
            MovementType.STOCK_IN,
            quantity,
            quantity_before,
            reserved_before,
            user,
            reason,
            reference,
        )
        return stock

    @staticmethod
    @transaction.atomic
    def stock_out(variant, quantity, user, reason="", reference=""):
        """Агуулахаас бараа зарлага хийнэ (нийт үлдэгдэл, шаардлагатай бол
        нөөцлөлт хамт буурна)."""
        if quantity <= 0:
            raise БизнесАлдаа("Зарлагын хэмжээ 0-ээс их байх ёстой.")

        stock = InventoryRepository.get_stock_for_update(variant)
        quantity_before, reserved_before = stock.quantity, stock.reserved_quantity

        if quantity > stock.quantity:
            raise БизнесАлдаа(
                f"Үлдэгдэл хүрэлцэхгүй байна. Одоогийн үлдэгдэл: {stock.quantity}."
            )

        stock.quantity -= quantity
        stock.reserved_quantity = max(0, stock.reserved_quantity - quantity)
        stock.save(update_fields=["quantity", "reserved_quantity"])

        InventoryService._log_movement(
            stock,
            MovementType.STOCK_OUT,
            -quantity,
            quantity_before,
            reserved_before,
            user,
            reason,
            reference,
        )
        return stock

    @staticmethod
    @transaction.atomic
    def reserve(variant, quantity, user, reference=""):
        """Захиалгад зориулж боломжит үлдэгдлээс нөөцлөнө."""
        if quantity <= 0:
            raise БизнесАлдаа("Нөөцлөх хэмжээ 0-ээс их байх ёстой.")

        stock = InventoryRepository.get_stock_for_update(variant)
        quantity_before, reserved_before = stock.quantity, stock.reserved_quantity

        available = stock.quantity - stock.reserved_quantity
        if quantity > available:
            raise БизнесАлдаа(f"Нөөцлөх боломжгүй. Боломжит үлдэгдэл: {available}.")

        stock.reserved_quantity += quantity
        stock.save(update_fields=["reserved_quantity"])

        InventoryService._log_movement(
            stock,
            MovementType.RESERVATION,
            quantity,
            quantity_before,
            reserved_before,
            user,
            "",
            reference,
        )
        return stock

    @staticmethod
    @transaction.atomic
    def release_reservation(variant, quantity, user, reference=""):
        """Захиалга цуцлагдах/өөрчлөгдөх үед нөөцлөлтийг чөлөөлнө."""
        if quantity <= 0:
            raise БизнесАлдаа("Цуцлах хэмжээ 0-ээс их байх ёстой.")

        stock = InventoryRepository.get_stock_for_update(variant)
        quantity_before, reserved_before = stock.quantity, stock.reserved_quantity

        if quantity > stock.reserved_quantity:
            raise БизнесАлдаа("Нөөцлөлтөөс илүү хэмжээг цуцлах боломжгүй.")

        stock.reserved_quantity -= quantity
        stock.save(update_fields=["reserved_quantity"])

        InventoryService._log_movement(
            stock,
            MovementType.RELEASE_RESERVATION,
            -quantity,
            quantity_before,
            reserved_before,
            user,
            "",
            reference,
        )
        return stock

    @staticmethod
    @transaction.atomic
    def adjust(variant, new_quantity, user, reason):
        """Тооллого зэрэг шалтгаанаар үлдэгдлийг гараар тохируулна.
        Шалтгаан заавал шаардлагатай."""
        if not reason:
            raise БизнесАлдаа("Тохируулга хийхэд шалтгаан заавал бичнэ үү.")
        if new_quantity < 0:
            raise БизнесАлдаа("Үлдэгдэл 0-ээс доош байж болохгүй.")

        stock = InventoryRepository.get_stock_for_update(variant)
        quantity_before, reserved_before = stock.quantity, stock.reserved_quantity

        if new_quantity < stock.reserved_quantity:
            raise БизнесАлдаа(
                f"Шинэ үлдэгдэл ({new_quantity}) нөөцлөгдсөн хэмжээнээс "
                f"({stock.reserved_quantity}) бага байж болохгүй."
            )

        delta = new_quantity - stock.quantity
        stock.quantity = new_quantity
        stock.save(update_fields=["quantity"])

        InventoryService._log_movement(
            stock,
            MovementType.ADJUSTMENT,
            delta,
            quantity_before,
            reserved_before,
            user,
            reason,
            "",
        )
        return stock

    @staticmethod
    def _log_movement(
        stock,
        movement_type,
        quantity_change,
        quantity_before,
        reserved_before,
        user,
        reason,
        reference,
    ):
        InventoryMovement.objects.create(
            variant=stock.variant,
            movement_type=movement_type,
            quantity_change=quantity_change,
            quantity_before=quantity_before,
            quantity_after=stock.quantity,
            reserved_before=reserved_before,
            reserved_after=stock.reserved_quantity,
            reason=reason,
            reference=reference,
            created_by=user,
        )
