"""
MERRIGE ERP - Захиалгын (Order) models
12 төлөвтэй захиалгын workflow: REQUESTED → UNDER_REVIEW → APPROVED/REJECTED
→ PAYMENT_PENDING → PAYMENT_REVIEW → PAYMENT_CONFIRMED → GROUPED_ORDER →
ARRIVED → SHIPPING → COMPLETED (эсвэл CANCELLED). Төлөв шилжилтийн бодит
дүрэм, side-effect (агуулах нөөцлөх/чөлөөлөх) нь apps.orders.services-д
байрлана — энд зөвхөн өгөгдлийн бүтэц.

Захиалгын төлөвийн түүх (OrderStatusHistory) нь InventoryMovement-тэй адил
өөрчлөгдөшгүй (immutable) аудит бичлэг: "Огноо, Цаг, Хэрэглэгч, Шалтгаан"-г
BaseModel-ийн created_at/created_by + reason талбараар бүрэн хадгална.
"""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel
from apps.products.models import ProductVariant


class OrderStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Хүсэлт илгээсэн"
    UNDER_REVIEW = "UNDER_REVIEW", "Хянагдаж байгаа"
    APPROVED = "APPROVED", "Батлагдсан"
    REJECTED = "REJECTED", "Татгалзсан"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Төлбөр хүлээгдэж буй"
    PAYMENT_REVIEW = "PAYMENT_REVIEW", "Төлбөр шалгагдаж буй"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Төлбөр баталгаажсан"
    GROUPED_ORDER = "GROUPED_ORDER", "Нэгдсэн захиалгад орсон"
    ARRIVED = "ARRIVED", "Ирсэн"
    SHIPPING = "SHIPPING", "Хүргэлтэд гарсан"
    COMPLETED = "COMPLETED", "Дууссан"
    CANCELLED = "CANCELLED", "Цуцлагдсан"


class GroupedOrder(BaseModel):
    """Нэгдсэн захиалгын төв: батлагдсан, төлбөр баталгаажсан захиалгуудыг
    нэг бөөнд нэгтгэж, нийлүүлэгч рүү илгээхэд ашиглана. Дугаар: GO-YYYYMM-XXXXX."""

    order_number = models.CharField(
        verbose_name="Дугаар", max_length=20, unique=True, editable=False
    )
    note = models.TextField(verbose_name="Тэмдэглэл", blank=True)

    class Meta:
        verbose_name = "Нэгдсэн захиалга"
        verbose_name_plural = "Нэгдсэн захиалгууд"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number


class Order(BaseModel):
    order_number = models.CharField(
        verbose_name="Захиалгын дугаар", max_length=30, unique=True, editable=False
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Захиалагч",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        verbose_name="Төлөв",
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.REQUESTED,
    )
    grouped_order = models.ForeignKey(
        GroupedOrder,
        verbose_name="Нэгдсэн захиалга",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    note = models.TextField(verbose_name="Тэмдэглэл", blank=True)
    rejected_reason = models.CharField(
        verbose_name="Татгалзсан шалтгаан", max_length=255, blank=True
    )
    cancelled_reason = models.CharField(
        verbose_name="Цуцалсан шалтгаан", max_length=255, blank=True
    )

    class Meta:
        verbose_name = "Захиалга"
        verbose_name_plural = "Захиалгууд"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order, verbose_name="Захиалга", on_delete=models.CASCADE, related_name="items"
    )
    variant = models.ForeignKey(
        ProductVariant,
        verbose_name="Барааны хувилбар",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(verbose_name="Тоо ширхэг")
    unit_price = models.DecimalField(
        verbose_name="Нэгжийн үнэ", max_digits=12, decimal_places=2
    )

    class Meta:
        verbose_name = "Захиалгын мөр"
        verbose_name_plural = "Захиалгын мөрүүд"

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.order.order_number} / {self.variant} x{self.quantity}"


class OrderStatusHistory(BaseModel):
    """Захиалгын төлөвийн өөрчлөгдөшгүй (immutable) түүх."""

    order = models.ForeignKey(
        Order,
        verbose_name="Захиалга",
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    from_status = models.CharField(
        verbose_name="Өмнөх төлөв", max_length=30, choices=OrderStatus.choices, blank=True
    )
    to_status = models.CharField(
        verbose_name="Шинэ төлөв", max_length=30, choices=OrderStatus.choices
    )
    reason = models.CharField(verbose_name="Шалтгаан", max_length=255, blank=True)

    class Meta:
        verbose_name = "Захиалгын төлөвийн түүх"
        verbose_name_plural = "Захиалгын төлөвийн түүхүүд"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number}: {self.from_status or '—'} → {self.to_status}"

    def save(self, *args, **kwargs):
        if self.pk and OrderStatusHistory.all_objects.filter(pk=self.pk).exists():
            raise RuntimeError(
                "Захиалгын төлөвийн түүхийг засварлах боломжгүй (immutable)."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Захиалгын төлөвийн түүхийг устгах боломжгүй (immutable).")
