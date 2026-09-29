"""
MERRIGE ERP - Төлбөрийн Serializers
"""

from decimal import Decimal

from rest_framework import serializers

from apps.payments.models import Payment
from apps.shared.validators import validate_receipt_extension, validate_receipt_size


class PaymentSubmitSerializer(serializers.Serializer):
    receipt_file = serializers.FileField(
        validators=[validate_receipt_extension, validate_receipt_size]
    )
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )


class PaymentRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)


class PaymentListSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    seller_name = serializers.CharField(
        source="order.seller.get_full_name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "uuid",
            "order_number",
            "seller_name",
            "amount",
            "status",
            "status_display",
            "created_at",
        )


class PaymentDetailSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    seller_name = serializers.CharField(
        source="order.seller.get_full_name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "uuid",
            "order_number",
            "seller_name",
            "receipt_file",
            "amount",
            "status",
            "status_display",
            "rejected_reason",
            "verified_by_name",
            "verified_at",
            "created_at",
        )

    def get_verified_by_name(self, obj):
        return obj.verified_by.get_full_name() if obj.verified_by else None
