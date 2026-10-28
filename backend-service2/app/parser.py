"""Parser de logs SSH (``auth.log`` / ``secure``).

Reconoce los formatos más habituales de OpenSSH y PAM:

* ``Failed password for root from 203.0.113.42 port 4242 ssh2``
* ``Failed publickey for invalid user admin from ...``
* ``Accepted password/publickey/keyboard-interactive for ...``
* ``pam_unix(sshd:auth): authentication failure; ... rhost=...``
* ``Invalid user ...``, ``Connection closed by ...`` y ``maximum
  authentication attempts exceeded``.

Las líneas auxiliares se marcan con ``countable=False``: OpenSSH emite varias
líneas por un mismo intento fallido y contarlas todas inflaría el umbral. Solo
las líneas canónicas de ``Failed ...`` (y no sus acompañantes) incrementan el
contador del motor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from typing import Final

from app.models import Outcome, SSHEvent

# ----------------------------------------------------------------------
# Patrones de eventos
# ----------------------------------------------------------------------
_FAILED_AUTH: Final[re.Pattern[str]] = re.compile(
    r"Failed\s+(?P<method>password|publickey|keyboard-interactive(?:/pam)?|"
    r"gssapi-with-mic|hostbased)\s+for\s+"
    r"(?:(?:invalid|unknown)\s+user\s+)?(?P<user>\S+)\s+from\s+"
    r"(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
    re.IGNORECASE,
)
_ACCEPTED_AUTH: Final[re.Pattern[str]] = re.compile(
    r"Accepted\s+(?P<method>password|publickey|keyboard-interactive(?:/pam)?|"
    r"gssapi-with-mic|hostbased)\s+for\s+(?P<user>\S+)\s+from\s+"
    r"(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
    re.IGNORECASE,
)
_MAX_ATTEMPTS: Final[re.Pattern[str]] = re.compile(
    r"maximum authentication attempts exceeded for\s+"
    r"(?:(?:invalid|unknown)\s+user\s+)?(?P<user>\S+)\s+from\s+"
    r"(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
    re.IGNORECASE,
)
_PAM_FAILURE: Final[re.Pattern[str]] = re.compile(
    r"pam_unix\(sshd:auth\):\s+authentication failure;.*?"
    r"\brhost=(?P<ip>\S+?)(?:\s+user=(?P<user>\S+))?(?:\s|$)",
    re.IGNORECASE,
)
_CONNECTION_CLOSED: Final[re.Pattern[str]] = re.compile(
    r"Connection closed by\s+(?:authenticating user|invalid user)\s+"
    r"(?P<user>\S+)\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
    re.IGNORECASE,
)
_INVALID_USER: Final[re.Pattern[str]] = re.compile(
    r"Invalid user\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)",
    re.IGNORECASE,
)

_ISO_TIMESTAMP: Final[re.Pattern[str]] = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s"
)
_SYSLOG_TIMESTAMP: Final[re.Pattern[str]] = re.compile(
    r"^(?P<ts>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s"
)


@dataclass(frozen=True, slots=True)
class _Rule:
    pattern: re.Pattern[str]
    outcome: Outcome
    event_type: str
    countable: bool


# El orden importa: las reglas específicas van antes que ``Invalid user``,
# que también aparece como texto dentro de otras líneas.
_RULES: Final[tuple[_Rule, ...]] = (
    _Rule(_ACCEPTED_AUTH, Outcome.SUCCESS, "accepted", True),
    _Rule(_FAILED_AUTH, Outcome.FAILED, "failed", True),
    _Rule(_MAX_ATTEMPTS, Outcome.FAILED, "max_attempts", False),
    _Rule(_PAM_FAILURE, Outcome.FAILED, "pam_failure", False),
    _Rule(_CONNECTION_CLOSED, Outcome.FAILED, "connection_closed", False),
    _Rule(_INVALID_USER, Outcome.FAILED, "invalid_user", False),
)


def _as_reference(reference: datetime | int | float | None) -> datetime:
    """Normaliza la referencia temporal usada para años y líneas sin fecha."""
    if reference is None:
        return datetime.now(timezone.utc)
    if isinstance(reference, datetime):
        if reference.tzinfo is None:
            return reference.replace(tzinfo=timezone.utc)
        return reference.astimezone(timezone.utc)
    return datetime.fromtimestamp(reference, tz=timezone.utc)


def _parse_timestamp(line: str, reference: datetime) -> int:
    """Extrae el timestamp de la línea; si no existe, usa la referencia."""
    iso_match = _ISO_TIMESTAMP.match(line)
    if iso_match:
        raw = iso_match.group("ts").replace("Z", "+00:00")
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())

    syslog_match = _SYSLOG_TIMESTAMP.match(line)
    if syslog_match:
        parsed = datetime.strptime(
            syslog_match.group("ts"), "%b %d %H:%M:%S"
        ).replace(year=reference.year, tzinfo=timezone.utc)
        # Un log de diciembre procesado el 1 de enero pertenece al año anterior.
        if parsed - reference > timedelta(days=2):
            parsed = parsed.replace(year=reference.year - 1)
        return int(parsed.timestamp())

    return int(reference.timestamp())


class SSHParser:
    """Convierte líneas de log en :class:`~app.models.SSHEvent`."""

    def parse(
        self, line: str, reference: datetime | int | float | None = None
    ) -> SSHEvent | None:
        """Parsea una línea y devuelve el evento, o ``None`` si no es SSH.

        Args:
            line: Línea cruda del archivo de logs (con o sin ``\\n``).
            reference: Fecha usada para resolver el año de los logs syslog y
                las líneas sin timestamp. Facilita pruebas deterministas.
        """
        text = (line or "").rstrip("\r\n")
        if not text.strip():
            return None

        reference_dt = _as_reference(reference)
        timestamp = _parse_timestamp(text, reference_dt)

        for rule in _RULES:
            match = rule.pattern.search(text)
            if match is None:
                continue

            normalized_ip = _normalize_ip(match.group("ip"))
            if normalized_ip is None:
                return None

            method = match.groupdict().get("method")
            event_type = rule.event_type
            if method:
                event_type = f"{rule.event_type}_{method.lower().replace('/', '_')}"

            return SSHEvent(
                timestamp=timestamp,
                ip=normalized_ip,
                username=_clean_user(match.groupdict().get("user")),
                outcome=rule.outcome,
                event_type=event_type,
                raw_line=text,
                countable=rule.countable,
                port=_as_port(match.groupdict().get("port")),
            )

        return None


def _normalize_ip(raw: str | None) -> str | None:
    """Valida y normaliza una IP; devuelve ``None`` si el texto no lo es."""
    if not raw:
        return None
    candidate = raw.strip("[]")
    try:
        return str(ip_address(candidate))
    except ValueError:
        return None


def _clean_user(raw: str | None) -> str | None:
    if not raw:
        return None
    return raw.strip().strip("'\"")


def _as_port(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None
