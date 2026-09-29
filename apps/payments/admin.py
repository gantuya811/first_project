"""
MERRIGE ERP - Төлбөрийн Django Admin тохиргоо
"""

from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "amount",
        "status",
        "verified_by",
        "verified_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("order__order_number",)
    readonly_fields = ("uuid", "created_at", "updated_at", "verified_at")
