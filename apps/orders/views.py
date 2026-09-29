"""
MERRIGE ERP - Захиалгын Views
Views нимгэн байна: хүсэлтийг уншиж Service Layer руу дамжуулаад,
стандарт success_response буцаана. Бизнес логик (төлөв шилжилт,
агуулахтай интеграц) энд байхгүй, бүгд Service Layer-т байна.
"""

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.orders.repositories import GroupedOrderRepository, OrderRepository
from apps.orders.serializers import (
    GroupedOrderCreateSerializer,
    GroupedOrderDetailSerializer,
    GroupedOrderSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderGroupSerializer,
    OrderListSerializer,
    OrderReasonSerializer,
    OrderStatusHistorySerializer,
)
from apps.orders.services import GroupedOrderService, OrderService
from apps.shared.exporters import export_rows_to_excel
from apps.shared.pagination import StandardResultsPagination
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


def _get_visible_order_or_404(user, order_uuid):
    order = OrderRepository.get_visible_by_uuid(user, order_uuid)
    if order is None:
        raise NotFound()
    return order


class OrderListCreateView(APIView):
    """GET /api/v1/orders/ — RBAC жагсаалт.
    POST /api/v1/orders/ — Борлуулагч захиалгын хүсэлт илгээнэ."""

    def get(self, request):
        queryset = OrderRepository.list_visible_to(request.user)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = OrderListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if not (request.user.is_main_seller or request.user.is_contract_seller):
            raise PermissionDenied("Зөвхөн борлуулагч захиалга үүсгэх боломжтой.")

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = OrderService.create_order(
            seller=request.user,
            items_data=serializer.validated_data["items"],
            note=serializer.validated_data.get("note", ""),
        )
        return success_response(
            data=OrderDetailSerializer(order).data,
            message="Захиалга амжилттай илгээгдлээ.",
            status_code=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):
    """GET /api/v1/orders/{uuid}/ — RBAC-ийн дагуу дэлгэрэнгүй."""

    def get(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        return success_response(data=OrderDetailSerializer(order).data)


class OrderHistoryView(APIView):
    """GET /api/v1/orders/{uuid}/history/ — Төлөвийн түүх."""

    def get(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        queryset = order.status_history.all()
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = OrderStatusHistorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class OrderReviewView(APIView):
    """POST /api/v1/orders/{uuid}/review/ — Админ хянаж эхлэх (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        order = OrderService.start_review(order, request.user)
        return success_response(
            data=OrderDetailSerializer(order).data, message="Захиалга хянагдаж эхэллээ."
        )


class OrderApproveView(APIView):
    """POST /api/v1/orders/{uuid}/approve/ — Админ батлах / 'Боломжтой'
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        order = OrderService.approve(order, request.user)
        return success_response(
            data=OrderDetailSerializer(order).data, message="Захиалга батлагдлаа."
        )


class OrderRejectView(APIView):
    """POST /api/v1/orders/{uuid}/reject/ — Админ татгалзах / 'Боломжгүй'
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        serializer = OrderReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.reject(
            order, request.user, serializer.validated_data["reason"]
        )
        return success_response(
            data=OrderDetailSerializer(order).data, message="Захиалга татгалзагдлаа."
        )


class OrderCancelView(APIView):
    """POST /api/v1/orders/{uuid}/cancel/ — Борлуулагч (зөвхөн өөрийн) эсвэл
    Админ захиалгыг цуцлана."""

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        if not (request.user.is_admin or order.seller_id == request.user.id):
            raise PermissionDenied("Танд энэ захиалгыг цуцлах эрх байхгүй байна.")

        serializer = OrderReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.cancel(
            order, request.user, serializer.validated_data["reason"]
        )
        return success_response(
            data=OrderDetailSerializer(order).data, message="Захиалга цуцлагдлаа."
        )


class OrderGroupView(APIView):
    """POST /api/v1/orders/{uuid}/group/ — Нэгдсэн захиалганд оруулах
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        serializer = OrderGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        grouped_order = GroupedOrderRepository.get_by_uuid(
            serializer.validated_data["grouped_order_uuid"]
        )
        if grouped_order is None:
            raise NotFound()

        order = OrderService.group(order, grouped_order, request.user)
        return success_response(
            data=OrderDetailSerializer(order).data,
            message="Захиалга нэгдсэн захиалганд орлоо.",
        )


class OrderMarkArrivedView(APIView):
    """POST /api/v1/orders/{uuid}/mark-arrived/ — Бараа ирлээ (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        order = OrderService.mark_arrived(order, request.user)
        return success_response(
            data=OrderDetailSerializer(order).data, message="Бараа ирлээ."
        )


class OrderShipView(APIView):
    """POST /api/v1/orders/{uuid}/ship/ — Хүргэлтэд гаргах (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        order = OrderService.ship(order, request.user)
        return success_response(
            data=OrderDetailSerializer(order).data, message="Хүргэлт эхэллээ."
        )


class OrderCompleteView(APIView):
    """POST /api/v1/orders/{uuid}/complete/ — Захиалга дуусгах (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, order_uuid):
        order = _get_visible_order_or_404(request.user, order_uuid)
        order = OrderService.complete(order, request.user)
        return success_response(
            data=OrderDetailSerializer(order).data, message="Захиалга дууслаа."
        )


class GroupedOrderListCreateView(APIView):
    """GET/POST /api/v1/orders/grouped/ — Нэгдсэн захиалгын жагсаалт/үүсгэх
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        queryset = GroupedOrderRepository.list_all()
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = GroupedOrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = GroupedOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grouped_order = GroupedOrderService.create(
            user=request.user, note=serializer.validated_data.get("note", "")
        )
        return success_response(
            data=GroupedOrderSerializer(grouped_order).data,
            message="Нэгдсэн захиалга амжилттай үүслээ.",
            status_code=status.HTTP_201_CREATED,
        )


class GroupedOrderDetailView(APIView):
    """GET /api/v1/orders/grouped/{uuid}/ — Нэгдсэн захиалгын дэлгэрэнгүй
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request, grouped_order_uuid):
        grouped_order = GroupedOrderRepository.get_by_uuid(grouped_order_uuid)
        if grouped_order is None:
            raise NotFound()
        return success_response(data=GroupedOrderDetailSerializer(grouped_order).data)


class GroupedOrderExportView(APIView):
    """GET /api/v1/orders/grouped/{uuid}/export/ — Нэгдсэн захиалгад орсон
    бүх захиалга/мөрийг Excel файлаар гаргана (нийлүүлэгч рүү илгээхэд
    зориулагдсан, зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request, grouped_order_uuid):
        grouped_order = GroupedOrderRepository.get_by_uuid(grouped_order_uuid)
        if grouped_order is None:
            raise NotFound()

        headers = [
            "Захиалгын дугаар",
            "Захиалагч",
            "Утасны дугаар",
            "Барааны код",
            "Барааны нэр",
            "Өнгө",
            "Размер",
            "Тоо ширхэг",
            "Нэгжийн үнэ",
            "Нийт үнэ",
            "Төлөв",
        ]
        rows = []
        orders = grouped_order.orders.select_related("seller").prefetch_related(
            "items__variant__product"
        )
        for order in orders:
            for item in order.items.all():
                rows.append(
                    [
                        order.order_number,
                        order.seller.get_full_name(),
                        order.seller.phone_number,
                        item.variant.product.code,
                        item.variant.product.name,
                        item.variant.get_color_display(),
                        item.variant.size,
                        item.quantity,
                        float(item.unit_price),
                        float(item.total_price),
                        order.get_status_display(),
                    ]
                )

        return export_rows_to_excel(
            f"negdsen_zahialga_{grouped_order.order_number}.xlsx",
            headers,
            rows,
            f"Нэгдсэн захиалга {grouped_order.order_number}",
        )
