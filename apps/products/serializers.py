"""
MERRIGE ERP - Барааны Serializers
Views нимгэн байх ёстой тул оролтын шалгалтыг энд байрлуулсан.
"""

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.products.models import (
    Product,
    ProductColor,
    ProductImage,
    ProductSize,
    ProductVariant,
)
from apps.shared.validators import validate_image_extension, validate_image_size


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("uuid", "image", "is_primary", "display_order")
        read_only_fields = ("uuid", "display_order")


class ProductImageUploadSerializer(serializers.Serializer):
    """Зураг байршуулах хүсэлтийн оролтыг шалгана. DRF-ийн ImageField нь
    файлыг Pillow-оор бодитоор нээж шалгадаг тул (.txt зэрэг) зураг биш
    файлыг энд аль хэдийн барина; нэмээд өргөтгөл/хэмжээг хязгаарлана."""

    image = serializers.ImageField(
        validators=[validate_image_extension, validate_image_size]
    )
    is_primary = serializers.BooleanField(required=False, default=False)


class ProductVariantSerializer(serializers.ModelSerializer):
    color_display = serializers.CharField(source="get_color_display", read_only=True)

    class Meta:
        model = ProductVariant
        fields = ("uuid", "color", "color_display", "size")
        read_only_fields = ("uuid",)


class ProductVariantCreateSerializer(serializers.Serializer):
    color = serializers.ChoiceField(choices=ProductColor.choices)
    size = serializers.ChoiceField(choices=ProductSize.choices)


class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("uuid", "code", "name", "price", "status", "primary_image")

    def get_primary_image(self, obj):
        images = list(obj.images.all())
        primary = next((img for img in images if img.is_primary), None) or (
            images[0] if images else None
        )
        if primary is None:
            return None
        request = self.context.get("request")
        url = primary.image.url
        return request.build_absolute_uri(url) if request else url


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "uuid",
            "code",
            "name",
            "description",
            "material",
            "care_instructions",
            "size_chart_image",
            "price",
            "status",
            "images",
            "variants",
            "created_at",
            "updated_at",
        )


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    # DRF нь Product.Meta.constraints дэх UniqueConstraint-г автоматаар
    # илрүүлж, өөрийн (Англи эхтэй орчуулгаас хамааралтай) UniqueValidator-ыг
    # нэмдэг тул, 100% Монгол мессежийг баталгаатай харуулахын тулд энд
    # тодорхой validators=[...] өгч, автомат нэмэлтийг дарж бичив.
    code = serializers.CharField(
        max_length=50,
        validators=[
            UniqueValidator(
                queryset=Product.objects.all(),
                message="Энэ барааны код бүртгэлтэй байна.",
            )
        ],
    )

    class Meta:
        model = Product
        fields = (
            "code",
            "name",
            "description",
            "material",
            "care_instructions",
            "size_chart_image",
            "price",
            "status",
        )

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Үнэ 0-ээс их байх ёстой.")
        return value


class ProductImportFileSerializer(serializers.Serializer):
    """Excel Import хүсэлтийн оролт."""

    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith((".xlsx", ".xlsm")):
            raise serializers.ValidationError(
                "Зөвхөн .xlsx Excel файл оруулна уу."
            )
        return value


class ProductImportRowResultSerializer(serializers.Serializer):
    row_number = serializers.IntegerField()
    code = serializers.CharField(allow_null=True)
    success = serializers.BooleanField()
    errors = serializers.JSONField(allow_null=True)
