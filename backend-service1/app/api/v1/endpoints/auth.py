"""Endpoints de autenticación del administrador.

Cubre US-01.2 (setup único), US-01 (login), US-01.3 (recuperación de
contraseña) y US-10 (expiración estricta por TTL nativo de Redis).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import (
    AuthServiceDep,
    CurrentAdminDep,
    CurrentTokenDep,
    MailServiceDep,
    get_client_ip,
)
from app.core import constants
from app.core.keys import ADMIN_ROLE
from app.core.security import TokenPayload, create_access_token
from app.schemas.auth import (
    AdminPublic,
    AuthStatusResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SessionResponse,
    SetupRequest,
    TokenResponse,
    VerifyResetTokenResponse,
)
from app.services.auth_service import AlreadyInitializedError, ResetOutcome
from app.services.mail_service import MailDeliveryError

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Respuestas de error reutilizables en la documentación de Swagger ------
_ERRORS_COMMON: dict[int | str, dict[str, Any]] = {
    422: {"description": "Datos inválidos (por ejemplo, contraseña débil)."},
    503: {
        "description": "Redis no disponible.",
        "content": {
            "application/json": {"example": {"detail": constants.AUTH_SERVICE_UNAVAILABLE}}
        },
    },
}

_ERRORS_INVALID_RESET_TOKEN: dict[str, Any] = {
    "description": "Token expirado (Redis lo eliminó por TTL), ya consumido o inexistente.",
    "content": {"application/json": {"example": {"detail": constants.RESET_TOKEN_INVALID}}},
}


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="Consultar si el administrador ya fue creado",
    description=(
        "El Frontend A lo consulta al arrancar. Si `initialized` es `false`, "
        "redirige automáticamente a la pantalla de creación de la cuenta única."
    ),
    responses=_ERRORS_COMMON,
    tags=["Autenticación"],
)
async def read_auth_status(service: AuthServiceDep) -> AuthStatusResponse:
    """``GET /api/v1/auth/status`` → ``{"initialized": bool}``."""
    return AuthStatusResponse(initialized=await service.is_initialized())


@router.post(
    "/setup",
    response_model=AdminPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Crear la cuenta única de administrador",
    description=(
        "Solo funciona una vez. La escritura de `admin:credentials` y del marcador "
        "`admin:initialized` se hace en un único script Lua, por lo que dos "
        "peticiones simultáneas no pueden crear dos administradores: la segunda "
        "recibe `409`. Tras un `201` el Frontend A redirige al login."
    ),
    responses={
        **_ERRORS_COMMON,
        409: {
            "description": "Ya existe un administrador registrado.",
            "content": {
                "application/json": {"example": {"detail": constants.ALREADY_INITIALIZED}}
            },
        },
    },
    tags=["Autenticación"],
)
async def setup_admin(payload: SetupRequest, service: AuthServiceDep) -> AdminPublic:
    """``POST /api/v1/auth/setup`` — CU-01.2 / US-01.2."""
    # Comprobación rápida para dar la respuesta habitual; la condición
    # autoritativa vive en el script Lua.
    if await service.is_initialized():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=constants.ALREADY_INITIALIZED
        )

    try:
        record = await service.create_initial_admin(
            username=payload.username,
            email=str(payload.email),
            password=payload.password,
        )
    except AlreadyInitializedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=constants.ALREADY_INITIALIZED
        ) from exc

    return AdminPublic.from_record(record)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description=(
        "Valida las credenciales contra el hash bcrypt guardado en Redis y devuelve "
        "un JWT HS256 válido por `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`. Con credenciales "
        f"incorrectas responde `401` con el mensaje `{constants.INVALID_CREDENTIALS}`."
    ),
    responses={
        **_ERRORS_COMMON,
        401: {
            "description": "Credenciales incorrectas.",
            "content": {
                "application/json": {"example": {"detail": constants.INVALID_CREDENTIALS}}
            },
            "headers": {"WWW-Authenticate": {"description": "Bearer", "schema": {"type": "string"}}},
        },
    },
    tags=["Autenticación"],
)
async def login(
    payload: LoginRequest, service: AuthServiceDep, request: Request
) -> TokenResponse:
    """``POST /api/v1/auth/login`` — US-01 / BACK1-01."""
    record = await service.authenticate(payload.identifier, payload.password)
    if record is None:
        logger.warning(
            "Intento de login fallido desde %s (identificador=%s)",
            get_client_ip(request),
            payload.identifier,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(
        subject=record.admin_id,
        session_version=record.session_version,
        role=ADMIN_ROLE,
        settings=service.settings,
    )
    logger.info("Inicio de sesión exitoso de %s desde %s", record.username, get_client_ip(request))
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        admin=AdminPublic.from_record(record),
    )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar enlace de recuperación de contraseña",
    description=(
        "Si el correo está registrado, genera un token opaco de 256 bits, lo guarda "
        "en `reset_token:<token>` con `SETEX` y el TTL configurado (900 s por "
        "defecto) y envía el correo con el enlace `/reset-password?token=...`. "
        "La respuesta es **idéntica** exista o no el correo: no permite enumerar cuentas."
    ),
    responses={
        **_ERRORS_COMMON,
        502: {
            "description": "El servidor SMTP no pudo entregar el correo.",
            "content": {
                "application/json": {
                    "example": {"detail": "No se pudo enviar el correo. Intentá nuevamente."}
                }
            },
        },
    },
    tags=["Autenticación"],
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthServiceDep,
    mail: MailServiceDep,
) -> ForgotPasswordResponse:
    """``POST /api/v1/auth/forgot-password`` — US-01.3."""
    created = await service.create_reset_token(str(payload.email))

    if created is None:
        logger.info("Solicitud de recuperación para un correo no registrado")
    else:
        record, token = created
        try:
            await mail.send_password_reset(
                to_email=record.email, username=record.username, token=token
            )
        except MailDeliveryError as exc:
            # Si el correo no salió, el token no sirve: se revoca para que el
            # administrador pueda solicitar otro inmediatamente.
            logger.error("Entrega del correo de recuperación fallida: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No se pudo enviar el correo. Intentá nuevamente.",
            ) from exc

    return ForgotPasswordResponse(
        message=constants.RESET_REQUEST_ACCEPTED,
        email=payload.email,
        expires_in=service.settings.reset_token_ttl,
    )


@router.get(
    "/verify-reset-token/{token}",
    response_model=VerifyResetTokenResponse,
    summary="Validar la vigencia de un enlace de recuperación",
    description=(
        "El Frontend A lo invoca al abrir el enlace. Si Redis ya eliminó la clave "
        "por TTL, o si el token fue consumido, responde `404` con el mensaje "
        f"`{constants.RESET_TOKEN_INVALID}` y el formulario no llega a mostrarse."
    ),
    responses={**_ERRORS_COMMON, 404: _ERRORS_INVALID_RESET_TOKEN},
    tags=["Autenticación"],
)
async def verify_reset_token(token: str, service: AuthServiceDep) -> VerifyResetTokenResponse:
    """``GET /api/v1/auth/verify-reset-token/{token}`` — US-10."""
    info = await service.get_reset_token_info(token)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=constants.RESET_TOKEN_INVALID
        )

    return VerifyResetTokenResponse(
        valid=True, expires_in=info.expires_in, expires_at=info.expires_at
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Establecer la nueva contraseña",
    description=(
        "Consume el token (un solo uso), guarda el nuevo hash bcrypt e incrementa "
        "`session_version`, lo que invalida cualquier sesión abierta antes del cambio. "
        f"Responde `{constants.PASSWORD_UPDATED}`."
    ),
    responses={**_ERRORS_COMMON, 404: _ERRORS_INVALID_RESET_TOKEN},
    tags=["Autenticación"],
)
async def reset_password(
    payload: ResetPasswordRequest, service: AuthServiceDep
) -> MessageResponse:
    """``POST /api/v1/auth/reset-password`` — US-01.3."""
    outcome = await service.consume_reset_token(payload.token, payload.new_password)
    if outcome is not ResetOutcome.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=constants.RESET_TOKEN_INVALID
        )

    return MessageResponse(message=constants.PASSWORD_UPDATED)


@router.get(
    "/me",
    response_model=SessionResponse,
    summary="Datos de la sesión activa",
    description=(
        "Valida el JWT y lo contrasta con Redis. Si la contraseña fue cambiada, "
        "responde `401` aunque el token todavía no haya expirado."
    ),
    responses={
        **_ERRORS_COMMON,
        401: {
            "description": "Token ausente, inválido, expirado o revocado.",
            "content": {
                "application/json": {"example": {"detail": constants.SESSION_EXPIRED}}
            },
        },
    },
    tags=["Autenticación"],
)
async def read_current_session(
    record: CurrentAdminDep, token: CurrentTokenDep
) -> SessionResponse:
    """``GET /api/v1/auth/me`` — sesión vigente del administrador."""
    return SessionResponse(
        admin=AdminPublic.from_record(record),
        role=token.role or ADMIN_ROLE,
        token_expires_at=token.expires_at,
    )
