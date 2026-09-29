"""
MERRIGE ERP - Мэдэгдлийн Serializers
"""

from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )

    class Meta:
        model = Notification
        fields = (
            "uuid",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "reference",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields
