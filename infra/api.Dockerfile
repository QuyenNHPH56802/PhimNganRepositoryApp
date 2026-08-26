FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY packages/shared /app/packages/shared
COPY apps/api /app/apps/api

RUN pip install --upgrade pip \
    && pip install -e /app/packages/shared \
    && pip install -e /app/apps/api

EXPOSE 8000
CMD ["uvicorn", "translator_api.main:app", "--host", "0.0.0.0", "--port", "8000"]