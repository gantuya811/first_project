"""
MERRIGE ERP - Нууц үгийн шалгалт (100% Монгол алдааны мессежтэй)
Django-ийн built-in validator-уудын зарим алдааны мессеж (жишээ нь
MinimumLengthValidator) Монгол хэлний орчуулгын санд бүрэн орчуулагдаагүй
байгааг тестээр илрүүлсэн тул, шаардлагатай логикийг ашиглаад алдааны
текстийг Монголоор шууд гаргана.
"""

from django.contrib.auth import password_validation as django_validation
from django.core.exceptions import ValidationError


class MinimumLengthValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"Нууц үг доод тал нь {self.min_length} тэмдэгт байх ёстой.",
                code="password_too_short",
            )

    def get_help_text(self):
        return f"Нууц үг доод тал нь {self.min_length} тэмдэгт байх ёстой."


class NumericPasswordValidator:
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                "Нууц үг зөвхөн тооноос бүрдэж болохгүй.",
                code="password_entirely_numeric",
            )

    def get_help_text(self):
        return "Нууц үг зөвхөн тооноос бүрдэж болохгүй."


class CommonPasswordValidator(django_validation.CommonPasswordValidator):
    """Түгээмэл, амархан таамаглагдах нууц үгсийн жагсаалтад Django-ийн
    суурь логикийг ашиглана, гэхдээ алдааны мессежийг Монголчилно."""

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as exc:
            raise ValidationError(
                "Энэ нууц үг хэт түгээмэл байна. Өөр нууц үг сонгоно уу.",
                code="password_too_common",
            ) from exc

    def get_help_text(self):
        return "Хэт түгээмэл, амархан таамаглагдах нууц үг ашиглаж болохгүй."


class UserAttributeSimilarityValidator(django_validation.UserAttributeSimilarityValidator):
    """Хэрэглэгчийн нэр/утас/имэйлтэй төстэй нууц үг зөвшөөрөхгүй."""

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as exc:
            raise ValidationError(
                "Нууц үг таны хувийн мэдээлэлтэй хэт төстэй байна.",
                code="password_too_similar",
            ) from exc

    def get_help_text(self):
        return "Нууц үг утасны дугаар, нэр, и-мэйлтэй хэт төстэй байж болохгүй."
