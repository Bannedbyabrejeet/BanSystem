"""Lógica de negocio de la autenticación del administrador.

Responsabilidades:

* **CU-01.2 / US-01.2** — setup único e irrepetible del administrador.
  La comprobación y la escritura se ejecutan en un único script Lua, de
  modo que dos peticiones simultáneas no puedan crear dos cuentas.
* **US-01** — autenticación contra el hash bcrypt almacenado en Redis.
* **US-01.3** — emisión de tokens de recuperación.
* **US-10** — expiración estricta: el token se crea con ``SETEX`` y Redis
  lo elimina solo al cumplirse el TTL. Ningún proceso del backend hace
  de limpieza posterior.

Estructura de claves: ver ``docs/REDIS_SCHEMA.md``.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Any

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.core.keys import (
    ADMIN_CREDENTIALS,
    ADMIN_INITIALIZED,
    ADMIN_RESET_TOKENS,
    reset_token_key,
)
from app.core.security import generate_reset_token, hash_password, verify_password
from app.schemas.auth import AdminRecord

logger = logging.getLogger(__name__)


class AlreadyInitializedError(RuntimeError):
    """Ya existe un administrador: el setup único no puede repetirse."""


class CredentialsNotFoundError(RuntimeError):
    """``admin:credentials`` no existe o está corrupto."""


class ResetOutcome(IntEnum):
    """Resultado de consumir un token de recuperación (códigos de Lua)."""

    SUCCESS = 1
    TOKEN_NOT_FOUND = -1
    CREDENTIALS_NOT_FOUND = -2
    ADMIN_MISMATCH = -3
    SESSION_VERSION_CHANGED = -4


@dataclass(frozen=True)
class ResetTokenInfo:
    """Datos públicos de un token de recuperación vigente."""

    admin_id: str
    expires_in: int
    expires_at: datetime


def _token_index_member(admin_id: str, token: str) -> str:
    """Miembro del set ``admin:reset_tokens``: ``<admin_id>|<token>``."""
    return f"{admin_id}|{token}"


# ----------------------------------------------------------------------
# Scripts Lua: operaciones atómicas (y seguras si Redis migrara a cluster)
# ----------------------------------------------------------------------
# KEYS[1] = admin:initialized
# KEYS[2] = admin:credentials
# ARGV[1] = documento JSON con las credenciales ya cifradas
#
# Devuelve 0 si ya hay una cuenta (y no escribe nada) o 1 tras crearla.
# La condición es idéntica a la de ``is_initialized()``: si el marcador
# existiera sin credenciales, el setup vuelve a estar disponible.
_LUA_SETUP = """
if redis.call('EXISTS', KEYS[1]) == 1 and redis.call('EXISTS', KEYS[2]) == 1 then
    return 0
end
redis.call('SET', KEYS[2], ARGV[1])
redis.call('SET', KEYS[1], ARGV[1])
return 1
"""

# KEYS[1] = reset_token:<token>
# KEYS[2] = admin:credentials
# KEYS[3] = admin:reset_tokens
# ARGV[1] = nuevo password_hash (bcrypt)
# ARGV[2] = updated_at ISO 8601
# ARGV[3] = token opaco
#
# Valida el token, rota la contraseña, incrementa session_version (lo que
# invalida los JWT emitidos antes del cambio) y consume el token.
_LUA_CONSUME_RESET = """
local raw_token = redis.call('GET', KEYS[1])
if not raw_token then
    return -1
end

local token_data = cjson.decode(raw_token)
local raw_creds = redis.call('GET', KEYS[2])
if not raw_creds then
    return -2
end

local creds = cjson.decode(raw_creds)

if token_data['admin_id'] ~= creds['admin_id'] then
    return -3
end

if tonumber(token_data['session_version']) ~= tonumber(creds['session_version']) then
    redis.call('DEL', KEYS[1])
    redis.call('SREM', KEYS[3], creds['admin_id'] .. '|' .. ARGV[3])
    return -4
end

creds['password_hash'] = ARGV[1]
creds['updated_at'] = ARGV[2]
creds['session_version'] = tonumber(creds['session_version']) + 1

