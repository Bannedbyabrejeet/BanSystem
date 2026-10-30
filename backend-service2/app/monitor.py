"""Bucle que conecta el tailer, el parser, el motor y UFW."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterable

from app.bans import BanError, BanService
from app.engine import SecurityEngine
from app.models import EngineAction, EngineDecision, SSHEvent
from app.parser import SSHParser
from app.tailer import LogTailer

logger = logging.getLogger(__name__)


class LogMonitor:
    """Procesa líneas nuevas, aplica el motor y ejecuta el baneo en UFW."""

    def __init__(
        self,
        tailer: LogTailer,
        parser: SSHParser,
        engine: SecurityEngine,
        *,
        poll_interval: float = 0.5,
        ban_service: BanService | None = None,
        maintenance_interval: float = 5.0,
    ) -> None:
        self.tailer = tailer
        self.parser = parser
        self.engine = engine
        self.poll_interval = poll_interval
        self.ban_service = ban_service
        self.maintenance_interval = maintenance_interval
        self._last_maintenance = 0.0

    # ------------------------------------------------------------------
    # Lectura de eventos
    # ------------------------------------------------------------------
    def process_available(self) -> list[EngineDecision]:
        """Procesa todos los eventos disponibles sin bloquear."""
        decisions: list[EngineDecision] = []
        for line in self.tailer.read_available():
            event = self.parser.parse(line)
            if event is None:
                continue
            decision = self.engine.process(event)
            self._log(event, decision)
            self._apply_ban(decision)
            decisions.append(decision)
        return decisions

    def run(self, stop_event: threading.Event | None = None) -> None:
        """Sondea el archivo hasta que se pida detener el proceso."""
        logger.info("Motor de seguridad escuchando %s", self.tailer.path)
        try:
            while stop_event is None or not stop_event.is_set():
                self.process_available()
                self.run_maintenance()
                if stop_event is None:
                    time.sleep(self.poll_interval)
                else:
                    stop_event.wait(self.poll_interval)
        finally:
            self.tailer.close()
            logger.info("Lector de logs detenido")

    def process_lines(self, lines: Iterable[str]) -> list[EngineDecision]:
        """Atajo para pruebas o para alimentar líneas desde otra fuente."""
        decisions: list[EngineDecision] = []
        for line in lines:
            event = self.parser.parse(line)
            if event is None:
                continue
            decision = self.engine.process(event)
            self._log(event, decision)
            self._apply_ban(decision)
            decisions.append(decision)
        return decisions

    # ------------------------------------------------------------------
    # UFW y expiración
    # ------------------------------------------------------------------
    def _apply_ban(self, decision: EngineDecision) -> None:
        """Ejecuta el bloqueo cuando el motor lo pide (US-04)."""
        if not decision.should_ban or self.ban_service is None:
            return

        try:
            record = self.ban_service.ban(decision.ip)
        except BanError as exc:
            logger.critical(
                "BLOQUEO FALLIDO para %s: %s", decision.ip, exc
            )
            return

        logger.warning(
            "UFW: regla activa para %s hasta %s (%d min)",
            record.ip,
            record.expires_at,
            record.duration_min,
        )

    def run_maintenance(self, *, force: bool = False) -> list[str]:
        """Desbanea las IPs vencidas cada ``maintenance_interval`` segundos."""
        if self.ban_service is None:
            return []

        now = time.monotonic()
        if not force and now - self._last_maintenance < self.maintenance_interval:
            return []
        self._last_maintenance = now

        try:
            # ``reconcile`` vuelve a sincronizar el ZSET (por si el Servicio 1
            # creó un baneo manual) y desbanea lo que ya venció.
            expired = self.ban_service.reconcile()
        except Exception:  # Redis caído: el motor sigue leyendo logs
            logger.exception("Error revisando baneos vencidos")
            return []

        for ip in expired:
            logger.warning("UFW: baneo vencido, regla eliminada para %s", ip)
        return expired

    # ------------------------------------------------------------------
    # Trazas para la consola / evidencias
    # ------------------------------------------------------------------
    def _log(self, event: SSHEvent, decision: EngineDecision) -> None:
        prefix = (
            "FALLO" if event.outcome.value == "failed" else "ÉXITO"
        )
        base = "%s SSH ip=%s usuario=%s tipo=%s" % (
            prefix,
            event.ip,
            event.username or "-",
            event.event_type,
        )

        if decision.action is EngineAction.SUCCESS:
            logger.info("%s -> no se contabiliza", base)
        elif decision.action is EngineAction.WHITELISTED:
            logger.info("%s -> IP en whitelist, evento ignorado", base)
        elif decision.action is EngineAction.NOT_COUNTABLE:
            logger.debug("%s -> línea auxiliar, no incrementa", base)
        elif decision.action is EngineAction.ALREADY_BANNED:
            logger.info("%s -> IP ya baneada, no se acumula", base)
        elif decision.action is EngineAction.COUNTED:
            logger.info(
                "%s -> %d/%d intentos en %ds",
                base,
                decision.attempts_in_window,
                decision.maxretry,
                decision.findtime_seconds,
            )
        elif decision.action is EngineAction.BAN_REQUIRED:
            logger.warning(
                "%s -> UMBRAL ALCANZADO %d/%d en %ds; aplicando bloqueo UFW",
                base,
                decision.attempts_in_window,
                decision.maxretry,
                decision.findtime_seconds,
            )
