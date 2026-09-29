"""
MERRIGE ERP - Стандарт API хариултын туслах функцууд
API STANDARD-ийн дагуу success/error envelope-ийг нэгдсэн, давтагдашгүй
байдлаар үүсгэнэ. Дараагийн бүх STEP-ийн View/ViewSet эндээс ашиглана.

Success:
{"success": true, "message": "Амжилттай", "data": {}}

Error:
{"success": false, "message": "Алдаа гарлаа", "errors": []}
"""

from rest_framework import status
from rest_framework.response import Response


def success_response(data=None, message="Амжилттай", status_code=status.HTTP_200_OK):
    """Амжилттай гүйцэтгэсэн хүсэлтийн стандарт хариулт."""
    return Response(
        {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        },
        status=status_code,
    )


def error_response(
    message="Алдаа гарлаа", errors=None, status_code=status.HTTP_400_BAD_REQUEST
):
    """Амжилтгүй хүсэлтийн стандарт хариулт (DRF-ийн exception_handler-ээс
    гадна, Service Layer-ээс шууд алдаа буцаах шаардлагатай үед ашиглана)."""
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors if errors is not None else [],
        },
        status=status_code,
    )
