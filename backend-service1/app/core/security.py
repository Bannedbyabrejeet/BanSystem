"""Primitivas criptográficas del Servicio 1.

* Contraseñas: **Argon2id** (coste configurable: iteraciones, memoria en
  KiB y paralelismo).
* Tokens de recuperación: 256 bits de entropía con ``secrets.token_urlsafe``.
* Sesión: **JWT HS256** firmado con ``JWT_SECRET`` que incluye ``iss``,
  ``aud``, ``sub``, ``jti``, ``iat``, ``nbf``, ``exp``, el rol y la
  ``session_version`` del administrador.

Se usa ``argon2-cffi``, binding oficial de la implementación de referencia
en C. Argon2id es el ganador del Password Hashing Competition y el modo
recomendado por OWASP: combina los caminos 1i y 1d de Argon2, de modo que
resiste tanto ataques masivos de GPU como ataques por canal lateral en
caché.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import argon2
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

#: Argon2id no trunca la entrada como hacía bcrypt (límite de 72 bytes),
#: pero se acota la longitud de la contraseña como defensa contra
#: agotamiento de CPU y memoria durante el hashing.
PASSWORD_MAX_BYTES = 1024
PASSWORD_MIN_LENGTH = 12
#: Bytes de entropía del token opaco de recuperación (256 bits).
RESET_TOKEN_BYTES = 32

#: Contraseñas triviales bloqueadas además de las reglas de formato.
WEAK_PASSWORDS: frozenset[str] = frozenset(
    {
        "administrador",
        "bannedbyabrejeet",
        "changeme12345",
        "contrasena1234",
        "password1234",
        "password12345",
        "qwertyuiop123",
        "administrador1",
        "adminadmin1234",
        "1234567890123",
    }
)


class SecurityError(Exception):
    """Error base de las utilidades de seguridad."""


class PasswordPolicyError(SecurityError):
    """La contraseña no cumple la política de seguridad."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = list(violations)
        super().__init__("; ".join(self.violations))


class TokenError(SecurityError):
    """Error base al trabajar con JWT."""


class InvalidTokenError(TokenError):
    """El JWT es inválido: firma, emisor, audiencia o claims incorrectos."""


class ExpiredTokenError(TokenError):
    """El JWT venció (``exp``) o todavía no es válido (``nbf``)."""


@dataclass(frozen=True)
class TokenPayload:
    """Claims relevantes extraídos de un JWT verificado."""

    subject: str
    role: str
    session_version: int
    token_id: str
    issued_at: datetime
    expires_at: datetime


