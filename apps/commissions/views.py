"""
MERRIGE ERP - Шимтгэлийн Views
Views нимгэн байна: хүсэлтийг уншиж Service Layer руу дамжуулаад,
стандарт success_response буцаана.
"""

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.commissions.repositories import CommissionRepository
from apps.commissions.serializers import CommissionSerializer
from apps.commissions.services import CommissionService
from apps.orders.repositories import OrderRepository
from apps.shared.pagination import StandardResultsPagination
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


class CommissionListView(APIView):
    """GET /api/v1/commissions/ — RBAC жагсаалт (Order/Payment-тэй ижил шатлал)."""

    def get(self, request):
        queryset = CommissionRepository.list_visible_to(request.user)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = CommissionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CommissionDetailView(APIView):
    """GET /api/v1/commissions/{uuid}/ — RBAC-ийн дагуу дэлгэрэнгүй."""

    def get(self, request, commission_uuid):
        commission = CommissionRepository.get_visible_by_uuid(
            request.user, commission_uuid
        )
        if commission is None:
            raise NotFound()
        return success_response(data=CommissionSerializer(commission).data)


class CommissionGenerateView(APIView):
    """POST /api/v1/commissions/orders/{order_uuid}/generate/ — Админ гараар
    дахин бодуулах боломж (ердийн тохиолдолд автоматаар бодогддог,
    энэ нь зөвхөн нөхөн бодоход зориулагдсан)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = OrderRepository.get_by_uuid(order_uuid)
        if order is None:
            raise NotFound()

        commission = CommissionService.generate_for_order(order, actor=request.user)
        return success_response(
            data=CommissionSerializer(commission).data,
            message="Шимтгэл амжилттай бодогдлоо.",
            status_code=status.HTTP_201_CREATED,
        )
