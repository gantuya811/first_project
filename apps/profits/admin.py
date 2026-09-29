"""
MERRIGE ERP - Ашгийн Django Admin тохиргоо
"""

from django.contrib import admin

from apps.profits.models import ProductCost, ProfitDistributionConfig


@admin.register(ProfitDistributionConfig)
class ProfitDistributionConfigAdmin(admin.ModelAdmin):
    list_display = (
        "owner_percentage",
        "main_seller_percentage",
        "contract_seller_percentage",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(ProductCost)
class ProductCostAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "original_price",
        "total_cost_display",
        "net_profit_display",
    )
    search_fields = ("product__code", "product__name")
    readonly_fields = ("uuid", "created_at", "updated_at")

    @admin.display(description="Нийт зардал")
    def total_cost_display(self, obj):
        return obj.total_cost

    @admin.display(description="Цэвэр ашиг")
    def net_profit_display(self, obj):
        return obj.net_profit
