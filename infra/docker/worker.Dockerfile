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
COPY apps/shared/python ./apps/shared/python
COPY apps/api/python ./apps/api/python
COPY apps/worker/python ./apps/worker/python

RUN pip install --upgrade pip && \
    pip install ".[worker,shared]"

CMD ["python", "-m", "translator_worker"]