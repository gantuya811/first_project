"""
MERRIGE ERP - Хэрэглэгчийн Admin форм
Django-ийн стандарт UserCreationForm/UserChangeForm нь "username" талбар
ашигладаг тул custom User-ийн "phone_number"-т тохируулан өргөтгөсөн.
"""

from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.accounts.models import User


class UserCreationAdminForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("phone_number", "email", "last_name", "first_name", "role")
        error_messages = {
            "password_mismatch": "Нууц үг хоорондоо таарахгүй байна.",
        }


class UserChangeAdminForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"
