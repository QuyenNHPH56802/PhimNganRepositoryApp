FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/packages/shared/python:/app/apps/api/python

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ffmpeg libgl1 && \
    rm -rf /var/lib/apt/lists/*

COPY packages/shared/python/translator_shared /app/packages/shared/python/translator_shared
COPY apps/api/python/translator_api /app/apps/api/python/translator_api
COPY infra/migrations /app/infra/migrations

RUN pip install --upgrade pip \
    && pip install -e /app/packages/shared/python/translator_shared \
    && pip install -e /app/apps/api/python/translator_api \
    && pip install "psycopg[binary]>=3.2.1" "boto3>=1.34" "uvicorn[standard]" "alembic>=1.13" "python-multipart>=0.0.9"

EXPOSE 8000
CMD ["uvicorn", "translator_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
