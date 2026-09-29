"""
MERRIGE ERP - User Management API URL-ууд
"""

from django.urls import path

from apps.accounts.views import (
    RegisterView,
    UserApproveView,
    UserDeactivateView,
    UserDetailView,
    UserListView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("", UserListView.as_view(), name="list"),
    path("<uuid:user_uuid>/", UserDetailView.as_view(), name="detail"),
    path("<uuid:user_uuid>/approve/", UserApproveView.as_view(), name="approve"),
    path("<uuid:user_uuid>/deactivate/", UserDeactivateView.as_view(), name="deactivate"),
]
