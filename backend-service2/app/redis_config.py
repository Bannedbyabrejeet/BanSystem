"""Lectura de la configuración compartida en Redis.

El Servicio 2 nunca escribe ``config:*``: esos valores son propiedad del
Servicio 1 (Issue #6). Aquí solo se leen en cada evaluación para que los
cambios del administrador se apliquen de forma dinámica (US-02 / US-09).

La whitelist se interpreta tanto como IP suelta como red CIDR (US-08). Las
entradas locales ``127.0.0.1`` y ``::1`` se consideran siempre protegidas,
aunque Redis todavía no las contenga al arrancar.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from typing import Final

from redis import Redis

from app.keys import CONFIG_SETTINGS, CONFIG_WHITELIST
from app.models import BanSettings

logger = logging.getLogger(__name__)

DEFAULT_MAXRETRY: Final[int] = 5
DEFAULT_BANTIME: Final[int] = 30
DEFAULT_FINDTIME: Final[int] = 10
MAX_MAXRETRY: Final[int] = 1_000
MAX_BANTIME_MINUTES: Final[int] = 525_600
MAX_FINDTIME_MINUTES: Final[int] = 10_080

#: Entradas que el Servicio 1 mantiene siempre en Redis (US-08).
PROTECTED_WHITELIST_ENTRIES: Final[tuple[str, ...]] = ("127.0.0.1", "::1")


def _text(value: str | bytes) -> str:
    return value.decode() if isinstance(value, bytes) else value


def _positive_int(raw: str | bytes | None, default: int, maximum: int) -> int:
    """Convierte un campo de Redis en entero válido o usa el default."""
    if raw is None:
        return default
    text = _text(raw).strip()
    if not re.fullmatch(r"\d+", text):
        return default
    value = int(text)
    return value if 1 <= value <= maximum else default


@dataclass(frozen=True, slots=True)
class WhitelistMatch:
    """Resultado de contrastar una IP contra la lista blanca."""

    matched: bool
    entry: str | None = None


class RedisConfigReader:
    """Lee parámetros y whitelist desde Redis en cada evento."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    def get_settings(self) -> BanSettings:
        """Devuelve los parámetros vigentes con los defaults del contrato."""
        raw = self.redis.hgetall(CONFIG_SETTINGS)
        return BanSettings(
            maxretry=_positive_int(raw.get("maxretry"), DEFAULT_MAXRETRY, MAX_MAXRETRY),
            bantime=_positive_int(
                raw.get("bantime"), DEFAULT_BANTIME, MAX_BANTIME_MINUTES
            ),
            findtime=_positive_int(
                raw.get("findtime"), DEFAULT_FINDTIME, MAX_FINDTIME_MINUTES
            ),
        )

    def get_whitelist(self) -> tuple[str, ...]:
        """Devuelve las entradas normalizadas, incluyendo las locales."""
        raw_entries = self.redis.smembers(CONFIG_WHITELIST)
        entries = {_text(entry).strip() for entry in raw_entries}
        entries.update(PROTECTED_WHITELIST_ENTRIES)
        return tuple(sorted(entry for entry in entries if entry))

    def match_whitelist(self, ip: str) -> WhitelistMatch:
        """Indica si ``ip`` coincide con una entrada o red de la whitelist."""
        try:
            address = ip_address(ip)
        except ValueError:
            logger.warning("IP inválida en el motor de seguridad: %r", ip)
            return WhitelistMatch(False)

        for entry in self.get_whitelist():
            try:
                network = ip_network(entry, strict=False)
            except ValueError:
                logger.warning("Entrada inválida en config:whitelist: %r", entry)
                continue
            if address.version == network.version and address in network:
                return WhitelistMatch(True, entry)

        return WhitelistMatch(False)
