"""
MERRIGE ERP - Core Managers
Soft Delete дэмждэг QuerySet болон Manager классууд.
Агуулах, захиалга, төлбөр зэрэг бүх модуль эндээс удамшина.
"""

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

    def delete(self):
        """Bulk .delete()-ийг Soft Delete болгож дарна (Soft Delete Only дүрэм)."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def soft_delete(self):
        return self.delete()

    def hard_delete(self):
        """Бодит устгал. Зөвхөн онцгой, зөвшөөрөгдсөн тохиолдолд ашиглана."""
        return super().delete()


class SoftDeleteManager(models.Manager):
    """Идэвхтэй (устгагдаагүй) бичлэгүүдийг л буцаах үндсэн менежер."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            is_deleted=False
        )


class AllObjectsManager(models.Manager):
    """Устгасан бичлэгийг оролцуулан бүх бичлэгийг буцаах менежер (аудитад ашиглана)."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)
