"""
MERRIGE ERP - DRF/SimpleJWT-ийн Монгол хэлний орчуулга
Django REST Framework болон SimpleJWT нь Монгол хэлний орчуулгын сан (locale)
огт агуулаагүй тул, "УИ 100% Монгол хэл дээр байна" шаардлагыг найдвартай
хангахын тулд талбарын шалгалт (required/blank/invalid...) болон нийтлэг
exception-уудын анхдагч (default) мессежийг эндээс шууд Монголчилно.

Энэ файл apps.shared.apps.SharedConfig.ready()-ээс Django эхлэхэд нэг л удаа
дуудагдана (Django-ийн gettext орчуулгын каталогоос үл хамааран, тайлбарын
текстийг тодорхой, найдвартай байлгах зорилготой).
"""

from rest_framework import exceptions, fields, serializers

FIELD_MESSAGES = {
    fields.Field: {
        "required": "Энэ талбарыг заавал бөглөнө үү.",
        "null": "Энэ талбар хоосон байж болохгүй.",
    },
    fields.CharField: {
        "invalid": "Зөв бичвэр оруулна уу.",
        "blank": "Энэ талбарыг хоосон орхиж болохгүй.",
        "max_length": "Хамгийн ихдээ {max_length} тэмдэгт оруулна уу.",
        "min_length": "Хамгийн багадаа {min_length} тэмдэгт оруулна уу.",
    },
    fields.BooleanField: {
        "invalid": "Тийм/Үгүй утга оруулна уу.",
    },
    fields.EmailField: {
        "invalid": "Зөв и-мэйл хаяг оруулна уу.",
    },
    fields.RegexField: {
        "invalid": "Оруулсан утга шаардлагатай форматад тохирохгүй байна.",
    },
    fields.URLField: {
        "invalid": "Зөв URL хаяг оруулна уу.",
    },
    fields.UUIDField: {
        "invalid": "Зөв UUID утга оруулна уу.",
    },
    fields.IPAddressField: {
        "invalid": "Зөв IPv4 эсвэл IPv6 хаяг оруулна уу.",
    },
    fields.IntegerField: {
        "invalid": "Бүхэл тоон утга оруулна уу.",
        "max_value": "Утга {max_value}-ээс ихгүй байх ёстой.",
        "min_value": "Утга {min_value}-ээс багагүй байх ёстой.",
        "max_string_length": "Оруулсан утга хэт урт байна.",
    },
    fields.FloatField: {
        "invalid": "Тоон утга оруулна уу.",
        "max_value": "Утга {max_value}-ээс ихгүй байх ёстой.",
        "min_value": "Утга {min_value}-ээс багагүй байх ёстой.",
        "max_string_length": "Оруулсан утга хэт урт байна.",
    },
    fields.DecimalField: {
        "invalid": "Тоон утга оруулна уу.",
        "max_value": "Утга {max_value}-ээс ихгүй байх ёстой.",
        "min_value": "Утга {min_value}-ээс багагүй байх ёстой.",
        "max_digits": "Нийт орон {max_digits}-ээс ихгүй байх ёстой.",
        "max_decimal_places": "Аравтын орон {max_decimal_places}-ээс ихгүй байх ёстой.",
        "max_whole_digits": "Бүхэл тооны орон {max_whole_digits}-ээс ихгүй байх ёстой.",
        "max_string_length": "Оруулсан утга хэт урт байна.",
    },
    fields.DateTimeField: {
        "invalid": "Огноо, цагийн формат буруу байна.",
        "date": "Огноо биш, огноо+цаг оруулна уу.",
        "make_aware": "Цагийн бүсийн утга буруу байна.",
        "overflow": "Огноо, цагийн утга хязгаараас хэтэрсэн байна.",
    },
    fields.DateField: {
        "invalid": "Огнооны формат буруу байна.",
        "datetime": "Огноо биш, огноо+цаг оруулсан байна.",
    },
    fields.TimeField: {
        "invalid": "Цагийн формат буруу байна.",
    },
    fields.DurationField: {
        "invalid": "Хугацааны формат буруу байна.",
        "max_value": "Хугацаа {max_value}-ээс ихгүй байх ёстой.",
        "min_value": "Хугацаа {min_value}-ээс багагүй байх ёстой.",
    },
    fields.ChoiceField: {
        "invalid_choice": '"{input}" сонголт хүчингүй байна.',
    },
    fields.MultipleChoiceField: {
        "invalid_choice": '"{input}" сонголт хүчингүй байна.',
        "not_a_list": "Жагсаалт төрлөөр оруулна уу.",
        "empty": "Хамгийн багадаа нэг сонголт хийнэ үү.",
    },
    fields.FilePathField: {
        "invalid_choice": "Сонгосон файлын зам хүчингүй байна.",
    },
    fields.FileField: {
        "required": "Файл оруулаагүй байна.",
        "invalid": "Оруулсан өгөгдөл файл биш байна.",
        "max_length": "Файлын нэр хэт урт байна ({max_length} тэмдэгтээс ихгүй байх ёстой).",
        "empty": "Хоосон файл оруулж болохгүй.",
    },
    fields.ImageField: {
        "invalid_image": "Оруулсан файл эвдэрсэн эсвэл зураг биш байна.",
    },
    fields.ListField: {
        "not_a_list": "Жагсаалт төрлөөр оруулна уу.",
        "empty": "Хоосон жагсаалт оруулж болохгүй.",
        "min_length": "Хамгийн багадаа {min_length} элемент байх ёстой.",
        "max_length": "Хамгийн ихдээ {max_length} элемент байх ёстой.",
    },
    fields.JSONField: {
        "invalid": "Зөв JSON утга оруулна уу.",
    },
}

