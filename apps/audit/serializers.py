"""
MERRIGE ERP - Аудитын Serializers
"""

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            "uuid",
            "user_name",
            "category",
            "category_display",
            "action",
            "ip_address",
            "object_reference",
            "old_value",
            "new_value",
            "created_at",
        )
        read_only_fields = fields

    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else "Систем"
