import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import ask, collections, documents, health, search
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.providers.base import ProviderError
from app.providers.registry import ProviderNotAvailableError

logger = logging.getLogger("cognita")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ProviderNotAvailableError)
    async def provider_not_available(_: Request, exc: ProviderNotAvailableError) -> JSONResponse:
        logger.warning("provider_not_available", extra={"data": {"detail": str(exc)}})
        return JSONResponse(status_code=501, content={"detail": str(exc)})

    @app.exception_handler(ProviderError)
    async def provider_error(_: Request, exc: ProviderError) -> JSONResponse:
        # Falha externa (chave inválida, cota, rede): 502 = erro num serviço do qual dependemos.
        logger.warning("provider_error", extra={"data": {"detail": str(exc)}})
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    app.include_router(health.router, prefix="/api")
    app.include_router(collections.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(ask.router, prefix="/api")
    logger.info(
        "app_started",
        extra={"data": {"env": settings.app_env, "llm": settings.llm_provider}},
    )
    return app


app = create_app()
