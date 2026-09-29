"""
MERRIGE ERP - Тайлангийн Serializers
"""

from rest_framework import serializers


class DateRangeQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class SalesReportSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=16, decimal_places=2)


class ProfitReportSerializer(serializers.Serializer):
    """Зөвхөн Админ харна (НУУЦ МЭДЭЭЛЭЛ)."""

    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_revenue = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_net_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_owner_profit = serializers.DecimalField(max_digits=16, decimal_places=2)


class CommissionBySellerSerializer(serializers.Serializer):
    seller__id = serializers.IntegerField()
    seller__first_name = serializers.CharField()
    seller__last_name = serializers.CharField()
    total = serializers.DecimalField(max_digits=16, decimal_places=2)
    count = serializers.IntegerField()


class CommissionReportSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    by_seller = CommissionBySellerSerializer(many=True)


class InventoryReportSerializer(serializers.Serializer):
    total_variants = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    total_retail_value = serializers.DecimalField(max_digits=16, decimal_places=2)
    low_stock_count = serializers.IntegerField()


class SellerReportEntrySerializer(serializers.Serializer):
    seller_name = serializers.CharField()
    order_count = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=16, decimal_places=2)


class TopProductSerializer(serializers.Serializer):
    product_code = serializers.CharField()
    product_name = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=16, decimal_places=2)
