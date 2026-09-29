"""
MERRIGE ERP - Агуулахын Views
Views нимгэн байна: хүсэлтийг уншиж Service Layer руу дамжуулаад,
стандарт success_response буцаана. Бизнес логик энд байхгүй.
"""

from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.inventory.repositories import InventoryRepository
from apps.inventory.serializers import (
    InventoryMovementSerializer,
    StockAdjustSerializer,
    StockQuantitySerializer,
    StockSerializer,
)
from apps.inventory.services import InventoryService
from apps.shared.pagination import StandardResultsPagination
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


def _get_stock_or_404(variant_uuid):
    stock = InventoryRepository.get_stock_by_variant_uuid(variant_uuid)
    if stock is None:
        raise NotFound()
    return stock


class StockListView(APIView):
    """GET /api/v1/inventory/stock/ — Бүх хувилбарын үлдэгдэл (бүх эрхт хэрэглэгч)."""

    def get(self, request):
        queryset = InventoryRepository.list_stock()
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = StockSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class StockDetailView(APIView):
    """GET /api/v1/inventory/stock/{variant_uuid}/ — Нэг хувилбарын үлдэгдэл."""

    def get(self, request, variant_uuid):
        stock = _get_stock_or_404(variant_uuid)
        return success_response(data=StockSerializer(stock).data)


class LowStockView(APIView):
    """GET /api/v1/inventory/low-stock/?threshold=5 — Нөөц багатай бараа
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        try:
            threshold = int(request.query_params.get("threshold", 5))
        except (TypeError, ValueError):
            threshold = 5

        queryset = InventoryRepository.list_low_stock(threshold=threshold)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = StockSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class StockInView(APIView):
    """POST /api/v1/inventory/stock/{variant_uuid}/stock-in/ — Орлого
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, variant_uuid):
        stock = _get_stock_or_404(variant_uuid)
        serializer = StockQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = InventoryService.stock_in(
            stock.variant,
            quantity=serializer.validated_data["quantity"],
            user=request.user,
            reason=serializer.validated_data.get("reason", ""),
            reference=serializer.validated_data.get("reference", ""),
        )
        return success_response(
            data=StockSerializer(updated).data, message="Орлого амжилттай бүртгэгдлээ."
        )


class StockOutView(APIView):
    """POST /api/v1/inventory/stock/{variant_uuid}/stock-out/ — Зарлага
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, variant_uuid):
        stock = _get_stock_or_404(variant_uuid)
        serializer = StockQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = InventoryService.stock_out(
            stock.variant,
            quantity=serializer.validated_data["quantity"],
            user=request.user,
            reason=serializer.validated_data.get("reason", ""),
            reference=serializer.validated_data.get("reference", ""),
        )
        return success_response(
            data=StockSerializer(updated).data, message="Зарлага амжилттай бүртгэгдлээ."
        )


class StockReserveView(APIView):
    """POST /api/v1/inventory/stock/{variant_uuid}/reserve/ — Нөөцлөх
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, variant_uuid):
        stock = _get_stock_or_404(variant_uuid)
        serializer = StockQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = InventoryService.reserve(
            stock.variant,
            quantity=serializer.validated_data["quantity"],
            user=request.user,
            reference=serializer.validated_data.get("reference", ""),
        )
        return success_response(
            data=StockSerializer(updated).data, message="Нөөцлөлт амжилттай хийгдлээ."
        )


class StockReleaseView(APIView):
    """POST /api/v1/inventory/stock/{variant_uuid}/release/ — Нөөцлөлт
    цуцлах (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, variant_uuid):
        stock = _get_stock_or_404(variant_uuid)
        serializer = StockQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = InventoryService.release_reservation(
            stock.variant,
            quantity=serializer.validated_data["quantity"],
            user=request.user,
            reference=serializer.validated_data.get("reference", ""),
        )
        return success_response(
            data=StockSerializer(updated).data,
            message="Нөөцлөлт амжилттай цуцлагдлаа.",
        )


class StockAdjustView(APIView):
    """POST /api/v1/inventory/stock/{variant_uuid}/adjust/ — Тохируулга
    (зөвхөн Админ, шалтгаан заавал)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, variant_uuid):
        stock = _get_stock_or_404(variant_uuid)
        serializer = StockAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = InventoryService.adjust(
            stock.variant,
            new_quantity=serializer.validated_data["quantity"],
            user=request.user,
            reason=serializer.validated_data["reason"],
        )
        return success_response(
            data=StockSerializer(updated).data,
            message="Үлдэгдэл амжилттай тохируулагдлаа.",
        )


class StockMovementListView(APIView):
    """GET /api/v1/inventory/stock/{variant_uuid}/movements/ — Хувилбарын
    хөдөлгөөний түүх (Inventory History, зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request, variant_uuid):
        stock = _get_stock_or_404(variant_uuid)
        queryset = InventoryRepository.list_movements(variant=stock.variant)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = InventoryMovementSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
