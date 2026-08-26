FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY packages/shared /app/packages/shared
COPY apps/worker /app/apps/worker

RUN pip install --upgrade pip \
    && pip install -e /app/packages/shared \
    && pip install -e /app/apps/worker

CMD ["python", "-m", "translator_worker.main"]