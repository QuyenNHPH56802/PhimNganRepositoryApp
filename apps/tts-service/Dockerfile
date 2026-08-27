# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=3099

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install fastapi 'uvicorn[standard]' edge-tts httpx pydantic \
    || pip install fastapi 'uvicorn[standard]' edge-tts httpx pydantic

COPY tts_service ./tts_service
COPY tests ./tests

EXPOSE 3099

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/healthz || exit 1

CMD ["python", "-m", "tts_service.main"]
