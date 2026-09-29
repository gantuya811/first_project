"""
MERRIGE ERP - Нийтлэг бизнес алдааны классууд
Domain Driven Design шаардлагын дагуу бизнесийн дүрэм зөрчигдөх үед
энэ файлын алдааг өргөтгөж ашиглана (жишээ нь: барааны үлдэгдэл хүрэлцэхгүй,
захиалгын төлөв буруу шилжилт хийх гэх мэт).
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class БизнесАлдаа(APIException):
    """Бизнес дүрэм зөрчигдөх үед дэд app-ууд удамшуулан ашиглана."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Хүсэлтийг гүйцэтгэх боломжгүй байна."
    default_code = "business_rule_error"


class ЭрхийнАлдаа(APIException):
    """Хэрэглэгч тухайн үйлдлийг хийх эрхгүй үед үүснэ."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Танд энэ үйлдлийг хийх эрх байхгүй байна."
    default_code = "permission_denied"


class ХүчинтэйБайдлынАлдаа(APIException):
    """Оролтын өгөгдөл бизнесийн дүрэмд нийцэхгүй үед үүснэ."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Оруулсан мэдээлэл буруу байна."
    default_code = "validation_error"


class ДавхардсанБичлэгАлдаа(APIException):
    """Давхардсан утга (жишээ: барааны код) хадгалахыг завдах үед үүснэ."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Ийм мэдээлэл системд аль хэдийн бүртгэлтэй байна."
    default_code = "duplicate_error"