# ----------------------------------------------------------------------
# Política de contraseñas
# ----------------------------------------------------------------------
def password_policy_violations(password: str) -> list[str]:
    """Devuelve la lista de reglas incumplidas (vacía si cumple todo)."""
    violations: list[str] = []

    if len(password) < PASSWORD_MIN_LENGTH:
        violations.append(f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")
    if not any(char.isupper() for char in password):
        violations.append("La contraseña debe incluir al menos una letra mayúscula.")
    if not any(char.islower() for char in password):
        violations.append("La contraseña debe incluir al menos una letra minúscula.")
    if not any(char.isdigit() for char in password):
        violations.append("La contraseña debe incluir al menos un número.")

    size_in_bytes = len(password.encode("utf-8"))
    if size_in_bytes > PASSWORD_MAX_BYTES:
        violations.append(
            f"La contraseña no puede superar {PASSWORD_MAX_BYTES} bytes "
            f"(actual: {size_in_bytes} bytes)."
        )

    normalized = password.strip().casefold()
    if normalized in WEAK_PASSWORDS:
        violations.append("La contraseña es demasiado común. Elegí una más difícil de adivinar.")

    return violations


def assert_password_policy(password: str) -> None:
    """Lanza :class:`PasswordPolicyError` si la contraseña es insegura."""
    violations = password_policy_violations(password)
    if violations:
        raise PasswordPolicyError(violations)


# ----------------------------------------------------------------------
# Hash de contraseñas
# ----------------------------------------------------------------------
def _build_password_hasher(
    *,
    time_cost: int | None = None,
    memory_cost_kib: int | None = None,
    parallelism: int | None = None,
    settings: Settings | None = None,
) -> PasswordHasher:
    """Crea un ``PasswordHasher`` Argon2id con los parámetros indicados.

    Los valores no provistos se toman de la configuración activa.
    """
    active_settings = settings if settings is not None else get_settings()
    return PasswordHasher(
        time_cost=(
            time_cost if time_cost is not None else active_settings.argon2_time_cost
        ),
        memory_cost=(
            memory_cost_kib
            if memory_cost_kib is not None
            else active_settings.argon2_memory_cost_kib
        ),
        parallelism=(
            parallelism
            if parallelism is not None
            else active_settings.argon2_parallelism
        ),
        hash_len=32,
        salt_len=16,
        type=argon2.Type.ID,
    )


def hash_password(
    password: str,
    *,
    time_cost: int | None = None,
    memory_cost_kib: int | None = None,
    parallelism: int | None = None,
    settings: Settings | None = None,
) -> str:
    """Devuelve el hash Argon2id de ``password`` (nunca se guarda en claro)."""
    size_in_bytes = len(password.encode("utf-8"))
    if size_in_bytes > PASSWORD_MAX_BYTES:
        raise PasswordPolicyError(
            [
                f"La contraseña no puede superar {PASSWORD_MAX_BYTES} bytes "
                f"(actual: {size_in_bytes} bytes)."
            ]
        )

    hasher = _build_password_hasher(
        time_cost=time_cost,
        memory_cost_kib=memory_cost_kib,
        parallelism=parallelism,
        settings=settings,
    )
    return hasher.hash(password)


@lru_cache(maxsize=8)
def _timing_equalizer_hash(
    time_cost: int, memory_cost_kib: int, parallelism: int
) -> str:
    """Hash señuelo para igualar tiempos de respuesta en login fallido."""
    hasher = _build_password_hasher(
        time_cost=time_cost,
        memory_cost_kib=memory_cost_kib,
        parallelism=parallelism,
    )
    return hasher.hash("bannedbyabrejeet-timing-equalizer")


def verify_password(
    password: str, password_hash: str | None, *, settings: Settings | None = None
) -> bool:
    """Verifica una contraseña contra su hash Argon2id.

    Si el hash no existe o está corrupto se ejecuta igualmente una
    verificación contra un hash señuelo: así el tiempo de respuesta no
    revela si el usuario existe.
    """
    active_settings = settings if settings is not None else get_settings()
    hasher = _build_password_hasher(settings=active_settings)
    if not password_hash:
        try:
            hasher.verify(
                _timing_equalizer_hash(
                    active_settings.argon2_time_cost,
                    active_settings.argon2_memory_cost_kib,
                    active_settings.argon2_parallelism,
                ),
                password,
            )
        except (VerificationError, ValueError, TypeError):  # pragma: no cover - defensivo
            pass
        return False

    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, ValueError, TypeError):
        logger.warning("Hash de contraseña inválido o corrupto en Redis")
        return False


# ----------------------------------------------------------------------
# Tokens de recuperación
# ----------------------------------------------------------------------
def generate_reset_token() -> str:
    """Genera un token opaco, aleatorio y URL-safe de 256 bits."""
    return secrets.token_urlsafe(RESET_TOKEN_BYTES)


# ----------------------------------------------------------------------
# JWT de sesión
# ----------------------------------------------------------------------
def create_access_token(
    *,
    subject: str,
    session_version: int,
    role: str,
    expires_minutes: int | None = None,
    settings: Settings | None = None,
) -> tuple[str, int]:
    """Crea un JWT de acceso.

    Returns:
        Tupla ``(token, expires_in_seconds)``.
    """
    active_settings = settings or get_settings()
    lifetime_minutes = (
        expires_minutes
        if expires_minutes is not None
        else active_settings.jwt_access_token_expire_minutes
    )
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=lifetime_minutes)

    payload: dict[str, object] = {
        "sub": subject,
        "iss": active_settings.jwt_issuer,
        "aud": active_settings.jwt_audience,
        "role": role,
        "ver": session_version,
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(
        payload,
        active_settings.jwt_secret.get_secret_value(),
        algorithm=active_settings.jwt_algorithm,
    )
    return token, int(lifetime_minutes * 60)


def decode_access_token(
    token: str, *, settings: Settings | None = None
) -> TokenPayload:
    """Verifica la firma y los claims de un JWT de acceso.

    Raises:
        ExpiredTokenError: el token venció o aún no es válido.
        InvalidTokenError: firma, emisor, audiencia o estructura inválidos.
    """
    active_settings = settings or get_settings()
    options = {"require": ["exp", "iat", "nbf", "sub", "iss", "aud", "jti"]}

    try:
        claims = jwt.decode(
            token,
            active_settings.jwt_secret.get_secret_value(),
            algorithms=[active_settings.jwt_algorithm],
            audience=active_settings.jwt_audience,
            issuer=active_settings.jwt_issuer,
            options=options,
        )
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("El token de sesión expiró") from exc
    except jwt.ImmatureSignatureError as exc:
        raise ExpiredTokenError("El token de sesión todavía no es válido") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError(str(exc)) from exc

    return TokenPayload(
        subject=str(claims["sub"]),
        role=str(claims.get("role", "")),
        session_version=int(claims.get("ver", 0)),
        token_id=str(claims["jti"]),
        issued_at=datetime.fromtimestamp(int(claims["iat"]), tz=timezone.utc),
        expires_at=datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc),
    )
