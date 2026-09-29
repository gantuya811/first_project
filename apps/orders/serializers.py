"""
MERRIGE ERP - Захиалгын Serializers
"""

from decimal import Decimal

from rest_framework import serializers

from apps.orders.models import GroupedOrder, Order, OrderItem, OrderStatus, OrderStatusHistory


def _total_amount(order):
    return sum((item.total_price for item in order.items.all()), Decimal("0"))


class OrderItemInputSerializer(serializers.Serializer):
    variant_uuid = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Захиалгад хамгийн багадаа нэг бараа байх ёстой."
            )
        return value


class OrderReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)


class OrderGroupSerializer(serializers.Serializer):
    grouped_order_uuid = serializers.UUIDField()


class OrderItemSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="variant.product.code", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    color_display = serializers.CharField(
        source="variant.get_color_display", read_only=True
    )
    size = serializers.CharField(source="variant.size", read_only=True)
    total_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = (
            "uuid",
            "product_code",
            "product_name",
            "color_display",
            "size",
            "quantity",
            "unit_price",
            "total_price",
        )


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    from_status_display = serializers.SerializerMethodField()
    to_status_display = serializers.CharField(
        source="get_to_status_display", read_only=True
    )
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusHistory
        fields = (
            "uuid",
            "from_status",
            "from_status_display",
            "to_status",
            "to_status_display",
            "reason",
            "changed_by_name",
            "created_at",
        )

    def get_from_status_display(self, obj):
        if not obj.from_status:
            return None
        return OrderStatus(obj.from_status).label

    def get_changed_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class OrderListSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.get_full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "uuid",
            "order_number",
            "seller_name",
            "status",
            "status_display",
            "total_amount",
            "created_at",
        )

    def get_total_amount(self, obj):
        return _total_amount(obj)


class OrderDetailSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.get_full_name", read_only=True)
    seller_phone = serializers.CharField(source="seller.phone_number", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    grouped_order_number = serializers.CharField(
        source="grouped_order.order_number", read_only=True, allow_null=True
    )
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "uuid",
            "order_number",
            "seller_name",
            "seller_phone",
            "status",
            "status_display",
            "note",
            "rejected_reason",
            "cancelled_reason",
            "grouped_order_number",
            "items",
            "total_amount",
            "created_at",
            "updated_at",
        )

    def get_total_amount(self, obj):
        return _total_amount(obj)


class GroupedOrderCreateSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class GroupedOrderSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = GroupedOrder
        fields = ("uuid", "order_number", "note", "order_count", "created_at")

    def get_order_count(self, obj):
        return obj.orders.count()


class GroupedOrderDetailSerializer(GroupedOrderSerializer):
    orders = OrderListSerializer(many=True, read_only=True)

    class Meta(GroupedOrderSerializer.Meta):
        fields = GroupedOrderSerializer.Meta.fields + ("orders",)
