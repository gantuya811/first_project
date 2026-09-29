"""
MERRIGE ERP - Аудитын Views
Views нимгэн байна. Аудит лог зөвхөн Админ-д харагдана (дотоод, эрхийн
болон санхүүгийн нууц мэдээлэл агуулж болзошгүй тул).
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.audit.repositories import AuditLogRepository
from apps.audit.serializers import AuditLogSerializer
from apps.shared.pagination import StandardResultsPagination

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


class AuditLogListView(APIView):
    """GET /api/v1/audit/?category=&user_id= — Аудит логийн жагсаалт
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        category = request.query_params.get("category")
        user_id = request.query_params.get("user_id")
        queryset = AuditLogRepository.list_all(category=category, user_id=user_id)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AuditLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