redis.call('SET', KEYS[2], cjson.encode(creds))
redis.call('DEL', KEYS[1])
redis.call('SREM', KEYS[3], creds['admin_id'] .. '|' .. ARGV[3])
return 1
"""


class AuthService:
    """Operaciones de autenticación sobre Redis."""

    def __init__(self, redis: Redis, settings: Settings | None = None) -> None:
        self.redis = redis
        self.settings = settings if settings is not None else get_settings()

    # ------------------------------------------------------------------
    # Lectura de credenciales
    # ------------------------------------------------------------------
    async def get_credentials(self) -> AdminRecord | None:
        """Devuelve el registro del administrador o ``None`` si no existe."""
        raw = await self.redis.get(ADMIN_CREDENTIALS)
        if not raw:
            return None
        try:
            return AdminRecord.from_json(raw)
        except ValueError:
            logger.error("El documento %s no es válido", ADMIN_CREDENTIALS)
            raise CredentialsNotFoundError(f"{ADMIN_CREDENTIALS} está corrupto") from None

    async def is_initialized(self) -> bool:
        """``True`` si ya se creó la cuenta única de administrador.

        Se exigen *ambas* claves: si el marcador existiera sin credenciales
        (por ejemplo tras restaurar una copia parcial de Redis) el sistema
        se considera no inicializado y el setup vuelve a estar disponible.
        """
        initialized = await self.redis.exists(ADMIN_INITIALIZED)
        if not initialized:
            return False
        return bool(await self.redis.exists(ADMIN_CREDENTIALS))

    # ------------------------------------------------------------------
    # CU-01.2 — Setup único
    # ------------------------------------------------------------------
    async def create_initial_admin(
        self, *, username: str, email: str, password: str
    ) -> AdminRecord:
        """Crea la cuenta única del administrador.

        Raises:
            AlreadyInitializedError: ya existe un administrador.
        """
        now = datetime.now(timezone.utc)
        record = AdminRecord(
            admin_id=str(uuid.uuid4()),
            username=username,
            password_hash=hash_password(password, settings=self.settings),
            email=email,
            created_at=now,
            updated_at=now,
            session_version=1,
        )

        result = int(
            await self.redis.eval(_LUA_SETUP, 2, ADMIN_INITIALIZED, ADMIN_CREDENTIALS, record.to_json())
        )
        if result != 1:
            raise AlreadyInitializedError("El administrador ya fue creado")

        logger.info("Administrador inicial creado: %s <%s>", username, email)
        return record

    # ------------------------------------------------------------------
    # US-01 — Autenticación
    # ------------------------------------------------------------------
    async def authenticate(self, identifier: str, password: str) -> AdminRecord | None:
        """Valida las credenciales y devuelve el registro, o ``None``.

        No distingue entre "usuario inexistente" y "contraseña incorrecta":
        el endpoint responde siempre ``401 Credenciales inválidas``.
        """
        record = await self.get_credentials()
        if record is None:
            # Iguala tiempos de respuesta incluso sin cuenta creada.
            verify_password(password, None, settings=self.settings)
            return None

        if not record.matches_identifier(identifier):
            verify_password(password, None, settings=self.settings)
            return None

        if not verify_password(password, record.password_hash, settings=self.settings):
            logger.warning("Fallo de autenticación para %s", identifier)
            return None

        return record

    # ------------------------------------------------------------------
    # US-01.3 / US-10 — Recuperación de contraseña
    # ------------------------------------------------------------------
    async def create_reset_token(self, email: str) -> tuple[AdminRecord, str] | None:
        """Genera y persiste un token de recuperación con TTL nativo.

        Returns:
            ``(registro, token)`` si el correo está registrado; ``None`` si
            no existe. En ambos casos la respuesta HTTP al cliente es la
            misma, para no permitir enumerar cuentas.
        """
        record = await self.get_credentials()
        if record is None or record.email.casefold() != email.strip().casefold():
            return None

        token = generate_reset_token()
        ttl = self.settings.reset_token_ttl
        now = datetime.now(timezone.utc)
        payload = json.dumps(
            {
                "admin_id": record.admin_id,
                "email": record.email,
                "session_version": record.session_version,
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(seconds=ttl)).isoformat(),
            }
        )

        # SETEX: la expiración la aplica el propio Redis, sin tareas de limpieza.
        await self.redis.set(reset_token_key(token), payload, ex=ttl)
        await self._revoke_previous_reset_tokens(record.admin_id, keep=token)

        logger.info("Token de recuperación emitido para %s (ttl=%ss)", record.username, ttl)
        return record, token

    async def _revoke_previous_reset_tokens(self, admin_id: str, *, keep: str) -> None:
        """Deja un único enlace vigente por administrador.

        Recorre el set ``admin:reset_tokens`` y borra los tokens anteriores
        (cuya clave ``reset_token:<token>`` puede haber expirado ya por TTL
        sin que Redis haya limpiado el índice).
        """
        prefix = f"{admin_id}|"
        members = await self.redis.smembers(ADMIN_RESET_TOKENS)
        for member in members:
            if not member.startswith(prefix):
                continue
            previous_token = member[len(prefix) :]
            if previous_token == keep:
                continue
            await self.redis.delete(reset_token_key(previous_token))
            await self.redis.srem(ADMIN_RESET_TOKENS, member)
            logger.info("Token de recuperación anterior revocado")

        await self.redis.sadd(ADMIN_RESET_TOKENS, _token_index_member(admin_id, keep))
        await self.redis.persist(ADMIN_RESET_TOKENS)

    async def get_reset_token_info(self, token: str) -> ResetTokenInfo | None:
        """Devuelve la información de un token vigente, o ``None``.

        ``None`` significa que la clave no existe: expiró (Redis la borró
        por TTL), fue consumida, o nunca existió. Los tres casos producen
        el mismo mensaje al usuario.
        """
        if not token:
            return None

        key = reset_token_key(token)
        raw = await self.redis.get(key)
        if not raw:
            return None

        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Token de recuperación corrupto en Redis")
            await self.redis.delete(key)
            return None

        ttl = int(await self.redis.ttl(key))
        if ttl <= 0:
            # Carrera límite: expiró entre el GET y el TTL.
            return None

        expires_at = data.get("expires_at")
        if expires_at:
            parsed = datetime.fromisoformat(str(expires_at))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
        else:  # pragma: no cover - documento incompleto
            parsed = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        return ResetTokenInfo(
            admin_id=str(data.get("admin_id", "")),
            expires_in=ttl,
            expires_at=parsed,
        )

    async def consume_reset_token(self, token: str, new_password: str) -> ResetOutcome:
        """Rota la contraseña, consume el token e invalida sesiones previas."""
        new_hash = hash_password(new_password, settings=self.settings)
        now_iso = datetime.now(timezone.utc).isoformat()

        result = int(
            await self.redis.eval(
                _LUA_CONSUME_RESET,
                3,
                reset_token_key(token),
                ADMIN_CREDENTIALS,
                ADMIN_RESET_TOKENS,
                new_hash,
                now_iso,
                token,
            )
        )
        outcome = ResetOutcome(result)
        if outcome is ResetOutcome.SUCCESS:
            logger.info("Contraseña actualizada mediante token de recuperación")
        elif outcome is not ResetOutcome.TOKEN_NOT_FOUND:
            logger.warning("Consumo de token de recuperación rechazado: %s", outcome.name)
        return outcome

    # ------------------------------------------------------------------
    # Sesión
    # ------------------------------------------------------------------
    async def get_session_admin(self, admin_id: str, session_version: int) -> AdminRecord | None:
        """Valida un JWT contra el estado actual de Redis.

        Tras un cambio de contraseña ``session_version`` se incrementa y
        los JWT emitidos previamente dejan de ser válidos.
        """
        record = await self.get_credentials()
        if record is None:
            return None
        if record.admin_id != admin_id or record.session_version != session_version:
            return None
        return record

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    async def describe_state(self) -> dict[str, Any]:
        """Snapshot del estado de autenticación (diagnóstico)."""
        raw = await self.redis.get(ADMIN_CREDENTIALS)
        return {
            "initialized": await self.is_initialized(),
            "admin": None if not raw else json.loads(raw).get("username"),
            "reset_tokens_tracked": int(await self.redis.scard(ADMIN_RESET_TOKENS)),
            "reset_token_ttl": self.settings.reset_token_ttl,
        }
