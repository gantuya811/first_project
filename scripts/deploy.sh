#!/usr/bin/env bash
# ============================================================
# MERRIGE ERP - Production deploy скрипт
# Хамгийн сүүлийн кодыг татаж, Docker image-ийг дахин барьж,
# стекийг зогсоолгүйгээр (rolling) шинэчилнэ. Migration/collectstatic-ийг
# docker/entrypoint.sh (STEP17) аль хэдийн автоматаар хийдэг.
#
# Ашиглах:
#   ./scripts/deploy.sh
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE_FILES=(-f docker-compose.yml)
if [ -f docker-compose.prod.yml ] && [ -f docker/nginx/merrige.ssl.conf ]; then
    COMPOSE_FILES+=(-f docker-compose.prod.yml)
fi

echo "1/4: Хамгийн сүүлийн кодыг татаж байна (git pull)..."
git pull --ff-only

echo "2/4: Docker image-ийг дахин барьж байна..."
docker compose "${COMPOSE_FILES[@]}" build

echo "3/4: Контейнеруудыг шинэчилж байна (migration/collectstatic автоматаар ажиллана)..."
docker compose "${COMPOSE_FILES[@]}" up -d

echo "4/4: Хэрэглэгдэхгүй болсон хуучин image-үүдийг цэвэрлэж байна..."
docker image prune -f

echo "Deploy амжилттай дууслаа."
docker compose "${COMPOSE_FILES[@]}" ps
