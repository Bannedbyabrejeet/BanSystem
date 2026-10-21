"""Lógica de negocio de la configuración de baneos y la lista blanca.

Referencias:

* **US-02** — umbral de intentos fallidos y duración del baneo.
* **US-09** — ventana de tolerancia (``findtime``).
* **US-08** — alta y baja de IPs/subredes, con ``127.0.0.1`` y ``::1``
  siempre presentes e inmutables.

El contrato de claves está documentado en ``docs/REDIS_SCHEMA.md`` §2 y §3.
"""

from __future__ import annotations

import logging
import re
from typing import Final

from redis.asyncio import Redis

from app.core.keys import CONFIG_SETTINGS, CONFIG_WHITELIST
from app.core.network import (
    PROTECTED_WHITELIST_ENTRIES,
    is_protected_whitelist_entry,
    normalize_ip_or_network,
)
from app.schemas.config import (
    MAX_BANTIME_MINUTES,
    MAX_FINDTIME_MINUTES,
    MAX_MAXRETRY,
    BanSettings,
)

logger = logging.getLogger(__name__)

#: Valores usados cuando la clave no existe o un campo es inválido.
DEFAULT_MAXRETRY: Final[int] = 5
DEFAULT_BANTIME: Final[int] = 30
DEFAULT_FINDTIME: Final[int] = 10


class ProtectedWhitelistEntryError(ValueError):
    """Se intentó eliminar una entrada local protegida (US-08)."""


class WhitelistEntryNotFoundError(LookupError):
    """La entrada que se quiere eliminar no está en la lista blanca."""


def _positive_int(raw: str | None, default: int, maximum: int) -> int:
    """Convierte un valor de Redis en un entero válido o usa el default.

    El contrato tolera claves incompletas o escritas a mano por el Servicio 2:
    un campo ausente, no numérico o fuera de rango vuelve a su valor por
    defecto en lugar de romper la vista de configuración.
    """
    if raw is None or not re.fullmatch(r"\d+", str(raw).strip()):
        return default

    value = int(raw)
    return value if 1 <= value <= maximum else default


class ConfigService:
    """Operaciones sobre ``config:settings`` y ``config:whitelist``."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def ensure_defaults(self) -> None:
        """Deja la lista blanca con las IPs locales al arrancar el servicio.

        Se ejecuta en el ``lifespan`` para que el Servicio 2 encuentre la
        protección local incluso antes de la primera petición del dashboard.
        """
        await self._ensure_protected_entries()

    # ------------------------------------------------------------------
    # US-02 / US-09 — parámetros de baneo
    # ------------------------------------------------------------------
    async def get_settings(self) -> BanSettings:
        """Devuelve los parámetros vigentes, completando los valores por defecto."""
        raw = await self.redis.hgetall(CONFIG_SETTINGS)
        return BanSettings(
            maxretry=_positive_int(raw.get("maxretry"), DEFAULT_MAXRETRY, MAX_MAXRETRY),
            bantime=_positive_int(raw.get("bantime"), DEFAULT_BANTIME, MAX_BANTIME_MINUTES),
            findtime=_positive_int(
                raw.get("findtime"), DEFAULT_FINDTIME, MAX_FINDTIME_MINUTES
            ),
        )

    async def update_settings(self, settings: BanSettings) -> BanSettings:
        """Escribe los tres campos juntos en el hash persistente."""
        await self.redis.hset(CONFIG_SETTINGS, mapping=settings.model_dump())
        logger.info(
            "Parámetros de baneo actualizados: maxretry=%d bantime=%d findtime=%d",
            settings.maxretry,
            settings.bantime,
            settings.findtime,
        )
        return settings

    # ------------------------------------------------------------------
    # US-08 — lista blanca
    # ------------------------------------------------------------------
    async def get_whitelist(self) -> list[str]:
        """Lista ordenada de entradas, asegurando las locales protegidas."""
        await self._ensure_protected_entries()
        entries = await self.redis.smembers(CONFIG_WHITELIST)
        return sorted(entries)

    async def add_whitelist_entry(self, entry: str) -> tuple[str, bool]:
        """Agrega una IP/subred ya normalizada.

        Returns:
            ``(entrada_normalizada, agregada)``. ``agregada`` es ``False``
            si la dirección ya estaba en la lista (operación idempotente).
        """
        normalized = normalize_ip_or_network(entry)
        await self._ensure_protected_entries()
        added = bool(await self.redis.sadd(CONFIG_WHITELIST, normalized))
        if added:
            logger.info("Entrada agregada a la lista blanca: %s", normalized)
        return normalized, added

    async def remove_whitelist_entry(self, entry: str) -> str:
        """Elimina una entrada, salvo que sea una IP local protegida.

        Raises:
            ProtectedWhitelistEntryError: la entrada es ``127.0.0.1`` o ``::1``.
            WhitelistEntryNotFoundError: la entrada no existe.
        """
        normalized = normalize_ip_or_network(entry)
        # Se reinsertan las locales antes de validar: así siguen presentes
        # incluso si un intento de borrado es rechazado.
        await self._ensure_protected_entries()

        if is_protected_whitelist_entry(normalized):
            raise ProtectedWhitelistEntryError(normalized)

        removed = bool(await self.redis.srem(CONFIG_WHITELIST, normalized))
        if not removed:
            raise WhitelistEntryNotFoundError(normalized)

        logger.info("Entrada eliminada de la lista blanca: %s", normalized)
        return normalized

    async def _ensure_protected_entries(self) -> None:
        """Reinserta las IPs locales si alguien las borró por fuera de la API."""
        await self.redis.sadd(CONFIG_WHITELIST, *PROTECTED_WHITELIST_ENTRIES)
