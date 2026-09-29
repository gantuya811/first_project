"""
MERRIGE ERP - Хэрэглэгчийн Django Admin тохиргоо
100% Монгол хэл дээрх талбар, гарчиг, бүлэглэлттэй админ панель.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.forms import UserChangeAdminForm, UserCreationAdminForm
from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationAdminForm
    form = UserChangeAdminForm
    model = User

    list_display = (
        "phone_number",
        "last_name",
        "first_name",
        "role",
        "store_name",
        "is_approved",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_approved", "is_active", "is_staff")
    search_fields = ("phone_number", "last_name", "first_name", "email", "store_name")
    ordering = ("-created_at",)
    readonly_fields = ("uuid", "created_at", "updated_at", "last_login", "approved_at")
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        ("Нэвтрэлтийн мэдээлэл", {"fields": ("phone_number", "password")}),
        ("Хувийн мэдээлэл", {"fields": ("last_name", "first_name", "email")}),
        (
            "Борлуулагчийн мэдээлэл",
            {
                "fields": (
                    "role",
                    "parent_seller",
                    "store_name",
                    "province",
                    "soum",
                    "district",
                    "address",
                    "bank_name",
                    "account_number",
                )
            },
        ),
        (
            "Эрх, төлөв",
            {
                "fields": (
                    "is_approved",
                    "approved_by",
                    "approved_at",
                    "must_change_password",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Огноо", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            "Шинэ хэрэглэгч үүсгэх",
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "email",
                    "last_name",
                    "first_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
