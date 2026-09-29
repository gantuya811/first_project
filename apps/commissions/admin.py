"""
MERRIGE ERP - Шимтгэлийн Django Admin тохиргоо
Commission нь өөрчлөгдөшгүй (immutable) тул Admin-аас нэмэх, засах,
устгах боломжгүй (зөвхөн харах).
"""

from django.contrib import admin

from apps.commissions.models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ("order", "seller", "amount", "created_at")
    search_fields = (
        "order__order_number",
        "seller__phone_number",
        "seller__first_name",
        "seller__last_name",
    )
    readonly_fields = [f.name for f in Commission._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
