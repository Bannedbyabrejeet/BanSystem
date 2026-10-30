"""Claves de Redis compartidas con el Servicio 1.

El contrato completo está documentado en ``docs/REDIS_SCHEMA.md``.
"""

from __future__ import annotations

from typing import Final

#: Hash con ``maxretry``, ``bantime`` y ``findtime`` (minutos).
CONFIG_SETTINGS: Final[str] = "config:settings"
#: Set con IPs y redes CIDR exentas de bloqueo.
CONFIG_WHITELIST: Final[str] = "config:whitelist"
#: Hash de IPs baneadas. Lo escriben el Servicio 1 (baneo manual) y el
#: Servicio 2 (baneo automático y expiración).
IPS_BANNED: Final[str] = "ips:banned"
#: Lista JSON con el historial de baneos y desbaneos.
IPS_HISTORY: Final[str] = "ips:history"
#: ZSET auxiliar con score = ``expires_at`` de cada IP. Permite al worker de
#: expiración encontrar los baneos vencidos sin recorrer todo el hash.
BAN_EXPIRATIONS: Final[str] = "bans:expirations"
#: Stream del contrato de desbaneo manual (Servicio 1 -> Servicio 2).
UNBAN_STREAM: Final[str] = "security:events:unban"
#: Consumer group del stream de desbaneo.
UNBAN_CONSUMER_GROUP: Final[str] = "ufw_workers"
#: Prefijo del ZSET de intentos fallidos por IP.
FAILED_ATTEMPTS_PREFIX: Final[str] = "failed:"


def failed_attempts_key(ip: str) -> str:
    """Devuelve la clave ``failed:<IP>`` del contador deslizante."""
    return f"{FAILED_ATTEMPTS_PREFIX}{ip}"
