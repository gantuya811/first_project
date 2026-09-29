"""
MERRIGE ERP - Агуулахын Serializers
"""

from rest_framework import serializers

from apps.inventory.models import InventoryMovement, Stock


class StockSerializer(serializers.ModelSerializer):
    variant_uuid = serializers.UUIDField(source="variant.uuid", read_only=True)
    product_code = serializers.CharField(source="variant.product.code", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    color = serializers.CharField(source="variant.color", read_only=True)
    color_display = serializers.CharField(
        source="variant.get_color_display", read_only=True
    )
    size = serializers.CharField(source="variant.size", read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Stock
        fields = (
            "variant_uuid",
            "product_code",
            "product_name",
            "color",
            "color_display",
            "size",
            "quantity",
            "reserved_quantity",
            "available_quantity",
        )


class InventoryMovementSerializer(serializers.ModelSerializer):
    movement_type_display = serializers.CharField(
        source="get_movement_type_display", read_only=True
    )
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = InventoryMovement
        fields = (
            "uuid",
            "movement_type",
            "movement_type_display",
            "quantity_change",
            "quantity_before",
            "quantity_after",
            "reserved_before",
            "reserved_after",
            "reason",
            "reference",
            "created_by_name",
            "created_at",
        )

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class StockQuantitySerializer(serializers.Serializer):
    """Stock In / Stock Out / Reservation / Release-д зориулсан оролт."""

    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=100)


class StockAdjustSerializer(serializers.Serializer):
    """Тохируулга: шинэ (үнэмлэхүй) үлдэгдлийг зааж, шалтгаан заавал бичнэ."""

    quantity = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=255)
