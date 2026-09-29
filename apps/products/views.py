"""
MERRIGE ERP - Барааны Views
Views нимгэн байна: хүсэлтийг уншиж Service Layer руу дамжуулаад,
стандарт success_response буцаана. Бизнес логик энд байхгүй.
"""

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.products.excel import (
    EXPORT_HEADERS,
    build_products_export_rows,
    import_products_from_excel,
)
from apps.products.repositories import ProductRepository
from apps.products.serializers import (
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductImageUploadSerializer,
    ProductImportFileSerializer,
    ProductImportRowResultSerializer,
    ProductListSerializer,
    ProductVariantCreateSerializer,
    ProductVariantSerializer,
)
from apps.products.services import ProductService
from apps.shared.exporters import export_rows_to_excel
from apps.shared.pagination import StandardResultsPagination
from apps.shared.responses import success_response

ADMIN_ONLY_PERMISSIONS = [IsAuthenticated, IsPasswordChanged, IsAdminRole]


def _get_product_or_404(product_uuid):
    product = ProductRepository.get_by_uuid(product_uuid)
    if product is None:
        raise NotFound()
    return product


class AdminWriteMixin:
    """GET нь бүх эрхт хэрэглэгчид (анхдагч эрхээр), бичих үйлдэл
    (POST/PATCH/DELETE) зөвхөн Админ-д нээлттэй байх нийтлэг permission."""

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return super().get_permissions()
        return [permission() for permission in ADMIN_ONLY_PERMISSIONS]


class ProductListCreateView(AdminWriteMixin, APIView):
    """GET /api/v1/products/ — жагсаалт (бүх эрхт хэрэглэгч)
    POST /api/v1/products/ — шинэ бараа үүсгэх (зөвхөн Админ)."""

    def get(self, request):
        queryset = ProductRepository.list_all()
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ProductListSerializer(
            page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProductCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = ProductService.create_product(serializer.validated_data)
        return success_response(
            data=ProductDetailSerializer(product, context={"request": request}).data,
            message="Бараа амжилттай үүслээ.",
            status_code=status.HTTP_201_CREATED,
        )


class ProductDetailView(AdminWriteMixin, APIView):
    """GET/PATCH/DELETE /api/v1/products/{uuid}/"""

    def get(self, request, product_uuid):
        product = _get_product_or_404(product_uuid)
        return success_response(
            data=ProductDetailSerializer(product, context={"request": request}).data
        )

    def patch(self, request, product_uuid):
        product = _get_product_or_404(product_uuid)
        serializer = ProductCreateUpdateSerializer(
            product, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        product = ProductService.update_product(product, serializer.validated_data)
        return success_response(
            data=ProductDetailSerializer(product, context={"request": request}).data,
            message="Бараа амжилттай шинэчлэгдлээ.",
        )

    def delete(self, request, product_uuid):
        product = _get_product_or_404(product_uuid)
        ProductService.delete_product(product)
        return success_response(message="Бараа устгагдлаа.")


class ProductImageUploadView(APIView):
    """POST /api/v1/products/{uuid}/images/ — Зураг нэмэх (зөвхөн Админ,
    нэг бараанд хамгийн ихдээ 5 зураг)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, product_uuid):
        product = _get_product_or_404(product_uuid)
        serializer = ProductImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = ProductService.add_image(
            product,
            serializer.validated_data["image"],
            is_primary=serializer.validated_data["is_primary"],
        )
        return success_response(
            data=ProductImageSerializer(image, context={"request": request}).data,
            message="Зураг амжилттай нэмэгдлээ.",
            status_code=status.HTTP_201_CREATED,
        )


class ProductImageDeleteView(APIView):
    """DELETE /api/v1/products/{uuid}/images/{image_uuid}/ — зөвхөн Админ."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def delete(self, request, product_uuid, image_uuid):
        product = _get_product_or_404(product_uuid)
        image = product.images.filter(uuid=image_uuid).first()
        if image is None:
            raise NotFound()
        ProductService.delete_image(image)
        return success_response(message="Зураг устгагдлаа.")


class ProductVariantCreateView(APIView):
    """POST /api/v1/products/{uuid}/variants/ — Өнгө+Размер хослол нэмэх
    (зөвхөн Админ)."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def post(self, request, product_uuid):
        product = _get_product_or_404(product_uuid)
        serializer = ProductVariantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant = ProductService.add_variant(
            product,
            color=serializer.validated_data["color"],
            size=serializer.validated_data["size"],
        )
        return success_response(
            data=ProductVariantSerializer(variant).data,
            message="Хувилбар амжилттай нэмэгдлээ.",
            status_code=status.HTTP_201_CREATED,
        )


class ProductVariantDeleteView(APIView):
    """DELETE /api/v1/products/{uuid}/variants/{variant_uuid}/ — зөвхөн Админ."""

    permission_classes = ADMIN_ONLY_PERMISSIONS

    def delete(self, request, product_uuid, variant_uuid):
        product = _get_product_or_404(product_uuid)
        variant = product.variants.filter(uuid=variant_uuid).first()
        if variant is None:
            raise NotFound()
        ProductService.delete_variant(variant)
        return success_response(message="Хувилбар устгагдлаа.")


class ProductImportView(APIView):
    """POST /api/v1/products/import/ — Excel файлаас барааг бөөнөөр
    үүсгэнэ (зөвхөн Админ). Мөр бүрийг тусад нь шалгаж, зөв мөрийг
    үүсгэнэ; буруу мөр бусдад нөлөөлөхгүй, алдааны дэлгэрэнгүйтэй буцна."""

    permission_classes = ADMIN_ONLY_PERMISSIONS
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ProductImportFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = import_products_from_excel(serializer.validated_data["file"])
        success_count = sum(1 for row in results if row["success"])
        failure_count = len(results) - success_count

        return success_response(
            data={
                "total_rows": len(results),
                "success_count": success_count,
                "failure_count": failure_count,
                "rows": ProductImportRowResultSerializer(results, many=True).data,
            },
            message=f"{success_count}/{len(results)} мөр амжилттай импортлогдлоо.",
        )


class ProductExportView(APIView):
    """GET /api/v1/products/export/ — Барааны каталогийг Excel файлаар
    гаргана (бүх эрхт хэрэглэгч, жагсаалт харах эрхтэй хүн бүр)."""

    def get(self, request):
        products = ProductRepository.list_all()
        rows = build_products_export_rows(products)
        return export_rows_to_excel(
            "baraanii_katalog.xlsx", EXPORT_HEADERS, rows, "Бараа бүтээгдэхүүн"
        )
