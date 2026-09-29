"""
MERRIGE ERP - Authentication Serializers
Views нимгэн байх ёстой тул оролтын шалгалтыг энд, бизнесийн дүрмийг
services.py-д байрлуулсан (Clean Architecture).
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.accounts.models import User
from apps.shared.validators import validate_phone_number


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "uuid",
            "phone_number",
            "email",
            "first_name",
            "last_name",
            "role",
            "store_name",
            "province",
            "soum",
            "district",
            "address",
            "bank_name",
            "account_number",
            "is_approved",
            "must_change_password",
        )
        read_only_fields = fields


class UserRegisterSerializer(serializers.ModelSerializer):
    """Шинэ Үндсэн/Гэрээт Борлуулагчийн бүртгэлийн форм."""

    phone_number = serializers.CharField(
        validators=[
            validate_phone_number,
            UniqueValidator(
                queryset=User.all_objects.all(),
                message="Энэ утасны дугаар бүртгэлтэй байна.",
            ),
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.all_objects.all(),
                message="Энэ и-мэйл хаяг бүртгэлтэй байна.",
            )
        ]
    )
    parent_seller_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Таныг бүртгүүлсэн Үндсэн Борлуулагчийн утасны дугаар.",
    )

    class Meta:
        model = User
        fields = (
            "phone_number",
            "email",
            "last_name",
            "first_name",
            "role",
            "parent_seller_phone",
            "store_name",
            "province",
            "soum",
            "district",
            "address",
            "bank_name",
            "account_number",
        )

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Админ эрхээр бүртгүүлэх боломжгүй.")
        return value

    def validate(self, attrs):
        role = attrs.get("role", User.Role.CONTRACT_SELLER)
        parent_phone = attrs.get("parent_seller_phone")

        if role == User.Role.CONTRACT_SELLER and not parent_phone:
            raise serializers.ValidationError(
                {
                    "parent_seller_phone": "Гэрээт борлуулагч заавал үндсэн "
                    "борлуулагчийн утасны дугаарыг оруулна уу."
                }
            )
        if role == User.Role.MAIN_SELLER and parent_phone:
            raise serializers.ValidationError(
                {
                    "parent_seller_phone": "Үндсэн Борлуулагч харьяалагдах "
                    "борлуулагчгүй байх ёстой."
                }
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Одоогийн нууц үг буруу байна.")
        return value

    def validate_new_password(self, value):
        user = self.context["request"].user
        validate_password(value, user=user)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Шинэ нууц үг хоорондоо таарахгүй байна."}
            )
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "Шинэ нууц үг хуучин нууц үгтэй адил байж болохгүй."}
            )
        return attrs
