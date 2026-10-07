"""Primitivas criptográficas del Servicio 1.

* Contraseñas: **bcrypt** (coste configurable, mínimo 8, por defecto 12).
* Tokens de recuperación: 256 bits de entropía con ``secrets.token_urlsafe``.
* Sesión: **JWT HS256** firmado con ``JWT_SECRET`` que incluye ``iss``,
  ``aud``, ``sub``, ``jti``, ``iat``, ``nbf``, ``exp``, el rol y la
  ``session_version`` del administrador.

Se usa la librería ``bcrypt`` de forma directa en lugar de ``passlib``:
``passlib`` 1.7.4 (última versión) no es compatible con ``bcrypt >= 4.1``
y su soporte está congelado. El algoritmo y el resultado son los mismos.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import bcrypt
import jwt

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

#: bcrypt trunca silenciosamente las contraseñas de más de 72 bytes.
BCRYPT_MAX_PASSWORD_BYTES = 72
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
    if size_in_bytes > BCRYPT_MAX_PASSWORD_BYTES:
        violations.append(
            f"La contraseña no puede superar {BCRYPT_MAX_PASSWORD_BYTES} bytes "
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
def hash_password(password: str, *, rounds: int | None = None, settings: Settings | None = None) -> str:
    """Devuelve el hash bcrypt de ``password`` (nunca se guarda en claro)."""
    size_in_bytes = len(password.encode("utf-8"))
    if size_in_bytes > BCRYPT_MAX_PASSWORD_BYTES:
        raise PasswordPolicyError(
            [
                f"La contraseña no puede superar {BCRYPT_MAX_PASSWORD_BYTES} bytes "
                f"(actual: {size_in_bytes} bytes)."
            ]
        )

    active_settings = settings if settings is not None else get_settings()
    cost = rounds if rounds is not None else active_settings.bcrypt_rounds
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=cost))
    return hashed.decode("utf-8")


@lru_cache(maxsize=1)
def _timing_equalizer_hash(rounds: int) -> str:
    """Hash señuelo para igualar tiempos de respuesta en login fallido."""
    return bcrypt.hashpw(b"bannedbyabrejeet-timing-equalizer", bcrypt.gensalt(rounds=rounds)).decode(
        "utf-8"
    )


def verify_password(
    password: str, password_hash: str | None, *, settings: Settings | None = None
) -> bool:
    """Verifica una contraseña contra su hash bcrypt.

    Si el hash no existe o está corrupto se ejecuta igualmente un
    ``checkpw`` contra un hash señuelo: así el tiempo de respuesta no
    revela si el usuario existe.
    """
    active_settings = settings if settings is not None else get_settings()
    if not password_hash:
        try:
            bcrypt.checkpw(
                password.encode("utf-8"),
                _timing_equalizer_hash(active_settings.bcrypt_rounds).encode("utf-8"),
            )
        except ValueError:  # pragma: no cover - defensivo
            pass
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
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
