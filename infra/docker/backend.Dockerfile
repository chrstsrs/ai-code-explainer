# Base
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /srv/backend
COPY backend/requirements/ /srv/backend/requirements/
RUN pip install --no-cache-dir -r /srv/backend/requirements/base.txt

# Dev
FROM base AS dev
RUN pip install --no-cache-dir -r /srv/backend/requirements/dev.txt
# Copy project code
COPY backend/ /srv/backend/
WORKDIR /srv/backend/app
EXPOSE 8000

# Prod
FROM base AS prod
RUN pip install --no-cache-dir -r /srv/backend/requirements/prod.txt
# Copy project code
COPY backend/ /srv/backend/
WORKDIR /srv/backend/app
EXPOSE 8000
