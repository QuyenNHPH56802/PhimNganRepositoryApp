"""FastAPI entrypoint."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from translator_api.routers import router
from translator_api.routers_editor import router as editor_router
from translator_api.routers_governance import router as governance_router
from translator_api.routers_admin import router as admin_router
from translator_api.routers_admin_voice import router as admin_voice_router
from translator_api.routers_admin_dataset import router as admin_dataset_router
from translator_api.routers_stream import router as stream_router
from translator_api.routers_capabilities import router as capabilities_router
from translator_api.observability import configure_logging, install_fastapi, setup_telemetry
from translator_api.middleware import install as install_shedder

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    from translator_api.db import _engine
    from translator_api.models import Base
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=_engine)
    logger.info("Database tables created.")
    yield
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(title="Translator API", version="0.1.0", lifespan=lifespan)

    # Custom exception handler to ensure CORS headers on error responses
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
        # Manually add CORS headers for error responses
        origin = request.headers.get("origin", "")
        if origin in ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
        origin = request.headers.get("origin", "")
        if origin in ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response

    @app.get("/auth-debug", tags=["meta"])
    async def auth_debug():
        from translator_api.auth_dependency import (
            OWNER_USER_ID,
            OWNER_EMAIL,
            OWNER_DISPLAY_NAME,
        )
        return {
            "mode": "single-user",
            "user_id": OWNER_USER_ID,
            "email": OWNER_EMAIL,
            "display_name": OWNER_DISPLAY_NAME,
        }

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )
    setup_telemetry(app)
    install_fastapi(app)
    install_shedder(app)
    app.include_router(router)
    app.include_router(editor_router)
    app.include_router(governance_router)
    app.include_router(admin_router)
    app.include_router(admin_voice_router)
    app.include_router(admin_dataset_router)
    app.include_router(stream_router)
    app.include_router(capabilities_router)

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