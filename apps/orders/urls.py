"""
MERRIGE ERP - Захиалгын API URL-ууд
"""

from django.urls import path

from apps.orders.views import (
    GroupedOrderDetailView,
    GroupedOrderExportView,
    GroupedOrderListCreateView,
    OrderApproveView,
    OrderCancelView,
    OrderCompleteView,
    OrderDetailView,
    OrderGroupView,
    OrderHistoryView,
    OrderListCreateView,
    OrderMarkArrivedView,
    OrderRejectView,
    OrderReviewView,
    OrderShipView,
)

app_name = "orders"

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="list-create"),
    path("grouped/", GroupedOrderListCreateView.as_view(), name="grouped-list-create"),
    path(
        "grouped/<uuid:grouped_order_uuid>/",
        GroupedOrderDetailView.as_view(),
        name="grouped-detail",
    ),
    path(
        "grouped/<uuid:grouped_order_uuid>/export/",
        GroupedOrderExportView.as_view(),
        name="grouped-export",
    ),
    path("<uuid:order_uuid>/", OrderDetailView.as_view(), name="detail"),
    path("<uuid:order_uuid>/history/", OrderHistoryView.as_view(), name="history"),
    path("<uuid:order_uuid>/review/", OrderReviewView.as_view(), name="review"),
    path("<uuid:order_uuid>/approve/", OrderApproveView.as_view(), name="approve"),
    path("<uuid:order_uuid>/reject/", OrderRejectView.as_view(), name="reject"),
    path("<uuid:order_uuid>/cancel/", OrderCancelView.as_view(), name="cancel"),
    path("<uuid:order_uuid>/group/", OrderGroupView.as_view(), name="group"),
    path(
        "<uuid:order_uuid>/mark-arrived/",
        OrderMarkArrivedView.as_view(),
        name="mark-arrived",
    ),
    path("<uuid:order_uuid>/ship/", OrderShipView.as_view(), name="ship"),
    path("<uuid:order_uuid>/complete/", OrderCompleteView.as_view(), name="complete"),
]
