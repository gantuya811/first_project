#!/bin/sh
# ============================================================
# MERRIGE ERP - Docker container-ийн эхлэлийн скрипт (зөвхөн "web"
# service-д ашиглагдана). Database бэлэн болохыг хүлээгээд,
# migrate + collectstatic хийсний дараа гол командыг (gunicorn)
# ажиллуулна. Celery worker/beat service-үүд энэ скриптийг ашиглахгүй
# (docker-compose.yml-д entrypoint: [] гэж дарж, migrate-ийг зэрэг
# хэд хэдэн container давхар ажиллуулахаас сэргийлнэ).
# ============================================================
set -e

echo "MERRIGE ERP - Контейнер эхэлж байна..."

python <<'PYEOF'
import os
import sys
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from django.db import connections
from django.db.utils import OperationalError

conn = connections["default"]
max_retries = 30

for attempt in range(1, max_retries + 1):
    try:
        conn.cursor()
        print("Database холболт амжилттай.")
        break
    except OperationalError:
        print(f"Database бэлэн болохыг хүлээж байна... ({attempt}/{max_retries})")
        time.sleep(2)
else:
    print("Database-д холбогдож чадсангүй.", file=sys.stderr)
    sys.exit(1)
PYEOF

echo "Migration ажиллуулж байна..."
python manage.py migrate --noinput

echo "Static файлуудыг цуглуулж байна..."
python manage.py collectstatic --noinput

echo "MERRIGE ERP бэлэн боллоо. Гол командыг ажиллуулж байна: $*"
exec "$@"
