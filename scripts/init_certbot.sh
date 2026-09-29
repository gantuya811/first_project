#!/usr/bin/env bash
# ============================================================
# MERRIGE ERP - Let's Encrypt SSL сертификатыг анх удаа авах скрипт
# Зөвхөн серверийг ШИНЭЭР анх удаа production-д гаргаж байгаа үед
# нэг л удаа ажиллуулна. Дараа нь сертификат нь docker-compose.prod.yml
# доторх "certbot" service-ээр автоматаар шинэчлэгдэнэ (renew).
#
# Ашиглах:
#   SITE_DOMAIN_NAME=merrige.mn CERTBOT_EMAIL=admin@merrige.mn \
#     ./scripts/init_certbot.sh
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

: "${SITE_DOMAIN_NAME:?SITE_DOMAIN_NAME орчны хувьсагчийг заавал өгнө үү (жишээ: merrige.mn)}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL орчны хувьсагчийг заавал өгнө үү (SSL мэдэгдэл авах имэйл)}"

command -v envsubst >/dev/null 2>&1 || {
    echo "АЛДАА: 'envsubst' олдсонгүй. (Debian/Ubuntu: apt-get install -y gettext-base)" >&2
    exit 1
}

echo "1/4: Nginx SSL тохиргоог үүсгэж байна (SITE_DOMAIN=${SITE_DOMAIN_NAME})..."
SITE_DOMAIN="${SITE_DOMAIN_NAME}" envsubst '${SITE_DOMAIN}' \
    < docker/nginx/templates/default.conf.template \
    > docker/nginx/merrige.ssl.conf

echo "2/4: HTTP-only nginx-ийг түр ажиллуулж, ACME challenge замыг нээж байна..."
docker compose up -d nginx

echo "3/4: Let's Encrypt-с сертификат хүсэж байна..."
docker run --rm \
    -v "$(pwd)/docker/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/docker/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot -w /var/www/certbot \
    -d "${SITE_DOMAIN_NAME}" \
    --email "${CERTBOT_EMAIL}" \
    --agree-tos --no-eff-email --non-interactive

echo "4/4: SSL тохиргоотой стекийг эхлүүлж байна..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "Дууслаа. https://${SITE_DOMAIN_NAME} хаягаар шалгана уу."
