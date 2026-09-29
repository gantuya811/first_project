"""
MERRIGE ERP - Нийтлэг validator-ууд
Олон app-д давтагдаж ашиглагдах шалгалтуудыг (утасны дугаар гэх мэт) эндээс
дуудаж ашиглана. Алдааны мессеж 100% Монгол хэл дээр байна.
"""

import re

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class MongolianPhoneNumberValidator:
    """Монгол улсын гар утасны дугаарын формат: 8 оронтой, 5-9 тоогоор эхэлнэ."""

    regex = re.compile(r"^[5-9]\d{7}$")
    message = "Утасны дугаар 8 оронтой бөгөөд 5, 6, 7, 8, 9 тоогоор эхэлсэн байх ёстой."
    code = "invalid_phone_number"

    def __call__(self, value):
        if not self.regex.match(value):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return isinstance(other, MongolianPhoneNumberValidator)


validate_phone_number = MongolianPhoneNumberValidator()


# ------------------------------------------------------------------
# Файлын шалгалт (File Validation - SECURITY шаардлага)
# ------------------------------------------------------------------
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
MAX_IMAGE_SIZE_MB = 5

validate_image_extension = FileExtensionValidator(
    allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
    message="Зөвхөн JPG, JPEG, PNG, WEBP форматын зураг оруулна уу.",
    code="invalid_image_extension",
)


def validate_image_size(file):
    """Зургийн хэмжээг хязгаарлаж, сервер рүү хэт том файл орохоос сэргийлнэ."""
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(
            f"Зургийн хэмжээ {MAX_IMAGE_SIZE_MB}MB-ээс хэтрэхгүй байх ёстой.",
            code="image_too_large",
        )


# ------------------------------------------------------------------
# Төлбөрийн баримтын шалгалт (PDF-г ч дэмждэг тул ImageField-ийн
# Pillow-based шалгалт ашиглах боломжгүй — өргөтгөл/хэмжээгээр шалгана)
# ------------------------------------------------------------------
ALLOWED_RECEIPT_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "pdf"]
MAX_RECEIPT_SIZE_MB = 10

validate_receipt_extension = FileExtensionValidator(
    allowed_extensions=ALLOWED_RECEIPT_EXTENSIONS,
    message="Зөвхөн JPG, JPEG, PNG, WEBP, PDF файл оруулна уу.",
    code="invalid_receipt_extension",
)


def validate_receipt_size(file):
    """Төлбөрийн баримтын файлын хэмжээг хязгаарлана."""
    max_bytes = MAX_RECEIPT_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(
            f"Файлын хэмжээ {MAX_RECEIPT_SIZE_MB}MB-ээс хэтрэхгүй байх ёстой.",
            code="receipt_too_large",
        )
