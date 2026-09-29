"""
MERRIGE ERP - Шимтгэлийн (Commission) models
Дүрэм:
- Шимтгэл зөвхөн дууссан (COMPLETED) захиалганд бодогдоно.
- Давхар шимтгэл үүсэхгүй (нэг захиалганд хамгийн ихдээ нэг идэвхтэй
  шимтгэл — Soft Delete-той нийцтэй нөхцөлт UniqueConstraint).
- Шимтгэлийн түүх хадгална — Commission нь InventoryMovement/
  OrderStatusHistory-тэй адил өөрчлөгдөшгүй (immutable) аудит бичлэг.
"""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel
from apps.orders.models import Order


class Commission(BaseModel):
    order = models.ForeignKey(
        Order,
        verbose_name="Захиалга",
        on_delete=models.PROTECT,
        related_name="commissions",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Борлуулагч",
        on_delete=models.PROTECT,
        related_name="commissions",
    )
    amount = models.DecimalField(
        verbose_name="Шимтгэлийн дүн", max_digits=14, decimal_places=2
    )

    class Meta:
        verbose_name = "Шимтгэл"
        verbose_name_plural = "Шимтгэлүүд"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["order"],
                condition=models.Q(is_deleted=False),
                name="unique_active_commission_per_order",
            )
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.seller.get_full_name()} - {self.amount}"

    def save(self, *args, **kwargs):
        if self.pk and Commission.all_objects.filter(pk=self.pk).exists():
            raise RuntimeError("Шимтгэлийн бичлэгийг засварлах боломжгүй (immutable).")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Шимтгэлийн бичлэгийг устгах боломжгүй (immutable).")
