# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ffmpeg libgl1 && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY packages/shared/python/translator_shared ./packages/shared/python/translator_shared
COPY apps/api/python/translator_api ./apps/api/python/translator_api
COPY apps/worker/python/translator_worker ./apps/worker/python/translator_worker
COPY infra/migrations ./infra/migrations

RUN pip install --upgrade pip build && \
    pip install ".[api,shared]" && \
    pip install "psycopg[binary]>=3.2.1" "alembic>=1.13" "boto3>=1.34"

EXPOSE 8000

CMD ["uvicorn", "translator_api.main:app", "--host", "0.0.0.0", "--port", "8000"]