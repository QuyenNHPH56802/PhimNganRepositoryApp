"""Worker helpers: build DB session + storage for activities."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session, sessionmaker

from translator_api.settings import get_settings
from translator_api.storage_pkg import LocalStorage, S3CompatibleStorage


def make_worker_session_factory() -> sessionmaker[Session]:
    settings = get_settings()
    from sqlalchemy import create_engine

    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True, client_encoding="utf8")
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
    finally:
        session.close()


def build_storage():
    settings = get_settings()
    provider_str = (settings.storage_provider_id or "").lower()
    if provider_str in {"local", "local_fs", "local_storage"}:
        return LocalStorage()
    return S3CompatibleStorage()


async def get_redis_client():
    import os

    url = os.environ.get("TRANSLATOR_REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis.asyncio as redis_asyncio  # type: ignore[import-not-found]

        return redis_asyncio.from_url(url, decode_responses=False)
    except Exception:
        class _Stub:
            async def get(self, _key):  # type: ignore[no-redef]
                return None

            async def set(self, _key, _value, ex=None):  # type: ignore[no-redef]
                return None

        return _Stub()
