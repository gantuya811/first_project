"""
MERRIGE ERP - Төлбөрийн API URL-ууд
"""

from django.urls import path

from apps.payments.views import (
    PaymentConfirmView,
    PaymentDetailView,
    PaymentOrderListView,
    PaymentRejectView,
    PaymentSubmitView,
    PendingPaymentListView,
)

app_name = "payments"

urlpatterns = [
    path("pending/", PendingPaymentListView.as_view(), name="pending"),
    path("orders/<uuid:order_uuid>/", PaymentOrderListView.as_view(), name="order-list"),
    path(
        "orders/<uuid:order_uuid>/submit/",
        PaymentSubmitView.as_view(),
        name="submit",
    ),
    path("<uuid:payment_uuid>/", PaymentDetailView.as_view(), name="detail"),
    path("<uuid:payment_uuid>/confirm/", PaymentConfirmView.as_view(), name="confirm"),
    path("<uuid:payment_uuid>/reject/", PaymentRejectView.as_view(), name="reject"),
]
