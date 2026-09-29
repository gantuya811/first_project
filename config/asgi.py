"""
MERRIGE ERP - ASGI тохиргоо (Ирээдүйд WebSocket/мэдэгдэлд ашиглана)
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_asgi_application()
