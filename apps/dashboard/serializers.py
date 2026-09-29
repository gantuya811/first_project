"""
MERRIGE ERP - Dashboard Serializers
"""

from rest_framework import serializers


class KPISerializer(serializers.Serializer):
    today_orders = serializers.IntegerField()
    today_sales = serializers.DecimalField(max_digits=16, decimal_places=2)
    today_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
    month_sales = serializers.DecimalField(max_digits=16, decimal_places=2)
    month_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
    owner_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
    main_seller_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
    contract_seller_profit = serializers.DecimalField(max_digits=16, decimal_places=2)
    pending_payments = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()


class TrendPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    total = serializers.DecimalField(max_digits=16, decimal_places=2)


class ProvinceReportEntrySerializer(serializers.Serializer):
    province = serializers.CharField()
    order_count = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=16, decimal_places=2)
