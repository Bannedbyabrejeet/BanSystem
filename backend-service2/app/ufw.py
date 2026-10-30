"""Ejecutor de reglas UFW para el Servicio 2 (Issue #8).

El motor de seguridad decide *qué* IP bloquear; este módulo traduce esa
decisión a comandos del firewall del host. Se usa ``subprocess`` con una
lista de argumentos (nunca ``shell=True``) y se valida la IP con
``ipaddress`` antes de construir la orden, de modo que una línea de log
manipulada no pueda inyectar comandos.

Comandos generados (los mismos que documenta el enunciado):

* Bloqueo: ``ufw deny from <IP> to any port 22``
* Desbloqueo: ``ufw delete deny from <IP> to any port 22``

En desarrollo se puede activar ``UFW_DRY_RUN=true`` para ver los comandos
sin modificar el firewall.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from ipaddress import ip_address

logger = logging.getLogger(__name__)

#: Firma mínima compatible con ``subprocess.run`` (inyectable en pruebas).
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class UfwError(RuntimeError):
    """UFW no pudo aplicar o eliminar una regla."""


@dataclass(frozen=True, slots=True)
class UfwCommandResult:
    """Resultado de un comando UFW (real o simulado)."""

    command: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def normalize_ip(ip: str) -> str:
    """Valida y normaliza una IP. Rechaza redes CIDR.

    UFW acepta IPv4 e IPv6; ``ipaddress`` devuelve la forma canónica para
    que ``2001:0db8::1`` y ``2001:db8::1`` apunten a la misma regla.
    """
    try:
        return str(ip_address(ip.strip()))
    except ValueError as exc:
        raise ValueError(f"IP inválida para UFW: {ip!r}") from exc


class UfwExecutor:
    """Ejecuta reglas de bloqueo/desbloqueo con UFW."""

    def __init__(
        self,
        *,
        binary: str = "ufw",
        use_sudo: bool = True,
        ssh_port: int = 22,
        timeout: float = 10.0,
        dry_run: bool = False,
        runner: CommandRunner | None = None,
    ) -> None:
        self.binary = binary
        self.use_sudo = use_sudo
        self.ssh_port = ssh_port
        self.timeout = timeout
        self.dry_run = dry_run
        self._runner = runner or subprocess.run

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def block(self, ip: str) -> UfwCommandResult:
        """Agrega ``deny from <IP> to any port <ssh_port>``."""
        return self._execute(self._rule("deny", ip))

    def unblock(self, ip: str) -> UfwCommandResult:
        """Elimina la regla de bloqueo de la IP.

        Si UFW informa que la regla no existe, la operación se considera
        exitosa: el objetivo (que la IP no esté bloqueada) ya se cumple.
        """
        return self._execute(self._rule("delete deny", ip), allow_missing=True)

    def is_blocked(self, ip: str) -> bool:
        """Consulta ``ufw status`` y busca una regla DENY para la IP.

        Se usa en la reconciliación de arranque para no duplicar reglas si
        el proceso se reinició con el baneo todavía vigente en Redis.
        """
        normalized = normalize_ip(ip)
        result = self._execute(["status"], check=False)
        if not result.succeeded:
            return False
        for line in result.stdout.splitlines():
            if "DENY" in line.upper() and normalized in line:
                return True
        return False

    # ------------------------------------------------------------------
    # Construcción y ejecución
    # ------------------------------------------------------------------
    def _rule(self, action: str, ip: str) -> list[str]:
        normalized = normalize_ip(ip)
        return [
            *action.split(),
            "from",
            normalized,
            "to",
            "any",
            "port",
            str(self.ssh_port),
        ]

    def _command(self, args: Sequence[str]) -> list[str]:
        prefix = ["sudo", "-n"] if self.use_sudo else []
        return [*prefix, self.binary, *args]

    def _execute(
        self, args: Sequence[str], *, allow_missing: bool = False, check: bool = True
    ) -> UfwCommandResult:
        command = self._command(args)
        rendered = shlex.join(command)

        if self.dry_run:
            logger.info("[UFW dry-run] %s", rendered)
            return UfwCommandResult(tuple(command), 0, stdout="(dry-run)")

        logger.info("Ejecutando UFW: %s", rendered)
        try:
            completed = self._runner(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise UfwError(f"No se pudo ejecutar {rendered}: {exc}") from exc

        result = UfwCommandResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )

        if result.succeeded:
            return result

        combined = f"{result.stdout}\n{result.stderr}"
        if allow_missing and "could not delete non-existent rule" in combined.lower():
            logger.info("UFW: la regla de %s ya no existía", rendered)
            return result

        if not check:
            return result

        detail = result.stderr.strip() or result.stdout.strip() or "sin salida"
        raise UfwError(
            f"UFW falló con código {result.returncode} al ejecutar {rendered}: {detail}"
        )
