"""Almacén de telemetría para el Frontend B (Issue #9).

El motor ya parsea cada línea de ``auth.log``. Para que el visor pueda
mostrar el flujo sin volver a leer el archivo, cada evento se guarda como
JSON en la lista ``ssh:events`` (los más recientes primero, con un tope).

También se leen las sanciones activas (``ips:banned``) y el historial
(``ips:history``) que administra el ciclo de vida de la Issue #8.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Final

from redis import Redis

from app.keys import IPS_BANNED, IPS_HISTORY, SSH_EVENTS
from app.models import SSHEvent

logger = logging.getLogger(__name__)

DEFAULT_EVENT_LIMIT: Final[int] = 2_000
DEFAULT_PAGE_SIZE: Final[int] = 50
MAX_PAGE_SIZE: Final[int] = 200


@dataclass(frozen=True, slots=True)
class EventPage:
    """Página de eventos SSH más los contadores del conjunto filtrado."""

    items: list[dict[str, object]]
    total: int
    success: int
    failed: int


def _text(value: str | bytes) -> str:
    return value.decode() if isinstance(value, bytes) else value


def _json(value: str | bytes) -> dict[str, object] | None:
    try:
        data = json.loads(_text(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


class TelemetryStore:
    """Lee y escribe los datos que consume la consola operativa."""

    def __init__(self, redis: Redis, *, event_limit: int = DEFAULT_EVENT_LIMIT) -> None:
        self.redis = redis
        self.event_limit = event_limit

    # ------------------------------------------------------------------
    # Logs SSH
    # ------------------------------------------------------------------
    def record_event(self, event: SSHEvent, *, received_at: int | None = None) -> None:
        """Guarda un evento parseado en ``ssh:events``.

        Se usa ``LPUSH`` para que el visor muestre primero lo más reciente y
        ``LTRIM`` para acotar el crecimiento de Redis.
        """
        payload = {
            "timestamp": event.timestamp,
            "received_at": received_at if received_at is not None else int(time.time()),
            "ip": event.ip,
            "username": event.username,
            "outcome": event.outcome.value,
            "event_type": event.event_type,
            "raw_line": event.raw_line,
            "countable": event.countable,
            "port": event.port,
        }
        pipe = self.redis.pipeline(transaction=True)
        pipe.lpush(SSH_EVENTS, json.dumps(payload, ensure_ascii=False))
        pipe.ltrim(SSH_EVENTS, 0, self.event_limit - 1)
        pipe.execute()

    def list_events(
        self,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
        outcome: str | None = None,
        ip: str | None = None,
        username: str | None = None,
    ) -> EventPage:
        """Devuelve una página filtrada de eventos y sus contadores."""
        raw_items = self.redis.lrange(SSH_EVENTS, 0, -1)
        filtered: list[dict[str, object]] = []
        wanted_ip = (ip or "").strip()
        wanted_user = (username or "").strip().casefold()

        for raw in raw_items:
            item = _json(raw)
            if item is None:
                continue
            if outcome and item.get("outcome") != outcome:
                continue
            if wanted_ip and item.get("ip") != wanted_ip:
                continue
            if wanted_user and wanted_user not in str(item.get("username") or "").casefold():
                continue
            filtered.append(item)

        total = len(filtered)
        success = sum(1 for item in filtered if item.get("outcome") == "success")
        page = filtered[offset : offset + limit]
        return EventPage(items=page, total=total, success=success, failed=total - success)

    # ------------------------------------------------------------------
    # Baneos e historial
    # ------------------------------------------------------------------
    def list_bans(self) -> list[dict[str, object]]:
        """Devuelve las sanciones activas ordenadas por fecha de baneo."""
        raw = self.redis.hgetall(IPS_BANNED)
        bans: list[dict[str, object]] = []
        for raw_ip, payload in raw.items():
            ip = _text(raw_ip)
            data = _json(payload)
            if data is None:
                logger.warning("Registro corrupto en ips:banned para %s", ip)
                continue
            bans.append({"ip": ip, **data})
        bans.sort(key=lambda item: int(item.get("banned_at", 0)), reverse=True)
        return bans

    def list_history(self, *, limit: int = DEFAULT_PAGE_SIZE, offset: int = 0) -> tuple[list[dict[str, object]], int]:
        """Devuelve una página del historial y el total de entradas."""
        total = int(self.redis.llen(IPS_HISTORY))
        raw_items = self.redis.lrange(IPS_HISTORY, offset, offset + limit - 1)
        items: list[dict[str, object]] = []
        for raw in raw_items:
            data = _json(raw)
            if data is None:
                logger.warning("Entrada corrupta en ips:history")
                continue
            items.append(data)
        return items, total

    def count_events(self) -> int:
        """Cantidad actual de eventos retenidos (para healthcheck)."""
        return int(self.redis.llen(SSH_EVENTS))
