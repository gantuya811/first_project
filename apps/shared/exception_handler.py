"""
MERRIGE ERP - DRF-ийн нэгдсэн алдааны боловсруулагч
Бүх API алдааны мэдээллийг Монгол хэл дээр, нэгдсэн бүтэцтэйгээр буцаана.

Хариултын бүтэц:
{
    "success": false,
    "message": "Хэрэглэгчид харуулах Монгол мессеж",
    "errors": { ... талбар тус бүрийн алдаа ... }
}

Тэмдэглэл: DRF/SimpleJWT-ийн зарим exception (жишээ нь JWTAuthentication-ийн
"User not found", "Token is invalid or expired") Англи detail-ийг instance
үүсгэх үед шууд дамжуулдаг тул class-level орчуулга (apps.shared.localization)
хүрдэггүй. Харин манай өөрсдийн БизнесАлдаа болон Permission.message (жишээ:
IsPasswordChanged) мөн адил "detail" замаар ирдэг ч Монгол байдаг тул зөвхөн
эх сурвалжаар нь (module) ялгах боломжгүй. Тиймээс "detail" нь Кирилл (Монгол)
үсэг агуулж байгаа эсэхээр итгэмжилнэ — агуулбал шууд ашиглана, эс бөгөөс
(гарцаагүй Англи текст) доорх STATUS_MESSAGES-ийн баталгаатай fallback-ыг
ашиглана.
"""

import logging
import re

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("django")

CYRILLIC_PATTERN = re.compile(r"[Ѐ-ӿ]")

STATUS_MESSAGES = {
    400: "Хүсэлтийн өгөгдөлд алдаа байна.",
    401: "Нэвтрэх шаардлагатай.",
    403: "Танд энэ үйлдлийг хийх эрх байхгүй байна.",
    404: "Хүссэн мэдээлэл олдсонгүй.",
    405: "Энэ хүсэлтийн төрөл дэмжигдэхгүй байна.",
    409: "Мэдээлэл давхцаж байна.",
    429: "Хэт олон хүсэлт илгээлээ. Түр хүлээгээд дахин оролдоно уу.",
    500: "Системд алдаа гарлаа. Түр хүлээгээд дахин оролдоно уу.",
}

DEFAULT_MESSAGE = "Хүсэлтийг гүйцэтгэхэд алдаа гарлаа."


def _is_mongolian_text(text):
    return bool(CYRILLIC_PATTERN.search(text))


def merrige_exception_handler(exc, context):
    """DRF-ийн REST_FRAMEWORK['EXCEPTION_HANDLER']-т бүртгэгдэнэ."""

    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = drf_exceptions.PermissionDenied()

    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Барьцаалагдаагүй серверийн алдаа гарлаа: %s", exc)
        return Response(
            {
                "success": False,
                "message": STATUS_MESSAGES[500],
                "errors": None,
            },
            status=500,
        )

    errors = None
    message = STATUS_MESSAGES.get(response.status_code, DEFAULT_MESSAGE)

    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail and _is_mongolian_text(str(detail)):
            message = str(detail)
        elif not detail:
            errors = response.data
        # detail Англи (Кирилл агуулаагүй) бол огт ашиглахгүй, дээрх
        # STATUS_MESSAGES fallback хэвээр үлдэнэ.
    elif isinstance(response.data, list):
        errors = response.data

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response
