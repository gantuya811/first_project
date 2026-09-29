"""
MERRIGE ERP - apps.core / apps.shared-ийн нийтлэг infra тестүүд
100% Монгол хэлний шаардлагыг баталгаажуулах validator/localization/
exception_handler-ийн unit тест.
"""

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.shared.exception_handler import _is_mongolian_text
from apps.shared.password_validators import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)
from apps.shared.validators import MongolianPhoneNumberValidator


class TestPhoneNumberValidator:
    def test_valid_number_passes(self):
        MongolianPhoneNumberValidator()("88112233")

    def test_seven_digit_number_rejected(self):
        with pytest.raises(DjangoValidationError):
            MongolianPhoneNumberValidator()("8811223")

    def test_number_starting_with_wrong_digit_rejected(self):
        with pytest.raises(DjangoValidationError):
            MongolianPhoneNumberValidator()("48112233")

    def test_error_message_is_mongolian(self):
        try:
            MongolianPhoneNumberValidator()("123")
        except DjangoValidationError as exc:
            assert _is_mongolian_text(str(exc.message))


class TestPasswordValidators:
    def test_minimum_length_rejects_short_password(self):
        with pytest.raises(DjangoValidationError):
            MinimumLengthValidator(min_length=8).validate("short1")

    def test_numeric_only_password_rejected(self):
        with pytest.raises(DjangoValidationError):
            NumericPasswordValidator().validate("12345678")

    def test_valid_password_passes(self):
        MinimumLengthValidator(min_length=8).validate("GoodPass123")
        NumericPasswordValidator().validate("GoodPass123")

    def test_common_password_rejected_with_mongolian_message(self):
        with pytest.raises(DjangoValidationError) as exc_info:
            CommonPasswordValidator().validate("password")
        assert _is_mongolian_text(str(exc_info.value.message))

    def test_uncommon_password_passes_common_check(self):
        CommonPasswordValidator().validate("Zqx8!TuvNerd42")

    def test_similarity_validator_rejects_similar_password(self, main_seller):
        # Django-ийн анхдагч шалгалт зөвхөн username/first_name/last_name/
        # email-тэй харьцуулдаг (phone_number-тэй биш) тул email ашиглана.
        with pytest.raises(DjangoValidationError) as exc_info:
            UserAttributeSimilarityValidator().validate(
                main_seller.email, user=main_seller
            )
        assert _is_mongolian_text(str(exc_info.value.message))

    def test_similarity_validator_passes_dissimilar_password(self, main_seller):
        UserAttributeSimilarityValidator().validate("Zqx8!TuvNerd42", user=main_seller)

    def test_get_help_text_returns_mongolian(self):
        assert _is_mongolian_text(MinimumLengthValidator().get_help_text())
        assert _is_mongolian_text(NumericPasswordValidator().get_help_text())
        assert _is_mongolian_text(CommonPasswordValidator().get_help_text())
        assert _is_mongolian_text(UserAttributeSimilarityValidator().get_help_text())


class TestMongolianTextDetection:
    def test_detects_cyrillic(self):
        assert _is_mongolian_text("Амжилттай") is True

    def test_detects_pure_english_as_not_mongolian(self):
        assert _is_mongolian_text("Request was throttled.") is False

    def test_mixed_text_detected_as_mongolian(self):
        assert _is_mongolian_text("Хэт олон хүсэлт. Try again.") is True


class TestFieldLocalizationApplied:
    """apps.shared.localization.apply_mongolian_translations()-ийг
    SharedConfig.ready()-ээс аль хэдийн дуудсан эсэхийг баталгаажуулна
    (Django AppConfig.ready() бүх тестийн эхэнд нэг л удаа ажилладаг)."""

    def test_charfield_required_message_is_mongolian(self):
        from rest_framework import serializers

        field = serializers.CharField()
        assert _is_mongolian_text(str(field.error_messages["required"]))

    def test_email_invalid_message_is_mongolian(self):
        from rest_framework import serializers

        field = serializers.EmailField()
        assert _is_mongolian_text(str(field.error_messages["invalid"]))


@pytest.mark.django_db
class TestExceptionHandlerIntegration:
    def test_not_authenticated_returns_mongolian_message(self, api_client):
        response = api_client.get("/api/v1/notifications/")
        assert response.status_code == 401
        assert _is_mongolian_text(response.data["message"])

    def test_not_found_returns_mongolian_message(self, admin_client):
        import uuid

        response = admin_client.get(f"/api/v1/products/{uuid.uuid4()}/")
        assert response.status_code == 404
        assert _is_mongolian_text(response.data["message"])
