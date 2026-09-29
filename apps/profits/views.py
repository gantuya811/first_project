"""
MERRIGE ERP - Ашгийн Views
Views нимгэн байна: хүсэлтийг уншиж Service Layer руу дамжуулаад,
стандарт success_response буцаана. НУУЦ МЭДЭЭЛЭЛ харуулах эсэхийг
(Full vs Seller view) энд эрхээр нь шийднэ.
"""

from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.products.repositories import ProductRepository
from apps.profits.serializers import (
    ProductCostUpdateSerializer,
    ProductFullProfitSerializer,
    ProductSellerProfitSerializer,
    ProfitDistributionSerializer,
    ProfitDistributionUpdateSerializer,
)
from apps.profits.services import ProfitService
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


def _get_product_or_404(product_uuid):
    product = ProductRepository.get_by_uuid(product_uuid)
    if product is None:
        raise NotFound()
    return product


class ProfitDistributionView(APIView):
    """GET/PUT /api/v1/profits/distribution/ — Ашиг хуваарилалтын хувь
    (зөвхөн Админ, hardcode биш DB-ээс)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def get(self, request):
        config = ProfitService.get_active_config()
        return success_response(data=ProfitDistributionSerializer(config).data)

    def put(self, request):
        serializer = ProfitDistributionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        config = ProfitService.set_distribution(
            owner_pct=serializer.validated_data["owner_percentage"],
            main_seller_pct=serializer.validated_data["main_seller_percentage"],
            contract_seller_pct=serializer.validated_data["contract_seller_percentage"],
            user=request.user,
        )
        return success_response(
            data=ProfitDistributionSerializer(config).data,
            message="Ашиг хуваарилалт амжилттай шинэчлэгдлээ.",
        )


class ProductCostView(APIView):
    """PUT /api/v1/profits/products/{uuid}/cost/ — Барааны өртгийн
    мэдээлэл тохируулах (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def put(self, request, product_uuid):
        product = _get_product_or_404(product_uuid)
        serializer = ProductCostUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ProfitService.set_product_cost(product, serializer.validated_data)
        breakdown = ProfitService.calculate_breakdown(product)
        return success_response(
            data=ProductFullProfitSerializer(breakdown).data,
            message="Барааны өртөг амжилттай хадгалагдлаа.",
        )


class ProductProfitView(APIView):
    """GET /api/v1/profits/products/{uuid}/ — Эрхийн дагуу харагдац.
    Админ: бүрэн задаргаа (Анхны үнэ, Нийт зардал, Эзний ашиг гэх мэт).
    Борлуулагч: зөвхөн RRP, Own Price, Own Profit."""

    def get(self, request, product_uuid):
        product = _get_product_or_404(product_uuid)

        if request.user.is_admin:
            breakdown = ProfitService.calculate_breakdown(product)
            return success_response(data=ProductFullProfitSerializer(breakdown).data)

        view_data = ProfitService.calculate_seller_view(product, request.user.role)
        return success_response(data=ProductSellerProfitSerializer(view_data).data)
