"""
MERRIGE ERP - Celery тохиргоо (Celery Ready)
Ашиг тооцоолол, шимтгэл бодолт, имэйл/мэдэгдэл илгээх зэрэг
хугацаа шаардсан ажлуудыг арын процессоор гүйцэтгэхэд ашиглана.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("merrige_erp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
