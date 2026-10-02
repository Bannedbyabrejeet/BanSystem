"""Punto de entrada del Servicio 1 (FastAPI).

Incluye ciclo de vida con espera de Redis, CORS restringido a los orígenes
configurados, manejadores de error en español y documentación OpenAPI
(Swagger UI en ``/docs``).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.core import constants
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.api.v1.router import api_router
from app.db.redis import (
    RedisUnavailableError,
    close_redis,
    create_redis_client,
    ping_redis,
    wait_for_redis,
)
from app.services.auth_service import CredentialsNotFoundError

logger = logging.getLogger(__name__)

DESCRIPTION = """
API REST del **Servicio 1** de *Bannedbyabrejeet*: la capa que administra el
sistema de baneo de SSH por web.

* **Autenticación:** creación de la cuenta única de administrador, inicio de
  sesión con JWT y restauración de contraseña con tokens volátiles en Redis.
* **Persistencia:** todas las claves viven en Redis
  (`admin:credentials`, `admin:initialized`, `reset_token:<token>`).

Los endpoints de configuración de baneo, IPs baneadas e historial se
agregan en las issues posteriores del proyecto.
"""

TAGS_METADATA = [
    {"name": "Autenticación", "description": "Setup único, login JWT y recuperación de contraseña."},
    {"name": "Sistema", "description": "Healthcheck y diagnóstico del servicio."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa y libera el cliente de Redis junto con la aplicación."""
    settings: Settings = app.state.settings
    configure_logging(settings.log_level)
    logger.info("Iniciando %s v%s", settings.project_name, settings.version)

    client = create_redis_client(settings)
    app.state.redis = client
    try:
        await wait_for_redis(client, settings)
    except RedisUnavailableError:
        await close_redis(client)
        app.state.redis = None
        raise

    yield

    await close_redis(client)
    app.state.redis = None
    logger.info("Servicio 1 detenido correctamente")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fábrica de la aplicación (facilita los tests con configuración propia)."""
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    app = FastAPI(
        title=active_settings.project_name,
        version=active_settings.version,
        summary="Autenticación y administración del sistema de baneo SSH",
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        docs_url=active_settings.docs_url,
        redoc_url=active_settings.redoc_url,
        openapi_url=active_settings.openapi_url,
        lifespan=lifespan,
        contact={"name": "Equipo Bannedbyabrejeet"},
        license_info={"name": "Uso académico"},
    )
    app.state.settings = active_settings

    allowed_origins = active_settings.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,  # El token viaja en la cabecera Authorization.
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        expose_headers=["WWW-Authenticate"],
        max_age=600,
    )
    logger.info("CORS habilitado para: %s", ", ".join(allowed_origins) or "(ninguno)")

    _register_exception_handlers(app)
    app.include_router(api_router, prefix=active_settings.api_v1_prefix)
    _register_system_routes(app)
    _customize_openapi(app, active_settings)
    return app


# ----------------------------------------------------------------------
# Manejadores de error
# ----------------------------------------------------------------------
def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RedisError)
    @app.exception_handler(RedisUnavailableError)
    async def _redis_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Redis caído: se informa sin filtrar detalles de infraestructura."""
        logger.error("Fallo de Redis en %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=503,
            content={"detail": constants.AUTH_SERVICE_UNAVAILABLE},
        )

    @app.exception_handler(CredentialsNotFoundError)
    async def _corrupted_credentials_handler(
        request: Request, exc: CredentialsNotFoundError
    ) -> JSONResponse:
        """Documento de credenciales ilegible en Redis."""
        logger.error("Credenciales corrupte en Redis: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Las credenciales del administrador están corruptas."},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Aplana los errores de validación de Pydantic a una lista de textos."""
        details: list[str] = []
        for error in exc.errors():
            message = str(error.get("msg", "Dato inválido")).removeprefix("Value error, ")
            # Solo se corrige la primera letra: el resto del mensaje ya está redactado.
            details.append(message[:1].upper() + message[1:])
        return JSONResponse(status_code=422, content={"detail": details or ["Datos inválidos"]})


# ----------------------------------------------------------------------
# Rutas de sistema
# ----------------------------------------------------------------------
def _register_system_routes(app: FastAPI) -> None:
    @app.get("/health", tags=["Sistema"], summary="Healthcheck del servicio y de Redis")
    async def health(request: Request) -> dict[str, object]:
        """Verifica que el proceso responde y que Redis acepta conexiones."""
        redis_alive = await ping_redis(request.app.state.redis)
        return {
            "status": "ok" if redis_alive else "degraded",
            "service": "service1-api",
            "version": app.state.settings.version,
            "environment": app.state.settings.environment,
            "redis": "up" if redis_alive else "down",
        }


# ----------------------------------------------------------------------
# OpenAPI
# ----------------------------------------------------------------------
def _customize_openapi(app: FastAPI, settings: Settings) -> None:
    """Enriquece el esquema OpenAPI con el esquema de seguridad Bearer."""

    def openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=settings.project_name,
            version=settings.version,
            summary="Autenticación y administración del sistema de baneo SSH",
            description=DESCRIPTION,
            routes=app.routes,
            tags=TAGS_METADATA,
        )
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes.setdefault(
            "JWTAuthentication",
            {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        )
        schema["info"]["contact"] = {"name": "Equipo Bannedbyabrejeet"}
        app.openapi_schema = schema
        return schema

    app.openapi = openapi  # type: ignore[method-assign]


app = create_app()
