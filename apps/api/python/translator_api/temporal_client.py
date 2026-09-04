"""Temporal client wrapper. Phase 1 only opens a connection; activity dispatch
is the worker's responsibility (see apps/worker)."""

from __future__ import annotations

from temporalio.client import Client

from translator_api.settings import get_settings


async def get_temporal_client() -> Client:
    settings = get_settings()
    return await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )
