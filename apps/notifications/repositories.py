"""
MERRIGE ERP - Мэдэгдлийн Repository
Repository Pattern: Database Logic зөвхөн энд байрлана.
"""

from apps.notifications.models import Notification


class NotificationRepository:
    @staticmethod
    def get_by_uuid_for_user(user, notification_uuid):
        return Notification.objects.filter(recipient=user, uuid=notification_uuid).first()

    @staticmethod
    def list_for_user(user, is_read=None):
        queryset = Notification.objects.filter(recipient=user)
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        return queryset

    @staticmethod
    def unread_count(user):
        return Notification.objects.filter(recipient=user, is_read=False).count()
