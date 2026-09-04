FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app/apps/worker/python:/app/apps/api/python:/app/packages/shared/python

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ffmpeg libgl1 && \
    rm -rf /var/lib/apt/lists/*

COPY packages/shared/python/translator_shared /app/packages/shared/python/translator_shared
COPY apps/api/python/translator_api /app/apps/api/python/translator_api
COPY apps/worker/python/translator_worker /app/apps/worker/python/translator_worker

RUN pip install --upgrade pip \
    && pip install -e /app/packages/shared/python/translator_shared \
    && pip install -e /app/apps/api/python/translator_api \
    && pip install -e /app/apps/worker/python/translator_worker \
    && pip install "psycopg[binary]>=3.2.1" "boto3>=1.34"

CMD ["python", "-m", "translator_worker.main"]
