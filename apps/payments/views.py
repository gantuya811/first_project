"""
MERRIGE ERP - Төлбөрийн Views
Views нимгэн байна: хүсэлтийг уншиж Service Layer руу дамжуулаад,
стандарт success_response буцаана. Бизнес логик энд байхгүй.
"""

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.orders.repositories import OrderRepository
from apps.payments.repositories import PaymentRepository
from apps.payments.serializers import (
    PaymentDetailSerializer,
    PaymentListSerializer,
    PaymentRejectSerializer,
    PaymentSubmitSerializer,
)
from apps.payments.services import PaymentService
from apps.shared.pagination import StandardResultsPagination
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


def _get_visible_order_or_404(user, order_uuid):
    order = OrderRepository.get_visible_by_uuid(user, order_uuid)
    if order is None:
        raise NotFound()
    return order


def _get_visible_payment_or_404(user, payment_uuid):
    payment = PaymentRepository.get_visible_by_uuid(user, payment_uuid)
    if payment is None:
        raise NotFound()
    return payment


class PaymentSubmitView(APIView):
    """POST /api/v1/payments/orders/{order_uuid}/submit/ — Борлуулагч
    төлбөрийн баримт илгээнэ."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        if order.seller_id != request.user.id:
            raise PermissionDenied(
                "Зөвхөн өөрийн захиалгад төлбөрийн баримт оруулах боломжтой."
            )

        serializer = PaymentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.submit_payment(
            order=order,
            seller=request.user,
            receipt_file=serializer.validated_data["receipt_file"],
            amount=serializer.validated_data["amount"],
        )
        return success_response(
            data=PaymentDetailSerializer(payment).data,
            message="Төлбөрийн баримт амжилттай илгээгдлээ.",
            status_code=status.HTTP_201_CREATED,
        )


class PaymentOrderListView(APIView):
    """GET /api/v1/payments/orders/{order_uuid}/ — Захиалгын төлбөрийн түүх."""

    def get(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        queryset = PaymentRepository.list_for_order(order)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PaymentListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PendingPaymentListView(APIView):
    """GET /api/v1/payments/pending/ — Шалгах шаардлагатай төлбөрүүд
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        queryset = PaymentRepository.list_pending()
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PaymentListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PaymentDetailView(APIView):
    """GET /api/v1/payments/{uuid}/ — RBAC-ийн дагуу дэлгэрэнгүй."""

    def get(self, request, payment_uuid):
        payment = _get_visible_payment_or_404(request.user, payment_uuid)
        return success_response(data=PaymentDetailSerializer(payment).data)


class PaymentConfirmView(APIView):
    """POST /api/v1/payments/{uuid}/confirm/ — Админ баталгаажуулна."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, payment_uuid):
        payment = _get_visible_payment_or_404(request.user, payment_uuid)
        payment = PaymentService.confirm(payment, request.user)
        return success_response(
            data=PaymentDetailSerializer(payment).data, message="Төлбөр баталгаажлаа."
        )


class PaymentRejectView(APIView):
    """POST /api/v1/payments/{uuid}/reject/ — Админ татгалзана."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, payment_uuid):
        payment = _get_visible_payment_or_404(request.user, payment_uuid)
        serializer = PaymentRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = PaymentService.reject(
            payment, request.user, serializer.validated_data["reason"]
        )
        return success_response(
            data=PaymentDetailSerializer(payment).data, message="Төлбөр татгалзагдлаа."
        )
