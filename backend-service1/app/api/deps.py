"""Dependencias compartidas por los endpoints de la API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis

from app.core import constants
from app.core.config import Settings
from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    TokenPayload,
    decode_access_token,
)
from app.db.redis import get_redis
from app.schemas.auth import AdminRecord
from app.services.auth_service import AuthService
from app.services.mail_service import MailService

#: Esquema Bearer: FastAPI lo publica en Swagger UI (botón "Authorize").
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="JWTAuthentication",
    description="Token devuelto por `POST /api/v1/auth/login`.",
)

RedisDep = Annotated[Redis, Depends(get_redis)]


def get_settings_from_app(request: Request) -> Settings:
    """Configuración de la instancia de la aplicación en ejecución.

    Se lee de ``app.state`` en lugar del singleton global para que las
    pruebas puedan correr con su propia configuración (bcrypt barato, TTL
    corto) sin tocar el entorno del proceso.
    """
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_settings_from_app)]


def get_auth_service(redis: RedisDep, settings: SettingsDep) -> AuthService:
    """Construye el servicio de autenticación con el cliente Redis."""
    return AuthService(redis, settings)


def get_mail_service(settings: SettingsDep) -> MailService:
    return MailService(settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
MailServiceDep = Annotated[MailService, Depends(get_mail_service)]


def get_client_ip(request: Request) -> str:
    """IP del cliente, respetando ``X-Forwarded-For`` si hay un proxy delante."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "desconocida"


def unauthorized(detail: str) -> HTTPException:
    """Construye un ``401`` con la cabecera ``WWW-Authenticate`` obligatoria."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: SettingsDep,
) -> TokenPayload:
    """Verifica la firma y los claims del JWTBearer."""
    if credentials is None or not credentials.credentials:
        raise unauthorized(constants.MISSING_TOKEN)
    try:
        return decode_access_token(credentials.credentials, settings=settings)
    except ExpiredTokenError as exc:
        raise unauthorized(constants.SESSION_EXPIRED) from exc
    except InvalidTokenError as exc:
        raise unauthorized(constants.SESSION_REVOKED) from exc


async def get_current_admin(
    token: Annotated[TokenPayload, Depends(get_current_token)],
    service: AuthServiceDep,
) -> AdminRecord:
    """Valida el JWT y lo contrasta con el estado de Redis.

    El token no basta por sí solo: además debe coincidir el
    ``session_version``, por lo que un cambio de contraseña invalida de
    inmediato todas las sesiones abiertas.
    """
    record = await service.get_session_admin(token.subject, token.session_version)
    if record is None:
        raise unauthorized(constants.SESSION_REVOKED)
    return record


CurrentTokenDep = Annotated[TokenPayload, Depends(get_current_token)]
CurrentAdminDep = Annotated[AdminRecord, Depends(get_current_admin)]
