"""
MERRIGE ERP - Ашгийн Serializers
ProductFullProfitSerializer (Админ-д зориулсан бүрэн задаргаа) болон
ProductSellerProfitSerializer (Борлуулагчид зориулсан хязгаарлагдмал
харагдац)-ийг ялгаатай байлгаж, НУУЦ МЭДЭЭЛЭЛ алдамгүй хамгаалагдана.
"""

from decimal import Decimal

from rest_framework import serializers

from apps.profits.models import ProductCost, ProfitDistributionConfig


class ProfitDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfitDistributionConfig
        fields = (
            "uuid",
            "owner_percentage",
            "main_seller_percentage",
            "contract_seller_percentage",
            "created_at",
        )


class ProfitDistributionUpdateSerializer(serializers.Serializer):
    owner_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    main_seller_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    contract_seller_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )


class ProductCostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCost
        fields = (
            "original_price",
            "shipping_cost",
            "packaging_cost",
            "transfer_fee",
            "risk_reserve",
            "marketing_cost",
            "supplier_info",
        )


class ProductFullProfitSerializer(serializers.Serializer):
    """Зөвхөн Админ харна: Анхны үнэ, Нийт зардал, Эзний ашиг гэх мэт."""

    original_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    packaging_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    transfer_fee = serializers.DecimalField(max_digits=12, decimal_places=2)
    risk_reserve = serializers.DecimalField(max_digits=12, decimal_places=2)
    marketing_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    supplier_info = serializers.CharField()
    rrp = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    owner_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    main_seller_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    contract_seller_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    main_seller_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    contract_seller_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class ProductSellerProfitSerializer(serializers.Serializer):
    """Борлуулагчид зориулсан хязгаарлагдмал харагдац: RRP, Own Price, Own Profit."""

    rrp = serializers.DecimalField(max_digits=12, decimal_places=2)
    own_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    own_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
