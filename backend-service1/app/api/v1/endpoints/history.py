"""Endpoints para el historial de IPs baneadas (Issue #7).

Cubre US-06: Consulta de historial y estado actual de IPs.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import ConfigServiceDep, CurrentAdminDep
from app.core import constants
from app.schemas.config import HistoryEntry
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

router = APIRouter()

_ERRORS_COMMON: dict[int | str, dict[str, Any]] = {
    401: {
        "description": "Sesión ausente, expirada o revocada.",
        "content": {
            "application/json": {"example": {"detail": constants.SESSION_EXPIRED}}
        },
    },
    503: {
        "description": "Redis no disponible.",
        "content": {
            "application/json": {"example": {"detail": constants.AUTH_SERVICE_UNAVAILABLE}}
        },
    },
}


@router.get(
    "/",
    response_model=list[HistoryEntry],
    summary="Listar historial de baneos",
    description=(
        "Devuelve el historial de todas las acciones de baneo/desbaneo realizadas "
        "en el sistema. Las entradas más recientes aparecen primero (LPUSH).\n"
        "Cada elemento incluye la IP, acción, timestamps y razón."
    ),
    responses=_ERRORS_COMMON,
    tags=["Issue #7 - Historial"],
)
async def read_banned_ip_history(
    service: ConfigServiceDep, _admin: CurrentAdminDep,
    limit: int = Query(50, ge=1, le=1000, description="Número máximo de entradas a devolver"),
) -> list[HistoryEntry]:
    """``GET /api/v1/banned-ips/history/`` — US-06: listar historial."""

    import json

    raw = await service.redis.lrange("ips:history", 0, limit - 1)
    history: list[HistoryEntry] = []

    for entry_str in raw:
        try:
            entry = json.loads(entry_str) if isinstance(entry_str, str) else json.loads(entry_str.decode())
            history.append(
                HistoryEntry(
                    ip=entry.get("ip", ""),
                    action=entry.get("action", ""),
                    banned_at=entry.get("banned_at", 0),
                    unbanned_at=entry.get("unbanned_at"),
                    duration_min=entry.get("duration_min", 0),
                    reason=entry.get("reason", ""),
                    unban_reason=entry.get("unban_reason"),
                )
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Entrada corrupta en historial: %s", exc)
            continue

    return history