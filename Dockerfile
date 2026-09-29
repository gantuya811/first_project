# ============================================================
# MERRIGE ERP - Docker image (Production-ready, multi-stage build)
# Stage 1 (builder) нь Python сангуудыг угсарч, Stage 2 (runtime) нь
# зөвхөн шаардлагатай эцсийн үр дүнг (венгре биш) агуулна — image-ийн
# хэмжээг багасгаж, аюулгүй байдлыг сайжруулна (build tool-ууд эцсийн
# image-д ороогүй).
# ============================================================

# ---------- Stage 1: Builder ----------
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# psycopg[binary] зэрэг binary wheel-гүй сан тохиолдвол эх кодоос
# угсрах шаардлагатай болдог тул build-essential-ийг найдвартай
# байдлын үүднээс оруулсан (эцсийн image-д хуулагдахгүй).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# ---------- Stage 2: Runtime ----------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# libpq5 нь PostgreSQL клиент сангийн runtime хувилбар (dev header
# биш) — psycopg[binary]-д зарим тохиолдолд шаардлагатай байдаг.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash merrige

COPY --from=builder /root/.local /root/.local
COPY --chown=merrige:merrige . .

RUN mkdir -p /app/staticfiles /app/media /app/logs /app/exports /app/archives \
    && chown -R merrige:merrige /app/staticfiles /app/media /app/logs /app/exports /app/archives \
    && chmod +x /app/docker/entrypoint.sh

USER merrige

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
