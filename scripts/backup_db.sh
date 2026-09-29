#!/usr/bin/env bash
# ============================================================
# MERRIGE ERP - PostgreSQL нөөцлөлт (backup) скрипт
# docker compose-оор ажиллаж буй "db" service-ээс pg_dump ашиглан
# нөөц авч, шахаж (gzip), хуучин нөөцийг цэвэрлэнэ.
#
# Ашиглах (жишээ нь cron-оор өдөр бүр 03:00 цагт):
#   0 3 * * * cd /opt/merrige && BACKUP_RETENTION_DAYS=14 ./scripts/backup_db.sh
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# .env-ээс DB_NAME/DB_USER-г уншина (compose exec нь контейнер дотор
# аль хэдийн эдгээр орчны хувьсагчтай тул давхар унших шаардлагагүй ч
# файлын нэрэнд ашиглахын тулд эндээс тодорхойлно).
DB_NAME="$(grep -E '^DB_NAME=' .env | cut -d '=' -f2- || echo 'merrige_erp')"
DB_USER="$(grep -E '^DB_USER=' .env | cut -d '=' -f2- || echo 'merrige_user')"

mkdir -p "${BACKUP_DIR}"

OUTPUT_FILE="${BACKUP_DIR}/merrige_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Нөөцлөлт эхэллээ: ${OUTPUT_FILE}"
docker compose exec -T db pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${OUTPUT_FILE}"
echo "Нөөцлөлт амжилттай: $(du -h "${OUTPUT_FILE}" | cut -f1)"

echo "${RETENTION_DAYS} хоногоос хуучин нөөцийг устгаж байна..."
find "${BACKUP_DIR}" -name "merrige_*.sql.gz" -type f -mtime "+${RETENTION_DAYS}" -delete

echo "Дууслаа."
