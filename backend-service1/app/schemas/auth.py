"""Esquemas Pydantic (request/response) de la API de autenticación.

La política de contraseñas vive en ``app.core.security`` para que el
backend y el frontend apliquen exactamente la misma regla.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.security import password_policy_violations

USERNAME_PATTERN = r"^[A-Za-z0-9._-]+$"


def _ensure_utc(value: datetime) -> datetime:
    """Normaliza a UTC los timestamps leídos de Redis."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validate_password_pair(password: str, confirmation: str) -> None:
    """Valida coincidencia y política de seguridad de una contraseña."""
    if password != confirmation:
        raise ValueError("Las contraseñas no coinciden.")
    violations = password_policy_violations(password)
    if violations:
        raise ValueError(" ".join(violations))


class AdminRecord(BaseModel):
    """Documento almacenado en la clave ``admin:credentials`` de Redis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    admin_id: str
    username: str
    password_hash: str
    email: str
    created_at: datetime
    updated_at: datetime
    session_version: int = 1

    @field_validator("created_at", "updated_at")
    @classmethod
    def _normalize_timestamps(cls, value: datetime) -> datetime:
        return _ensure_utc(value)

    def matches_identifier(self, identifier: str) -> bool:
        """Compara usuario o correo sin distinguir mayúsculas."""
        candidate = identifier.strip().casefold()
        return candidate in {self.username.casefold(), self.email.casefold()}

    def to_json(self) -> str:
        """Serializa el registro a JSON (lo que se guarda en Redis)."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "AdminRecord":
        return cls.model_validate_json(raw)


class AdminPublic(BaseModel):
    """Datos del administrador que el frontend puede mostrar."""

    admin_id: str
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    session_version: int

    @classmethod
    def from_record(cls, record: AdminRecord) -> "AdminPublic":
        return cls(
            admin_id=record.admin_id,
            username=record.username,
            email=record.email,  # type: ignore[arg-type]  (validado por AdminPublic)
            created_at=record.created_at,
            updated_at=record.updated_at,
            session_version=record.session_version,
        )


# ----------------------------------------------------------------------
# Modelos de request
# ----------------------------------------------------------------------
class SetupRequest(BaseModel):
    """Cuerpo de ``POST /api/v1/auth/setup`` (CU-01.2)."""

    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=USERNAME_PATTERN,
        description="Solo letras, números, punto, guion y guion bajo.",
        examples=["admin"],
    )
    email: EmailStr = Field(
        description="Correo donde se recibirán los enlaces de recuperación.",
        examples=["admin@example.com"],
    )
    password: str = Field(min_length=1, max_length=256, repr=False)
    password_confirm: str = Field(min_length=1, max_length=256, repr=False)

    @model_validator(mode="after")
    def _check_password(self) -> "SetupRequest":
        _validate_password_pair(self.password, self.password_confirm)
        return self


class LoginRequest(BaseModel):
    """Cuerpo de ``POST /api/v1/auth/login`` (US-01)."""

    identifier: str = Field(
        min_length=1,
        max_length=254,
        description="Nombre de usuario o correo electrónico registrado.",
        examples=["admin"],
    )
    password: str = Field(min_length=1, max_length=256, repr=False)


class ForgotPasswordRequest(BaseModel):
    """Cuerpo de ``POST /api/v1/auth/forgot-password`` (US-01.3)."""

    email: EmailStr = Field(
        description="Correo electrónico registrado.",
        examples=["admin@example.com"],
    )


class ResetPasswordRequest(BaseModel):
    """Cuerpo de ``POST /api/v1/auth/reset-password`` (US-01.3)."""

    token: str = Field(
        min_length=20,
        max_length=256,
        description="Token recibido en el enlace de recuperación.",
        examples=["k3Yb1s8Qn0Zx7Ww2pL4mT9cR6hJ5vA1dF0gN3uO8eK7i"],
    )
    new_password: str = Field(min_length=1, max_length=256, repr=False)
    confirm_password: str = Field(min_length=1, max_length=256, repr=False)

    @model_validator(mode="after")
    def _check_password(self) -> "ResetPasswordRequest":
        _validate_password_pair(self.new_password, self.confirm_password)
        return self


# ----------------------------------------------------------------------
# Modelos de response
# ----------------------------------------------------------------------
class AuthStatusResponse(BaseModel):
    """Respuesta de ``GET /api/v1/auth/status``."""

    initialized: bool = Field(
        description="``true`` cuando ya existe un administrador registrado en Redis."
    )


class MessageResponse(BaseModel):
    """Respuesta genérica con un mensaje para mostrar en la interfaz."""

    message: str
    success: bool = True


class TokenResponse(BaseModel):
    """Respuesta de ``POST /api/v1/auth/login``."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Validez del token en segundos.", examples=[1800])
    admin: AdminPublic


class ForgotPasswordResponse(BaseModel):
    """Respuesta de ``POST /api/v1/auth/forgot-password``.

    Es idéntica exista o no el correo registrado: no revela información
    sobre cuentas (anti enumeración).
    """

    message: str
    email: EmailStr
    expires_in: int = Field(description="Validez del enlace en segundos.", examples=[900])


class VerifyResetTokenResponse(BaseModel):
    """Respuesta de ``GET /api/v1/auth/verify-reset-token/{token}``."""

    valid: bool = True
    expires_in: int = Field(
        description="Segundos restantes antes de que Redis elimine el token por TTL."
    )
    expires_at: datetime


class SessionResponse(BaseModel):
    """Respuesta de ``GET /api/v1/auth/me``: sesión validada contra Redis."""

    admin: AdminPublic
    role: str
    token_expires_at: datetime
