"""
MERRIGE ERP - Төлбөрийн (Payment) models
Дүрэм:
- Баримт заавал байна (receipt_file NOT NULL).
- Нэг төлбөрийг дахин баталж/татгалзаж болохгүй (status PENDING-ээс өөр
  бол Service Layer-д хориглоно).
- Татгалзсан шалтгаан хадгална (rejected_reason).

Захиалга нэг удаа татгалзагдсан төлбөртэй байж болох тул (дахин баримт
оруулах боломжтой) Payment-ийг Order дээр OneToOne биш ForeignKey-ээр
холбож, бүх оролдлогын түүхийг хадгална.
"""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel
from apps.orders.models import Order
from apps.shared.validators import validate_receipt_extension, validate_receipt_size


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Шалгагдаж буй"
    CONFIRMED = "CONFIRMED", "Баталгаажсан"
    REJECTED = "REJECTED", "Татгалзсан"


def receipt_upload_path(instance, filename):
    return f"payments/{instance.order.uuid}/{instance.uuid}_{filename}"


class Payment(BaseModel):
    order = models.ForeignKey(
        Order,
        verbose_name="Захиалга",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    receipt_file = models.FileField(
        verbose_name="Төлбөрийн баримт",
        upload_to=receipt_upload_path,
        validators=[validate_receipt_extension, validate_receipt_size],
    )
    amount = models.DecimalField(
        verbose_name="Төлсөн дүн", max_digits=14, decimal_places=2
    )
    status = models.CharField(
        verbose_name="Төлөв",
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    rejected_reason = models.CharField(
        verbose_name="Татгалзсан шалтгаан", max_length=255, blank=True
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Баталгаажуулсан админ",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_payments",
    )
    verified_at = models.DateTimeField(
        verbose_name="Баталгаажуулсан огноо", null=True, blank=True
    )

    class Meta:
        verbose_name = "Төлбөр"
        verbose_name_plural = "Төлбөрүүд"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.amount} ({self.get_status_display()})"
