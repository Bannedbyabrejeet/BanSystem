"""Esquemas Pydantic de la configuración de baneos, la lista blanca y el historial.

Cubre US-02 (umbral e intervalo de baneo), US-09 (ventana de tolerancia) y
US-08 (whitelist), y la Issue #7: IPs baneadas e historial.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core import constants
from app.core.network import PROTECTED_WHITELIST_ENTRIES, normalize_ip_or_network

#: Límites superiores defensivos. Evitan valores absurdos (por ejemplo un
#: baneo de siglos) sin restringir los casos de uso normales.
MAX_MAXRETRY = 1_000
MAX_BANTIME_MINUTES = 525_600  # 365 días
MAX_FINDTIME_MINUTES = 10_080  # 7 días


class BanSettings(BaseModel):
    """Parámetros persistidos en ``config:settings``."""

    model_config = ConfigDict(extra="forbid")

    maxretry: int = Field(
        strict=True,
        ge=1,
        le=MAX_MAXRETRY,
        description="Intentos fallidos permitidos antes de banear una IP.",
        examples=[5],
    )
    bantime: int = Field(
        strict=True,
        ge=1,
        le=MAX_BANTIME_MINUTES,
        description="Duración del baneo en minutos.",
        examples=[30],
    )
    findtime: int = Field(
        strict=True,
        ge=1,
        le=MAX_FINDTIME_MINUTES,
        description="Ventana de tolerancia en minutos para acumular intentos.",
        examples=[10],
    )


class WhitelistEntryRequest(BaseModel):
    """Cuerpo de ``POST /config/whitelist``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    entry: str = Field(
        min_length=1,
        max_length=64,
        description="Dirección IP o subred CIDR (IPv4 o IPv6).",
        examples=["192.168.1.10", "10.0.0.0/8", "::1"],
    )

    @field_validator("entry")
    @classmethod
    def _normalize_entry(cls, value: str) -> str:
        try:
            return normalize_ip_or_network(value)
        except ValueError as exc:
            raise ValueError(constants.INVALID_NETWORK_ENTRY) from exc


class WhitelistResponse(BaseModel):
    """Estado completo de la lista blanca."""

    entries: list[str] = Field(
        description="Direcciones y subredes ordenadas alfabéticamente."
    )
    protected_entries: list[str] = Field(
        default_factory=lambda: list(PROTECTED_WHITELIST_ENTRIES),
        description="Entradas que no pueden eliminarse.",
    )


class WhitelistMutationResponse(WhitelistResponse):
    """Respuesta de alta o baja de una entrada de la lista blanca."""

    message: str
    entry: str


# --- Issue #7: IPs baneadas e historial ---

class BanRecord(BaseModel):
    """Registro de una IP baneada en ``ips:banned``."""

    model_config = ConfigDict()

    ip: str = Field(
        description="Dirección IP baneada.",
        example="203.0.113.42",
    )
    banned_at: int = Field(
        description="Timestamp UNIX de cuándo fue baneada.",
        example=1725484800,
    )
    expires_at: int = Field(
        description="Timestamp UNIX cuando vence el baneo.",
        example=1725486600,
    )
    duration_min: int = Field(
        description="Duración en minutos del baneo.",
        example=30,
    )
    reason: str = Field(
        description="Motivo del baneo.",
        example="SSH brute force",
    )


class HistoryEntry(BaseModel):
    """Entrada del historial de baneos en ``ips:history``."""

    model_config = ConfigDict()

    ip: str = Field(
        description="Dirección IP involucrada.",
        example="203.0.113.42",
    )
    action: str = Field(
        description="Acción realizada.",
        example="banned",
    )
    banned_at: int = Field(
        description="Timestamp UNIX de cuándo se realizó la acción.",
        example=1725484800,
    )
    unbanned_at: int | None = Field(
        description="Timestamp UNIX cuando se desbaneó, o ``None`` si aún está baneada.",
        default=None,
        example=1725486600,
    )
    duration_min: int = Field(
        description="Duración en minutos asignada.",
        example=30,
    )
    reason: str = Field(
        description="Motivo de la acción.",
        example="SSH brute force",
    )
    unban_reason: str | None = Field(
        description="Motivo del desbaneo manual, si aplica.",
        default=None,
        example="manual",
    )
