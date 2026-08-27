"""FastAPI entrypoint."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from translator_api.routers import router
from translator_api.routers_governance import router as governance_router
from translator_api.routers_admin import router as admin_router
from translator_api.routers_admin_voice import router as admin_voice_router
from translator_api.routers_admin_dataset import router as admin_dataset_router
from translator_api.routers_stream import router as stream_router
from translator_api.observability import configure_logging, install_fastapi, setup_telemetry
from translator_api.middleware import install as install_shedder

configure_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Translator API", version="0.1.0")
    setup_telemetry(app)
    install_fastapi(app)
    install_shedder(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(governance_router)
    app.include_router(admin_router)
    app.include_router(admin_voice_router)
    app.include_router(admin_dataset_router)
    app.include_router(stream_router)

    @app.get("/projects/{project_id}/events", tags=["events"])
    async def stream_events(project_id: str) -> StreamingResponse:
        async def iterator() -> AsyncIterator[bytes]:
            yield b": heartbeat\n\n"
            while True:
                await asyncio.sleep(15)
                payload = json.dumps({"project_id": project_id, "type": "heartbeat"})
                yield f"data: {payload}\n\n".encode()

        return StreamingResponse(iterator(), media_type="text/event-stream")

    from translator_api.observability.metrics import metrics_router, observe_requests_middleware

    app.include_router(metrics_router)
    app.middleware("http")(observe_requests_middleware)

    return app


app = create_app()