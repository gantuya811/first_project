"""
MERRIGE ERP - Аудит логийн (AuditLog) models
Бүртгэх ангилал: Нэвтрэлт, Захиалга, Төлбөр, Агуулах, Тохиргоо,
Хэрэглэгчийн өөрчлөлт. Хадгалах: Хэрэглэгч, Огноо, IP, Үйлдэл,
Хуучин утга, Шинэ утга. Аудит лог өөрчлөгдөхгүй (immutable) —
InventoryMovement/OrderStatusHistory/Commission-той адил зарчим.
"""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class AuditCategory(models.TextChoices):
    LOGIN = "LOGIN", "Нэвтрэлт"
    ORDER = "ORDER", "Захиалга"
    PAYMENT = "PAYMENT", "Төлбөр"
    INVENTORY = "INVENTORY", "Агуулах"
    SETTINGS = "SETTINGS", "Тохиргоо"
    USER = "USER", "Хэрэглэгч"


class AuditLog(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Хэрэглэгч",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    category = models.CharField(
        verbose_name="Ангилал", max_length=20, choices=AuditCategory.choices
    )
    action = models.CharField(verbose_name="Үйлдэл", max_length=255)
    ip_address = models.GenericIPAddressField(
        verbose_name="IP хаяг", null=True, blank=True
    )
    object_reference = models.CharField(
        verbose_name="Холбогдох баримт", max_length=100, blank=True
    )
    old_value = models.JSONField(verbose_name="Хуучин утга", null=True, blank=True)
    new_value = models.JSONField(verbose_name="Шинэ утга", null=True, blank=True)

    class Meta:
        verbose_name = "Аудит лог"
        verbose_name_plural = "Аудит логууд"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} - {self.action} ({self.created_at:%Y-%m-%d %H:%M})"

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.all_objects.filter(pk=self.pk).exists():
            raise RuntimeError("Аудит логийг засварлах боломжгүй (immutable).")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Аудит логийг устгах боломжгүй (immutable).")
