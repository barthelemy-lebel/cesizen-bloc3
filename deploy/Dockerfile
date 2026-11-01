# ---------------------------------------------------------------------------
# CESIZen - Image backend Django / DRF
# Build multi-stage : les outils de compilation ne partent pas en production.
# ---------------------------------------------------------------------------

# --------- Stage 1 : construction des dépendances --------------------------
FROM python:3.15-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt


# --------- Stage 2 : image d'exécution -------------------------------------
FROM python:3.15-slim-bookworm AS runtime

# Bonnes pratiques Python en conteneur : pas de .pyc, logs non bufferisés
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=cesizen.settings.production

# libpq5 seul (runtime), curl pour le HEALTHCHECK
RUN apt-get update && apt-get install --no-install-recommends -y \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1001 cesizen \
    && useradd --uid 1001 --gid cesizen --create-home cesizen

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=cesizen:cesizen . .

# Les statiques sont collectés au build : le conteneur de prod reste en lecture seule
RUN SECRET_KEY=build-only DATABASE_URL=postgres://build/build \
    python manage.py collectstatic --noinput

# Aucun processus ne tourne en root (mitigation escalade de privilèges)
USER cesizen

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health/ || exit 1

# 3 workers Gunicorn = (2 x vCPU) + 1 sur le VPS 1 vCPU de staging,
# surchargé par la commande du compose de production.
CMD ["gunicorn", "cesizen.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
