"""
MERRIGE ERP - Мэдэгдлийн Views
Views нимгэн байна: хүсэлтийг уншиж Repository/Service Layer руу
дамжуулаад, стандарт success_response буцаана. Хэрэглэгч зөвхөн
ӨӨРИЙН мэдэгдлийг л удирдана (RBAC шатлал энд хамаарахгүй).
"""

from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.notifications.repositories import NotificationRepository
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import NotificationService
from apps.shared.pagination import StandardResultsPagination
from apps.shared.responses import success_response


def _get_own_notification_or_404(user, notification_uuid):
    notification = NotificationRepository.get_by_uuid_for_user(user, notification_uuid)
    if notification is None:
        raise NotFound()
    return notification


class NotificationListView(APIView):
    """GET /api/v1/notifications/?is_read=true|false — Өөрийн мэдэгдлийн жагсаалт."""

    def get(self, request):
        is_read_param = request.query_params.get("is_read")
        is_read = None
        if is_read_param is not None:
            is_read = is_read_param.lower() in ("true", "1")

        queryset = NotificationRepository.list_for_user(request.user, is_read)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UnreadCountView(APIView):
    """GET /api/v1/notifications/unread-count/ — Уншаагүй мэдэгдлийн тоо."""

    def get(self, request):
        count = NotificationRepository.unread_count(request.user)
        return success_response(data={"unread_count": count})


class NotificationReadView(APIView):
    """POST /api/v1/notifications/{uuid}/read/ — Уншсан гэж тэмдэглэх."""

    def post(self, request, notification_uuid):
        notification = _get_own_notification_or_404(request.user, notification_uuid)
        notification = NotificationService.mark_as_read(notification)
        return success_response(
            data=NotificationSerializer(notification).data,
            message="Мэдэгдэл уншсан гэж тэмдэглэгдлээ.",
        )


class MarkAllReadView(APIView):
    """POST /api/v1/notifications/mark-all-read/ — Бүгдийг уншсан гэж тэмдэглэх."""

    def post(self, request):
        NotificationService.mark_all_as_read(request.user)
        return success_response(message="Бүх мэдэгдэл уншсан гэж тэмдэглэгдлээ.")


class NotificationDeleteView(APIView):
    """DELETE /api/v1/notifications/{uuid}/ — Мэдэгдлийг арилгах (Soft Delete)."""

    def delete(self, request, notification_uuid):
        notification = _get_own_notification_or_404(request.user, notification_uuid)
        notification.delete()
        return success_response(message="Мэдэгдэл устгагдлаа.")
