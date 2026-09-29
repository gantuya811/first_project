"""
MERRIGE ERP - API v1 нэгдсэн чиглүүлэлт
Дараагийн STEP тус бүрт (User Management, Products, Orders, Payments, ...)
холбогдох app-ийн urls.py-г энд include хийж холбоно.
"""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("users/", include("apps.accounts.user_urls")),
    path("products/", include("apps.products.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("orders/", include("apps.orders.urls")),
    path("payments/", include("apps.payments.urls")),
    path("profits/", include("apps.profits.urls")),
    path("commissions/", include("apps.commissions.urls")),
    path("reports/", include("apps.reports.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("audit/", include("apps.audit.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
]
