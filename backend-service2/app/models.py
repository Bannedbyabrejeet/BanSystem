"""Modelos de dominio del lector de logs y del motor de seguridad."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Outcome(str, Enum):
    """Resultado de un intento de autenticación SSH."""

    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SSHEvent:
    """Evento estructurado extraído de una línea de log.

    Attributes:
        timestamp: Instante del evento como UNIX epoch (segundos).
        ip: IP de origen ya validada.
        username: Usuario SSH involucrado, si aparece en el log.
        outcome: Éxito o fallo de autenticación.
        event_type: Tipo concreto (``failed_password``, ``accepted_publickey``…).
        raw_line: Línea original, útil para auditoría y el futuro visor.
        countable: ``False`` para líneas auxiliares que no deben sumar al
            contador (por ejemplo ``Invalid user`` o ``PAM authentication
            failure``), evitando contar dos veces un mismo intento.
        port: Puerto de origen cuando está disponible.
    """

    timestamp: int
    ip: str
    username: str | None
    outcome: Outcome
    event_type: str
    raw_line: str
    countable: bool = True
    port: int | None = None


@dataclass(frozen=True, slots=True)
class BanSettings:
    """Parámetros vigentes leídos de ``config:settings``."""

    maxretry: int = 5
    bantime: int = 30
    findtime: int = 10

    @property
    def findtime_seconds(self) -> int:
        """Ventana deslizante expresada en segundos."""
        return self.findtime * 60


class EngineAction(str, Enum):
    """Decisión tomada por el motor para un evento."""

    COUNTED = "counted"
    BAN_REQUIRED = "ban_required"
    WHITELISTED = "whitelisted"
    ALREADY_BANNED = "already_banned"
    SUCCESS = "success"
    NOT_COUNTABLE = "not_countable"


@dataclass(frozen=True, slots=True)
class EngineDecision:
    """Resultado de evaluar un evento contra la configuración de Redis."""

    action: EngineAction
    ip: str
    attempts_in_window: int = 0
    maxretry: int = 0
    findtime_seconds: int = 0

    @property
    def should_ban(self) -> bool:
        """``True`` cuando se alcanzó el umbral y el siguiente paso es UFW."""
        return self.action is EngineAction.BAN_REQUIRED
