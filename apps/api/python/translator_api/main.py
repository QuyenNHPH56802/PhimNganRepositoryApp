"""FastAPI entrypoint."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from translator_api.routers import router
from translator_api.routers_editor import router as editor_router
from translator_api.routers_governance import router as governance_router
from translator_api.routers_admin import router as admin_router
from translator_api.routers_admin_voice import router as admin_voice_router
from translator_api.routers_admin_dataset import router as admin_dataset_router
from translator_api.routers_stream import router as stream_router
from translator_api.routers_capabilities import router as capabilities_router
from translator_api.routers_providers import router as providers_router
from translator_api.routers_workflow_cancel import router as workflow_cancel_router
from translator_api.routers_glossary import router as glossary_router
from translator_api.routers_quality import router as quality_router
from translator_api.routers_webhooks import router as webhooks_router
from translator_api.routers_subtitles import router as multi_subtitles_router
from translator_api.routers_batch import router as batch_router
from translator_api.routers_templates import router as templates_router
from translator_api.routers_ocr import router as ocr_router
from translator_api.routers_separation import router as separation_router
# Importing registry runs bootstrap() at module load, populating the default provider registry
from translator_api.providers import registry as _provider_registry  # noqa: F401
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
    app = FastAPI(
        title="Translator API",
        version="0.1.0",
        description=(
            "API for the PhimNgan video localization platform.\n\n"
            "Provides endpoints for project management, ASR/translation/TTS workflow, "
            "dubbing alignment, video rendering, governance and admin operations.\n\n"
            "## Authentication\n"
            "Most endpoints require a session cookie or `Authorization: Bearer <token>` header. "
            "Admin endpoints additionally require an admin user.\n\n"
            "## Error format\n"
            "Errors are returned as `{\"detail\": \"<message>\"}` with the appropriate HTTP status code."
        ),
        openapi_tags=[
            {"name": "meta", "description": "Operational endpoints (health, auth-debug)."},
            {"name": "projects", "description": "Project CRUD and listing."},
            {"name": "editor", "description": "Editor APIs: transcript, translation, speaker, voice, subtitle, render."},
            {"name": "governance", "description": "Admin-only governance endpoints."},
            {"name": "admin", "description": "Admin console (users, datasets, providers)."},
            {"name": "providers", "description": "Provider registry and configuration."},
            {"name": "workflow", "description": "Workflow control (start, cancel, status)."},
            {"name": "stream", "description": "Server-Sent Events streams."},
            {"name": "events", "description": "Project-scoped event streams."},
            {"name": "capabilities", "description": "Capability negotiation (client/server feature set)."},
            {"name": "metrics", "description": "Prometheus-style metrics."},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

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
    app.include_router(providers_router)
    app.include_router(workflow_cancel_router)
    app.include_router(glossary_router)
    app.include_router(quality_router)
    app.include_router(webhooks_router)
    app.include_router(multi_subtitles_router)
    app.include_router(batch_router)
    app.include_router(templates_router)
    app.include_router(ocr_router)
    app.include_router(separation_router)

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

    @app.get("/docs", include_in_schema=False, tags=["meta"])
    async def custom_swagger_ui_html():
        """Swagger UI for the Translator API."""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False, tags=["meta"])
    async def custom_redoc_html():
        """ReDoc for the Translator API."""
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js",
        )

    return app


app = create_app()
