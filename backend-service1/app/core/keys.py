"""Nombres de claves de Redis utilizados por el Servicio 1.

Esquema documentado en ``docs/REDIS_SCHEMA.md``:

======================================  ==========  ===================  ======
Clave                                   Tipo        TTL                  Uso
======================================  ==========  ===================  ======
``admin:credentials``                   String JSON sin TTL             credenciales
``admin:initialized``                   String       sin TTL             setup único
``reset_token:<token>``                 String JSON ``SETEX`` 900 s     recuperación
``admin:reset_tokens``                  Set          sin TTL             revocación
``config:settings``                     Hash         sin TTL             umbrales
``config:whitelist``                    Set          sin TTL             lista blanca
======================================  ==========  ===================  ======
"""

from __future__ import annotations

from typing import Final

#: Credenciales cifradas del administrador (hash Argon2id). Persistente.
ADMIN_CREDENTIALS: Final[str] = "admin:credentials"
#: Marcador permanente que impide crear un segundo administrador.
ADMIN_INITIALIZED: Final[str] = "admin:initialized"
#: Set con los tokens de recuperación vigentes de cada administrador.
ADMIN_RESET_TOKENS: Final[str] = "admin:reset_tokens"

#: Prefijo de los tokens de recuperación (clave creada con SETEX).
RESET_TOKEN_PREFIX: Final[str] = "reset_token:"

#: Parámetros de baneo (hash con ``maxretry``, ``bantime`` y ``findtime``).
CONFIG_SETTINGS: Final[str] = "config:settings"
#: Lista blanca de IPs y subredes (set). Persistente.
CONFIG_WHITELIST: Final[str] = "config:whitelist"

#: Rol incluido en el JWT del administrador.
ADMIN_ROLE: Final[str] = "admin"


def reset_token_key(token: str) -> str:
    """Devuelve la clave ``reset_token:<token>`` para un token dado."""
    return f"{RESET_TOKEN_PREFIX}{token}"
