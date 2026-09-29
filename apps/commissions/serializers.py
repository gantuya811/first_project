"""
MERRIGE ERP - Шимтгэлийн Serializers
"""

from rest_framework import serializers

from apps.commissions.models import Commission


class CommissionSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    seller_name = serializers.CharField(source="seller.get_full_name", read_only=True)

    class Meta:
        model = Commission
        fields = ("uuid", "order_number", "seller_name", "amount", "created_at")
