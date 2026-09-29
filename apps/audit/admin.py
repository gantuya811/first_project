"""
MERRIGE ERP - Аудитын Django Admin тохиргоо
AuditLog нь өөрчлөгдөшгүй (immutable) тул Admin-аас нэмэх, засах, устгах
боломжгүй (зөвхөн харах).
"""

from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("category", "action", "user", "ip_address", "object_reference", "created_at")
    list_filter = ("category",)
    search_fields = ("action", "object_reference", "user__phone_number")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
