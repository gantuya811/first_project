"""
MERRIGE ERP - Аудитын Repository
Repository Pattern: Database Logic зөвхөн энд байрлана.
"""

from apps.audit.models import AuditLog


class AuditLogRepository:
    @staticmethod
    def list_all(category=None, user_id=None):
        queryset = AuditLog.objects.select_related("user").all()
        if category:
            queryset = queryset.filter(category=category)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
