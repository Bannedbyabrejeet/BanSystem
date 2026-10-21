"""Endpoints de configuración de baneos y lista blanca (Issue #6).

Cubre US-02 (umbral y duración del baneo), US-09 (ventana de tolerancia) y
US-08 (whitelist de IPs y subredes). Todos requieren una sesión de
administrador válida.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ConfigServiceDep, CurrentAdminDep
from app.core import constants
from app.schemas.config import (
    BanSettings,
    WhitelistEntryRequest,
    WhitelistMutationResponse,
    WhitelistResponse,
)
from app.services.config_service import (
    ProtectedWhitelistEntryError,
    WhitelistEntryNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_ERRORS_COMMON: dict[int | str, dict[str, Any]] = {
    401: {
        "description": "Sesión ausente, expirada o revocada.",
        "content": {
            "application/json": {"example": {"detail": constants.SESSION_EXPIRED}}
        },
    },
    422: {"description": "Datos inválidos (valores no enteros o IP mal formada)."},
    503: {
        "description": "Redis no disponible.",
        "content": {
            "application/json": {"example": {"detail": constants.AUTH_SERVICE_UNAVAILABLE}}
        },
    },
}


@router.get(
    "/settings",
    response_model=BanSettings,
    summary="Consultar los parámetros de baneo",
    description=(
        "Lee `config:settings` y devuelve `maxretry`, `bantime` y `findtime`. "
        "Si la clave no existe (o algún campo falta o es inválido), se aplican "
        "los valores por defecto `5`, `30` y `10` respectivamente."
    ),
    responses=_ERRORS_COMMON,
    tags=["Configuración"],
)
async def read_ban_settings(
    service: ConfigServiceDep, _admin: CurrentAdminDep
) -> BanSettings:
    """``GET /api/v1/config/settings`` — US-02 / US-09."""
    return await service.get_settings()


@router.put(
    "/settings",
    response_model=BanSettings,
    summary="Actualizar los parámetros de baneo",
    description=(
        "Sobrescribe los tres campos de `config:settings` en una sola operación. "
        "`maxretry`, `bantime` y `findtime` deben ser enteros positivos estrictos "
        "mayores a cero. Los cambios los toma el Servicio 2 en la siguiente "
        "evaluación."
    ),
    responses=_ERRORS_COMMON,
    tags=["Configuración"],
)
async def update_ban_settings(
    payload: BanSettings,
    service: ConfigServiceDep,
    admin: CurrentAdminDep,
) -> BanSettings:
    """``PUT /api/v1/config/settings`` — US-02 / US-09."""
    logger.info(
        "El administrador %s actualiza los parámetros de baneo", admin.username
    )
    return await service.update_settings(payload)


@router.get(
    "/whitelist",
    response_model=WhitelistResponse,
    summary="Consultar la lista blanca",
    description=(
        "Devuelve las IPs y subredes exentas de bloqueo. Las entradas "
        "`127.0.0.1` y `::1` siempre están presentes y se informan aparte en "
        "`protected_entries`."
    ),
    responses=_ERRORS_COMMON,
    tags=["Configuración"],
)
async def read_whitelist(
    service: ConfigServiceDep, _admin: CurrentAdminDep
) -> WhitelistResponse:
    """``GET /api/v1/config/whitelist`` — US-08."""
    return WhitelistResponse(entries=await service.get_whitelist())


@router.post(
    "/whitelist",
    response_model=WhitelistMutationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una IP o subred a la lista blanca",
    description=(
        "Acepta IPv4, IPv6 y notación CIDR. La entrada se normaliza antes de "
        "guardarse (por ejemplo `10.1.2.3/8` se persiste como `10.0.0.0/8`). "
        "Si la dirección ya existe la operación es idempotente."
    ),
    responses=_ERRORS_COMMON,
    tags=["Configuración"],
)
async def add_whitelist_entry(
    payload: WhitelistEntryRequest,
    service: ConfigServiceDep,
    admin: CurrentAdminDep,
) -> WhitelistMutationResponse:
    """``POST /api/v1/config/whitelist`` — US-08."""
    try:
        entry, created = await service.add_whitelist_entry(payload.entry)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=constants.INVALID_NETWORK_ENTRY,
        ) from exc

    logger.info(
        "El administrador %s agrega %s a la lista blanca", admin.username, entry
    )
    return WhitelistMutationResponse(
        entries=await service.get_whitelist(),
        message=(
            constants.WHITELIST_ENTRY_ADDED
            if created
            else constants.WHITELIST_ENTRY_EXISTS
        ),
        entry=entry,
    )


@router.delete(
    "/whitelist",
    response_model=WhitelistMutationResponse,
    summary="Eliminar una IP o subred de la lista blanca",
    description=(
        "Recibe la entrada como query param (`?entry=10.0.0.0/8`) para evitar "
        "problemas de enrutamiento con la barra de CIDR. Las IPs locales "
        "`127.0.0.1` y `::1` no pueden eliminarse: la API responde `409`."
    ),
    responses={
        **_ERRORS_COMMON,
        404: {
            "description": "La entrada no está en la lista blanca.",
            "content": {
                "application/json": {
                    "example": {"detail": constants.WHITELIST_ENTRY_NOT_FOUND}
                }
            },
        },
        409: {
            "description": "La entrada es una IP local protegida.",
            "content": {
                "application/json": {
                    "example": {"detail": constants.PROTECTED_WHITELIST_ENTRY}
                }
            },
        },
    },
    tags=["Configuración"],
)
async def remove_whitelist_entry(
    service: ConfigServiceDep,
    admin: CurrentAdminDep,
    entry: str = Query(
        min_length=1,
        max_length=64,
        description="IP o subred a eliminar.",
        examples=["192.168.1.10"],
    ),
) -> WhitelistMutationResponse:
    """``DELETE /api/v1/config/whitelist?entry=...`` — US-08."""
    try:
        removed = await service.remove_whitelist_entry(entry)
    except ProtectedWhitelistEntryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=constants.PROTECTED_WHITELIST_ENTRY,
        ) from exc
    except WhitelistEntryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=constants.WHITELIST_ENTRY_NOT_FOUND,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=constants.INVALID_NETWORK_ENTRY,
        ) from exc

    logger.info(
        "El administrador %s elimina %s de la lista blanca", admin.username, removed
    )
    return WhitelistMutationResponse(
        entries=await service.get_whitelist(),
        message=constants.WHITELIST_ENTRY_REMOVED,
        entry=removed,
    )
