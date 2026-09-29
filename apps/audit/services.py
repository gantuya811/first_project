"""
MERRIGE ERP - Аудитын Service Layer
Бүх дуудлага зөвхөн шинэ, өөрчлөгдөшгүй AuditLog бичлэг үүсгэнэ.
apps.audit.signals-ээс дуудагдана (доор тайлбарласан 6 эх сурвалж).
"""

from apps.audit.models import AuditLog


class AuditService:
    @staticmethod
    def log(
        user,
        category,
        action,
        ip_address=None,
        object_reference="",
        old_value=None,
        new_value=None,
    ):
        return AuditLog.objects.create(
            user=user,
            category=category,
            action=action,
            ip_address=ip_address,
            object_reference=object_reference,
            old_value=old_value,
            new_value=new_value,
        )
