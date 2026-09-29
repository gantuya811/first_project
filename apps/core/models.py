"""
MERRIGE ERP - Core Abstract Models
Бүх модулийн models.py эдгээр abstract класснуудаас удамшиж, DATABASE STANDARD
шаардлагын дагуу (id, uuid, created_at, updated_at, created_by, updated_by,
is_deleted, deleted_at) нэгдсэн бүтэцтэй байх ёстой. Дараагийн бүх STEP-үүд
эндээс BaseModel-ийг удамшина. Устгалт зөвхөн Soft Delete байх ёстой тул
.delete()-ийг бодит устгалаас Soft Delete болгож дарж бичсэн.
"""

import uuid as uuid_lib

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.managers import AllObjectsManager, SoftDeleteManager


class TimeStampedModel(models.Model):
    """Үүсгэсэн болон өөрчилсөн огноог хадгалах abstract загвар."""

    created_at = models.DateTimeField(
        verbose_name="Үүсгэсэн огноо", auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Өөрчилсөн огноо", auto_now=True
    )

    class Meta:
        abstract = True


class UserTrackingModel(models.Model):
    """Бичлэгийг хэн үүсгэж, хэн сүүлд өөрчилснийг хадгалах abstract загвар."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Үүсгэсэн хэрэглэгч",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Сүүлд өөрчилсөн хэрэглэгч",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated",
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Мэдээллийг бодитоор устгахгүйгээр архивлах (Soft Delete Only дүрэм).
    Django-ийн анхдагч .delete() дуудлагыг ч Soft Delete болгож дарсан тул
    аль ч давхаргаас (View, Admin, Service) устгал зөвхөн Soft Delete байна.
    """

    is_deleted = models.BooleanField(
        verbose_name="Устгагдсан эсэх", default=False, db_index=True
    )
    deleted_at = models.DateTimeField(
        verbose_name="Устгасан огноо", null=True, blank=True
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Django-ийн анхдагч instance.delete()-ийг Soft Delete болгож дарна."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["is_deleted", "deleted_at"])

    def soft_delete(self):
        """Service Layer-д илэрхий уншигдахуйц нэрээр ашиглах алиас."""
        self.delete()

    def hard_delete(self, using=None, keep_parents=False):
        """Бодит устгал. Зөвхөн онцгой, зөвшөөрөгдсөн тохиолдолд ашиглана."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Устгагдсан бичлэгийг эргүүлэн идэвхжүүлнэ."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class BaseModel(TimeStampedModel, UserTrackingModel, SoftDeleteModel):
    """
    Системийн бүх домэйн модель (Бараа, Захиалга, Төлбөр, Агуулах гэх мэт)
    энэ классаас удамшина.

    - id: дотоод хурдан холболт/индексэд зориулсан автомат тоон түлхүүр
      (DEFAULT_AUTO_FIELD = BigAutoField тул тодорхой бичих шаардлагагүй).
    - uuid: гадаад API/URL-д ил гарах, тааж болшгүй нийтийн танигч.
    """

    uuid = models.UUIDField(
        verbose_name="Нийтийн дугаар (UUID)",
        default=uuid_lib.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
