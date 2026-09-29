"""
MERRIGE ERP - Нэвтрэлтэд зориулсан хатуу Rate Limiting
Нууц үг таах (brute-force) халдлагаас хамгаалахын тулд /auth/login/
endpoint-т ерөнхий anon-throttle-ээс илүү хатуу хязгаар тавина.
"""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"
