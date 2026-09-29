"""
MERRIGE ERP - Агуулахын Django Admin тохиргоо
InventoryMovement нь өөрчлөгдөшгүй (immutable) тул Admin-аас ч нэмэх,
засах, устгах боломжгүй болгосон (зөвхөн харах).
"""

from django.contrib import admin

from apps.inventory.models import InventoryMovement, Stock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "quantity",
        "reserved_quantity",
        "available_quantity_display",
    )
    search_fields = ("variant__product__code", "variant__product__name")
    readonly_fields = ("uuid", "created_at", "updated_at")

    @admin.display(description="Боломжит үлдэгдэл")
    def available_quantity_display(self, obj):
        return obj.available_quantity


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "movement_type",
        "quantity_change",
        "quantity_after",
        "created_by",
        "created_at",
    )
    list_filter = ("movement_type",)
    search_fields = ("variant__product__code", "reference")
    readonly_fields = [f.name for f in InventoryMovement._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
