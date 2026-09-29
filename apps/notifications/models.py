"""
MERRIGE ERP - Мэдэгдлийн (Notification) models
Систем дотоод мэдэгдэл. InventoryMovement/Commission зэрэг аудит
бичлэгээс ялгаатай нь энэ модель ЗАВСАРДАГ (уншсан төлөв өөрчлөгдөнө)
тул immutable ХИЙХГҮЙ.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class NotificationType(models.TextChoices):
    ORDER_APPROVED = "ORDER_APPROVED", "Захиалга батлагдлаа"
    ORDER_REJECTED = "ORDER_REJECTED", "Захиалга татгалзагдлаа"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Төлбөр батлагдлаа"
    STOCK_ARRIVED = "STOCK_ARRIVED", "Бараа ирлээ"
    SHIPPING_STARTED = "SHIPPING_STARTED", "Хүргэлт эхэллээ"
    COMMISSION_CALCULATED = "COMMISSION_CALCULATED", "Шимтгэл бодогдлоо"


class Notification(BaseModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Хүлээн авагч",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        verbose_name="Мэдэгдлийн төрөл", max_length=30, choices=NotificationType.choices
    )
    title = models.CharField(verbose_name="Гарчиг", max_length=255)
    message = models.TextField(verbose_name="Агуулга")
    reference = models.CharField(
        verbose_name="Холбогдох баримт", max_length=100, blank=True
    )
    is_read = models.BooleanField(verbose_name="Уншсан эсэх", default=False)
    read_at = models.DateTimeField(verbose_name="Уншсан огноо", null=True, blank=True)

    class Meta:
        verbose_name = "Мэдэгдэл"
        verbose_name_plural = "Мэдэгдлүүд"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])
