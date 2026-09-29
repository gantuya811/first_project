"""
MERRIGE ERP - Мэдэгдлийн API URL-ууд
"""

from django.urls import path

from apps.notifications.views import (
    MarkAllReadView,
    NotificationDeleteView,
    NotificationListView,
    NotificationReadView,
    UnreadCountView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("unread-count/", UnreadCountView.as_view(), name="unread-count"),
    path("mark-all-read/", MarkAllReadView.as_view(), name="mark-all-read"),
    path(
        "<uuid:notification_uuid>/read/",
        NotificationReadView.as_view(),
        name="read",
    ),
    path(
        "<uuid:notification_uuid>/",
        NotificationDeleteView.as_view(),
        name="delete",
    ),
]
