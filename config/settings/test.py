"""
MERRIGE ERP - Тестийн тохиргоо (Test Settings)
pytest ажиллуулах хурдыг нэмэгдүүлэхийн тулд password hasher хөнгөвчилж,
Rate Limiting-ийг унтраана (тест хурдан бөгөөд тогтвортой ажиллах ёстой,
throttle-ийн улмаас тестүүд санамсаргүйгээр амжилтгүй болохоос сэргийлнэ).
"""

from .development import *  # noqa: F401,F403

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
    # LoginView зэрэг зарим view нь throttle_classes-ийг class attribute-ээр
    # тодорхой зааж өгсөн тул DEFAULT_THROTTLE_CLASSES хоослох нь тэдгээрт
    # нөлөөлдөггүй — "login" scope-ийг устгахгүй, зөвхөн бодит хязгаарлалт
    # тестэд саад болохооргүй хэт өндөр тоо болгов.
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000000/minute",
        "user": "1000000/minute",
        "login": "1000000/minute",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
