"""Claves de Redis compartidas con el Servicio 1.

El contrato completo está documentado en ``docs/REDIS_SCHEMA.md``.
"""

from __future__ import annotations

from typing import Final

#: Hash con ``maxretry``, ``bantime`` y ``findtime`` (minutos).
CONFIG_SETTINGS: Final[str] = "config:settings"
#: Set con IPs y redes CIDR exentas de bloqueo.
CONFIG_WHITELIST: Final[str] = "config:whitelist"
#: Hash de IPs baneadas. El motor solo lo consulta; UFW se implementa aparte.
IPS_BANNED: Final[str] = "ips:banned"
#: Prefijo del ZSET de intentos fallidos por IP.
FAILED_ATTEMPTS_PREFIX: Final[str] = "failed:"


def failed_attempts_key(ip: str) -> str:
    """Devuelve la clave ``failed:<IP>`` del contador deslizante."""
    return f"{FAILED_ATTEMPTS_PREFIX}{ip}"
