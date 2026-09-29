"""
MERRIGE ERP - Мэдэгдлийн Django Admin тохиргоо
"""

from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "title", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("recipient__phone_number", "title", "reference")
    readonly_fields = ("uuid", "created_at", "updated_at")