EXCEPTION_DEFAULT_DETAILS = {
    exceptions.APIException: "Серверт алдаа гарлаа.",
    exceptions.ValidationError: "Оруулсан мэдээлэл буруу байна.",
    exceptions.ParseError: "Илгээсэн хүсэлтийн формат буруу байна.",
    exceptions.AuthenticationFailed: "Нэвтрэлтийн мэдээлэл буруу байна.",
    exceptions.NotAuthenticated: "Эхлээд нэвтэрнэ үү.",
    exceptions.PermissionDenied: "Танд энэ үйлдлийг хийх эрх байхгүй байна.",
    exceptions.NotFound: "Хүссэн мэдээлэл олдсонгүй.",
    exceptions.NotAcceptable: "Хүсэлтийн формат дэмжигдэхгүй байна.",
    exceptions.UnsupportedMediaType: "Илгээсэн файлын төрөл дэмжигдэхгүй байна.",
    exceptions.Throttled: "Хэт олон хүсэлт илгээлээ.",
}


def apply_mongolian_translations():
    """DRF-ийн field болон exception классуудын анхдагч мессежийг Монголчилно."""

    for field_class, messages in FIELD_MESSAGES.items():
        field_class.default_error_messages = {
            **field_class.default_error_messages,
            **messages,
        }

    for exc_class, message in EXCEPTION_DEFAULT_DETAILS.items():
        exc_class.default_detail = message

    # Throttled exception нь "Request was throttled." (default_detail) дээр
    # хугацааны нэмэлт хэсгийг (жишээ нь "Expected available in 31 seconds.")
    # тусад нь холбож дамждаг тул үүнийг ч мөн Монголчилно.
    exceptions.Throttled.extra_detail_singular = "{wait} секундын дараа дахин оролдоно уу."
    exceptions.Throttled.extra_detail_plural = "{wait} секундын дараа дахин оролдоно уу."

    serializers.Serializer.default_error_messages = {
        **serializers.Serializer.default_error_messages,
        "invalid": "Буруу өгөгдөл: dictionary төрлөөр илгээнэ үү.",
    }
    serializers.ListSerializer.default_error_messages = {
        **serializers.ListSerializer.default_error_messages,
        "not_a_list": "Жагсаалт төрлөөр илгээнэ үү.",
        "empty": "Хоосон жагсаалт илгээж болохгүй.",
    }
