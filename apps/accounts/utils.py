"""
MERRIGE ERP - Accounts app-ийн тусламж функцууд
"""

import secrets
import string

_PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%"


def generate_random_password(length=12):
    """Админ баталгаажуулах үед хэрэглэгчид олгох криптограф хувьд
    аюулгүй санамсаргүй анхны нууц үг үүсгэнэ (доод, дээд үсэг, тоо агуулна)."""
    while True:
        password = "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return password
