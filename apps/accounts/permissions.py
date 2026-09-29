"""
MERRIGE ERP - Хэрэглэгчийн эрхийн (RBAC) класс
"Эхний нэвтрэлтээр нууц үг заавал солино. Нууц үг солих хүртэл системийн
үндсэн үйлдэл хийхгүй." дүрмийг API-ийн бүх endpoint дээр нэгдсэн байдлаар
хэрэгжүүлнэ (REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES-д бүртгэгдсэн).
"""

from rest_framework.permissions import BasePermission


class IsPasswordChanged(BasePermission):
    message = "Эхлээд нууц үгээ солино уу."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return True
        return not user.must_change_password


class IsAdminRole(BasePermission):
    """Зөвхөн Админ эрхтэй хэрэглэгчид зөвшөөрнө (RBAC). Дараагийн STEP-үүдийн
    (Хэрэглэгч баталгаажуулах, нууц үнэ/ашгийн мэдээлэл гэх мэт) Админ-т
    хязгаарлагдсан endpoint-үүд эндээс удамшина."""

    message = "Танд энэ үйлдлийг хийх эрх байхгүй байна."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)
