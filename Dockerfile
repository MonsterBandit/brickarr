# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

# Base images are pinned by tag plus digest (BR.DK.02): change both together.
# Find a digest with `docker buildx imagetools inspect <image>:<tag>`.

# --- Stage 1: build the React SPA ---------------------------------------------
FROM node:20.20.2-alpine3.23@sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293 AS frontend
WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# --- Stage 2: Python runtime that serves both API and SPA ---------------------
FROM python:3.12.15-slim-trixie@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2 AS runtime

# BRICKARR_CACHE_DIR is deliberately not set: it defaults to the library, so an
# unmounted /cache never becomes a folder or volume of its own.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PUID=1000 \
    PGID=1000 \
    TZ=Etc/UTC \
    UMASK=022 \
    BRICKARR_CONFIG_DIR=/config \
    BRICKARR_LIBRARY_DIR=/library

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

# Entrypoint handles UMASK, PUID/PGID, folders, migrations, then exec's uvicorn.
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh

# Set late so a new version doesn't invalidate the layers above.
ARG BRICKARR_VERSION=0.0.0-dev
ENV BRICKARR_VERSION=${BRICKARR_VERSION}
LABEL org.opencontainers.image.version=${BRICKARR_VERSION}

# Only /config is a volume: /library is the user's own mount, and /cache falls
# back to the library when it isn't mounted.
VOLUME ["/config"]
EXPOSE 5858

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5858/api/v1/ping >/dev/null || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5858", "--proxy-headers", "--forwarded-allow-ips=*"]
