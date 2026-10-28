"""Bucle que conecta el tailer, el parser y el motor de seguridad."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterable

from app.engine import SecurityEngine
from app.models import EngineAction, EngineDecision, SSHEvent
from app.parser import SSHParser
from app.tailer import LogTailer

logger = logging.getLogger(__name__)


class LogMonitor:
    """Procesa líneas nuevas y aplica el motor a cada evento SSH."""

    def __init__(
        self,
        tailer: LogTailer,
        parser: SSHParser,
        engine: SecurityEngine,
        *,
        poll_interval: float = 0.5,
    ) -> None:
        self.tailer = tailer
        self.parser = parser
        self.engine = engine
        self.poll_interval = poll_interval

    def process_available(self) -> list[EngineDecision]:
        """Procesa todos los eventos disponibles sin bloquear."""
        decisions: list[EngineDecision] = []
        for line in self.tailer.read_available():
            event = self.parser.parse(line)
            if event is None:
                continue
            decision = self.engine.process(event)
            self._log(event, decision)
            decisions.append(decision)
        return decisions

    def run(self, stop_event: threading.Event | None = None) -> None:
        """Sondea el archivo hasta que se pida detener el proceso."""
        logger.info("Motor de seguridad escuchando %s", self.tailer.path)
        try:
            while stop_event is None or not stop_event.is_set():
                self.process_available()
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
            decisions.append(decision)
        return decisions

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
                "%s -> UMBRAL ALCANZADO %d/%d en %ds; bloqueo pendiente (UFW "
                "fuera del alcance de esta issue)",
                base,
                decision.attempts_in_window,
                decision.maxretry,
                decision.findtime_seconds,
            )
