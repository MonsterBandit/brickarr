# syntax=docker/dockerfile:1.7

# --- Stage 1: build the React SPA ---------------------------------------------
FROM node:20-alpine AS frontend
WORKDIR /build

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# --- Stage 2: Python runtime that serves both API and SPA ---------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PUID=1000 \
    PGID=1000 \
    TZ=Etc/UTC \
    BRICKARR_CONFIG_DIR=/config \
    BRICKARR_STORAGE_DIR=/storage

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        tini \
        gosu \
        tzdata \
        ca-certificates \
        curl \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1000 brickarr \
 && useradd  --system --uid 1000 --gid brickarr --home /app --shell /usr/sbin/nologin brickarr

WORKDIR /app

# Install Python deps first for layer caching.
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Backend source (Alembic config sits at /app/alembic.ini per backend layout).
COPY backend/ /app/

# Built SPA from stage 1 — FastAPI serves it as StaticFiles + SPA fallback.
COPY --from=frontend /build/dist/ /app/app/static/

# Entrypoint handles PUID/PGID, volume permissions, migrations, then exec's uvicorn.
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh

VOLUME ["/config", "/storage"]
EXPOSE 5858

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5858", "--proxy-headers", "--forwarded-allow-ips=*"]
