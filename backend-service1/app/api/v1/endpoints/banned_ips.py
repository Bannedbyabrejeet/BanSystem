"""Endpoints para la gestión de IPs baneadas (Issue #7).

Cubre US-06: Consulta de historial y estado actual de IPs.
Cubre US-07: Desbaneo manual de IP desde el Dashboard.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ConfigServiceDep, CurrentAdminDep
from app.core import constants
from app.schemas.config import BanRecord, WhitelistMutationResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_ERRORS_COMMON: dict[int | str, dict[str, Any]] = {
    401: {
        "description": "Sesión ausente, expirada o revocada.",
        "content": {
            "application/json": {"example": {"detail": constants.SESSION_EXPIRED}}
        },
    },
    422: {"description": "Datos inválidos."},
    503: {
        "description": "Redis no disponible.",
        "content": {
            "application/json": {"example": {"detail": constants.AUTH_SERVICE_UNAVAILABLE}}
        },
    },
}


@router.get(
    "/",
    response_model=list[BanRecord],
    summary="Listar IPs baneadas activas",
    description=(
        "Devuelve el listado de IPs actualmente baneadas almacenadas en "
        "`ips:banned`. Cada entrada incluye la IP, fecha de baneo, tiempo de expiración y razón."
    ),
    responses=_ERRORS_COMMON,
    tags=["Issue #7 - IPs Baneadas"],
)
async def read_banned_ips(
    service: ConfigServiceDep, _admin: CurrentAdminDep
) -> list[BanRecord]:
    """``GET /api/v1/banned-ips/`` — US-06 / US-07."""

    import json

    raw = await service.redis.hgetall("ips:banned")
    if not raw:
        return []

    banned_ips: list[BanRecord] = []
    for ip_str, data_str in raw.items():
        ip = ip_str.decode() if isinstance(ip_str, bytes) else ip_str
        try:
            data = json.loads(data_str.decode() if isinstance(data_str, bytes) else data_str)
            banned_ips.append(
                BanRecord(
                    ip=ip,
                    banned_at=data.get("banned_at", 0),
                    expires_at=data.get("expires_at", 0),
                    duration_min=data.get("duration_min", 0),
                    reason=data.get("reason", "Desconocido"),
                )
            )
        except (json.JSONDecodeError, KeyError):
            logger.warning("Datos corruptos en ips:banned para IP %s", ip)
            continue

    return banned_ips


@router.post(
    "/",
    response_model=WhitelistMutationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Banear una IP (manual)",
    description=(
        "Registra una IP baneada manualmente en `ips:banned` y la agrega al historial `ips:history`.\n"
        "También publica un evento en el stream `security:events:unban` para que el Servicio 2 pueda desbloquear en UFW si es necesario.\n"
        "**Requiere que el administrador tenga sesión activa.**"
    ),
    responses={
        **_ERRORS_COMMON,
        409: {
            "description": "La IP ya está baneada.",
            "content": {
                "application/json": {"example": {"detail": "IP already banned"}}
            },
        },
    },
    tags=["Issue #7 - IPs Baneadas"],
)
async def ban_ip_manual(
    service: ConfigServiceDep,
    admin: CurrentAdminDep,
    ip: str = Query(..., min_length=1, max_length=64, description="IP a banear"),
) -> WhitelistMutationResponse:
    """``POST /api/v1/banned-ips/`` — US-07: banear IP manualmente."""

    import json
    import time

    from app.core.network import normalize_ip_or_network

    # Normalizar IP
    try:
        normalized_ip = normalize_ip_or_network(ip)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=constants.INVALID_NETWORK_ENTRY,
        ) from exc

    # Verificar si ya está baneada
    existing = await service.redis.hexists("ips:banned", normalized_ip)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="IP already banned",
        )

    now = int(time.time())
    bantime = (await service.get_settings()).bantime
    expires_at = now + (bantime * 60) if bantime else 0

    # Registrar en ips:banned
    ban_info = json.dumps(
        {
            "banned_at": now,
            "expires_at": expires_at,
            "duration_min": bantime or 30,
            "reason": "Manual administration",
        }
    )
    await service.redis.hset("ips:banned", normalized_ip, ban_info)

    # Agregar al historial
    history_entry = {
        "ip": normalized_ip,
        "action": "banned",
        "banned_at": now,
        "unbanned_at": None,
        "duration_min": bantime or 30,
        "reason": "Manual administration",
        "unban_reason": "manual",
    }
    # Usar Lua para escribir en la lista de historial de forma atómica
    lua_script = """
    local history_key = KEYS[1]
    local new_entry = ARGV[1]
    local max_len = tonumber(ARGV[2])
    redis.call('LPUSH', history_key, new_entry)
    redis.call('LTRIM', history_key, 0, max_len - 1)
    return redis.call('LLEN', history_key)
    """

    await service.redis.eval(
        lua_script,
        1,
        "ips:history",
        json.dumps(history_entry),
        1000,  # max 1000 entries
    )

    # Un baneo manual no publica en ``security:events:unban``: ese stream es
    # exclusivamente para órdenes de desbaneo (Issue #2). El Servicio 2
    # reconcilia ``ips:banned`` y aplica la expiración con ``bantime``.
    logger.info(
        "El administrador %s baneó manualmente la IP %s", admin.username, normalized_ip
    )

    return WhitelistMutationResponse(
        entries=[normalized_ip],  # type: ignore[arg-type]
        message="IP baneada manualmente",
        entry=normalized_ip,
    )


@router.delete(
    "/{ip}",
    response_model=WhitelistMutationResponse,
    summary="Desbanear una IP (manual)",
    description=(
        "Remueve una IP de `ips:banned`, la agrega al historial con acción 'unbanned'"
        " y ejecuta el desbaneo en UFW a través del Servicio 2 (stream `security:events:unban`)."
        " La IP pasará al estado 'Desbaneada manualmente' en Redis."
    ),
    responses={
        **_ERRORS_COMMON,
        404: {
            "description": "La IP no está baneada.",
            "content": {
                "application/json": {"example": {"detail": "IP not found in banned list"}}
            },
        },
    },
    tags=["Issue #7 - IPs Baneadas"],
)
async def unban_ip_manual(
    service: ConfigServiceDep,
    admin: CurrentAdminDep,
    ip: str,
) -> WhitelistMutationResponse:
    """``DELETE /api/v1/banned-ips/{ip}`` — US-07: desbanear IP manualmente."""

    import json
    import time

    from app.core.network import normalize_ip_or_network

    try:
        normalized_ip = normalize_ip_or_network(ip)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=constants.INVALID_NETWORK_ENTRY,
        ) from exc

    # Verificar si está baneada
    exists = await service.redis.hexists("ips:banned", normalized_ip)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP not found in banned list",
        )

    now = int(time.time())

    # Obtener información actual antes de remover
    data_str = await service.redis.hget("ips:banned", normalized_ip)
    data = json.loads(data_str) if data_str else {}

    # Remover de ips:banned
    await service.redis.hdel("ips:banned", normalized_ip)

    # Agregar al historial con acción unbanned
    history_entry = {
        "ip": normalized_ip,
        "action": "unbanned",
        "banned_at": data.get("banned_at", now),
        "unbanned_at": now,
        "duration_min": data.get("duration_min", 30),
        "reason": data.get("reason", "Manual administration"),
        "unban_reason": "manual",
    }

    # LPUSH en historial
    await service.redis.lpush("ips:history", json.dumps(history_entry))
    # Mantener tope de 1000
    await service.redis.ltrim("ips:history", 0, 999)

    # Publicar evento en stream para que Servicio 2 desbloquee en UFW
    try:
        stream = "security:events:unban"
        await service.redis.xadd(
            stream,
            {
                "action": "UNBAN",
                "ip": normalized_ip,
                "requested_by": admin.username,
                "timestamp": str(now),
            },
            maxlen=10000,
            approximate=True,
        )
        logger.info("Evento de desbaneo publicado para IP %s", normalized_ip)
    except Exception:
        logger.warning("No se pudo publicar evento en stream para desbaneo")

    logger.info(
        "El administrador %s desbaneó IP %s", admin.username, normalized_ip
    )

    return WhitelistMutationResponse(
        entries=[normalized_ip],  # type: ignore[arg-type]
        message="IP desbaneada manualmente",
        entry=normalized_ip,
    )