"""
MERRIGE ERP - Агуулахын (Inventory) models
Stock: тухайн Барааны хувилбар (Product+Color+Size)-ийн одоогийн үлдэгдэл.
InventoryMovement: Stock In/Out, Reservation, Release, Adjustment бүрийн
өөрчлөгдөшгүй (immutable) аудит түүх ("Аудит лог өөрчлөгдөхгүй" дүрэм).

Дүрэм: Үлдэгдэл (quantity) болон нөөцлөлт (reserved_quantity) хэзээ ч
0-ээс доош орохгүй, мөн reserved_quantity нь quantity-ээс их байж болохгүй
(DB CheckConstraint-оор бүрэн хамгаалагдсан).
"""

from django.db import models

from apps.core.models import BaseModel
from apps.products.models import ProductVariant


class MovementType(models.TextChoices):
    STOCK_IN = "STOCK_IN", "Орлого"
    STOCK_OUT = "STOCK_OUT", "Зарлага"
    RESERVATION = "RESERVATION", "Нөөцлөлт"
    RELEASE_RESERVATION = "RELEASE_RESERVATION", "Нөөцлөлт цуцлах"
    ADJUSTMENT = "ADJUSTMENT", "Тохируулга"


class Stock(BaseModel):
    variant = models.OneToOneField(
        ProductVariant,
        verbose_name="Барааны хувилбар",
        on_delete=models.CASCADE,
        related_name="stock",
    )
    quantity = models.PositiveIntegerField(verbose_name="Нийт үлдэгдэл", default=0)
    reserved_quantity = models.PositiveIntegerField(
        verbose_name="Нөөцлөгдсөн хэмжээ", default=0
    )

    class Meta:
        verbose_name = "Үлдэгдэл"
        verbose_name_plural = "Агуулахын үлдэгдэл"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(reserved_quantity__lte=models.F("quantity")),
                name="inventory_reserved_lte_quantity",
            ),
        ]

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return f"{self.variant} — {self.quantity} ширхэг"


class InventoryMovement(BaseModel):
    """Агуулахын хөдөлгөөн бүрийн өөрчлөгдөшгүй (immutable) түүх.
    Зөвхөн Service Layer-аас (InventoryService) үүсгэгдэнэ, дараа нь хэзээ
    ч засварлагдах, устгагдах боломжгүй."""

    variant = models.ForeignKey(
        ProductVariant,
        verbose_name="Барааны хувилбар",
        on_delete=models.PROTECT,
        related_name="movements",
    )
    movement_type = models.CharField(
        verbose_name="Хөдөлгөөний төрөл", max_length=30, choices=MovementType.choices
    )
    quantity_change = models.IntegerField(verbose_name="Өөрчлөлт (+/-)")
    quantity_before = models.PositiveIntegerField(verbose_name="Өмнөх нийт үлдэгдэл")
    quantity_after = models.PositiveIntegerField(verbose_name="Дараах нийт үлдэгдэл")
    reserved_before = models.PositiveIntegerField(verbose_name="Өмнөх нөөцлөлт")
    reserved_after = models.PositiveIntegerField(verbose_name="Дараах нөөцлөлт")
    reason = models.CharField(verbose_name="Шалтгаан", max_length=255, blank=True)
    reference = models.CharField(
        verbose_name="Холбогдох баримт", max_length=100, blank=True
    )

    class Meta:
        verbose_name = "Агуулахын хөдөлгөөн"
        verbose_name_plural = "Агуулахын хөдөлгөөний түүх"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.variant} / {self.get_movement_type_display()} / {self.quantity_change:+d}"

    def save(self, *args, **kwargs):
        if self.pk and InventoryMovement.all_objects.filter(pk=self.pk).exists():
            raise RuntimeError(
                "Агуулахын хөдөлгөөний түүхийг засварлах боломжгүй (immutable)."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError(
            "Агуулахын хөдөлгөөний түүхийг устгах боломжгүй (immutable)."
        )
