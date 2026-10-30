"""Validación del JWT del Servicio 1 para la API de telemetría (Issue #9).

El Frontend B reutiliza la sesión del Frontend A: envía el mismo Bearer token
que emitió el Servicio 1. El Servicio 2 verifica la firma, emisor, audiencia,
expiración y ``session_version`` contra ``admin:credentials`` en Redis, de
modo que un cambio de contraseña revoca también el acceso a la telemetría.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import jwt
from redis import Redis

from app.config import Settings
from app.keys import ADMIN_CREDENTIALS

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """El token falta, es inválido o la sesión fue revocada."""


@dataclass(frozen=True, slots=True)
class AuthIdentity:
    """Administrador autenticado que realiza la petición."""

    subject: str
    username: str
    role: str
    session_version: int
    expires_at: int


def _decode(token: str, settings: Settings) -> dict[str, object]:
    options = {"require": ["exp", "iat", "nbf", "sub", "iss", "aud", "jti"]}
    try:
        return jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options=options,
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("La sesión expiró") from exc
    except jwt.ImmatureSignatureError as exc:
        raise AuthError("La sesión todavía no es válida") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Token de sesión inválido") from exc


def authenticate(redis: Redis, settings: Settings, token: str) -> AuthIdentity:
    """Valida el JWT y lo contrasta con la sesión persistida en Redis."""
    if not token:
        raise AuthError("Falta el token de sesión")

    claims = _decode(token, settings)
    raw = redis.get(ADMIN_CREDENTIALS)
    if raw is None:
        raise AuthError("No hay un administrador registrado")

    try:
        credentials = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Credenciales corruptas en Redis: %s", exc)
        raise AuthError("Las credenciales del administrador están corruptas") from exc

    token_version = int(claims.get("ver", 0))
    current_version = int(credentials.get("session_version", 0))
    if token_version != current_version:
        raise AuthError("La sesión fue revocada")

    subject = str(claims.get("sub", ""))
    if not subject or subject != str(credentials.get("admin_id", "")):
        raise AuthError("La sesión no corresponde al administrador actual")

    return AuthIdentity(
        subject=subject,
        username=str(credentials.get("username", "admin")),
        role=str(claims.get("role", "")),
        session_version=token_version,
        expires_at=int(claims.get("exp", 0)),
    )
