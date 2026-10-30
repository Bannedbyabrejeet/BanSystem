"""Consumidor del stream de desbaneo manual (Issue #8 / US-07).

El Servicio 1 publica en ``security:events:unban`` cuando el administrador
pulsa "Desbanear" en el dashboard. Este worker, dentro del Servicio 2:

1. lee el mensaje con el consumer group ``ufw_workers``;
2. elimina la regla de UFW;
3. limpia el vencimiento ``bans:expirations`` y el hash ``ips:banned``;
4. confirma el mensaje con ``XACK``.

Si UFW falla, el mensaje **no** se confirma y queda pendiente para que el
worker lo reintente. Las órdenes con IP inválida o acción desconocida se
descartan con ``XACK`` para no bloquear el stream.
"""

from __future__ import annotations

import logging
import os
import socket
import threading
import time
from typing import Final

from redis import Redis
from redis.exceptions import ResponseError

from app.bans import BanError, BanService
from app.keys import UNBAN_CONSUMER_GROUP, UNBAN_STREAM
from app.ufw import normalize_ip

logger = logging.getLogger(__name__)

#: Acción esperada en el contrato ``docs/contrato-desbaneo.yaml``.
UNBAN_ACTION: Final[str] = "UNBAN"


def default_consumer_name() -> str:
    """Nombre único del consumidor para este proceso."""
    return f"service2-{socket.gethostname()}-{os.getpid()}"


def _field(fields: dict[str, str], name: str) -> str:
    value = fields.get(name, "")
    return value.decode() if isinstance(value, bytes) else str(value)


class UnbanWorker:
    """Bucle que consume órdenes de desbaneo del stream Redis."""

    def __init__(
        self,
        redis: Redis,
        bans: BanService,
        *,
        stream: str = UNBAN_STREAM,
        group: str = UNBAN_CONSUMER_GROUP,
        consumer: str | None = None,
        block_ms: int = 1_000,
        batch_size: int = 10,
        retry_min_idle_ms: int = 5_000,
    ) -> None:
        self.redis = redis
        self.bans = bans
        self.stream = stream
        self.group = group
        self.consumer = consumer or default_consumer_name()
        self.block_ms = block_ms
        self.batch_size = batch_size
        self.retry_min_idle_ms = retry_min_idle_ms

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def ensure_group(self) -> None:
        """Crea el consumer group si todavía no existe."""
        try:
            self.redis.xgroup_create(
                name=self.stream,
                groupname=self.group,
                id="0",
                mkstream=True,
            )
            logger.info(
                "Consumer group %s creado en %s", self.group, self.stream
            )
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise
            logger.info(
                "Consumer group %s ya existe en %s", self.group, self.stream
            )

    def run(self, stop_event: threading.Event | None = None) -> None:
        """Consume mensajes hasta que se solicite detener el proceso."""
        self.ensure_group()
        logger.info(
            "Worker de desbaneo escuchando %s (grupo=%s, consumidor=%s)",
            self.stream,
            self.group,
            self.consumer,
        )
        while stop_event is None or not stop_event.is_set():
            try:
                self.process_once()
            except Exception:  # Redis caído o error transitorio
                logger.exception("Error en el worker de desbaneo")
                if stop_event is not None:
                    stop_event.wait(1.0)
                else:
                    time.sleep(1.0)
        logger.info("Worker de desbaneo detenido")

    # ------------------------------------------------------------------
    # Procesamiento
    # ------------------------------------------------------------------
    def process_once(self, *, block_ms: int | None = None) -> int:
        """Procesa mensajes nuevos y reintenta los pendientes.

        Returns:
            Cantidad de órdenes procesadas correctamente en esta pasada.
        """
        processed = self._read_and_process(">", block_ms=block_ms)
        # Los mensajes que fallaron (por ejemplo, UFW no disponible) quedan
        # pendientes; XAUTOCLAIM los vuelve a entregar tras el tiempo de
        # espera configurado.
        processed += self._reclaim_and_process()
        return processed

    def _read_and_process(self, stream_id: str, *, block_ms: int | None) -> int:
        kwargs: dict[str, object] = {"count": self.batch_size}
        if stream_id == ">" and block_ms is not None and block_ms > 0:
            kwargs["block"] = block_ms

        response = self.redis.xreadgroup(
            self.group,
            self.consumer,
            {self.stream: stream_id},
            **kwargs,
        )
        if not response:
            return 0

        processed = 0
        for _stream, entries in response:
            for message_id, fields in entries:
                if self._handle(message_id, fields):
                    processed += 1
        return processed

    def _reclaim_and_process(self) -> int:
        """Reintenta mensajes pendientes de este consumidor (Redis >= 6.2).

        Se reclama como máximo un lote por pasada para no monopolizar el
        bucle: los pendientes restantes se retoman en la siguiente.
        """
        result = self.redis.xautoclaim(
            self.stream,
            self.group,
            self.consumer,
            min_idle_time=self.retry_min_idle_ms,
            start_id="0-0",
            count=self.batch_size,
        )
        if not result:
            return 0

        _next_id, entries, _deleted = result
        processed = 0
        for message_id, fields in entries:
            if self._handle(message_id, fields):
                processed += 1
        return processed

    def _handle(self, message_id: str, fields: dict[str, str]) -> bool:
        action = _field(fields, "action").strip().upper()
        ip = _field(fields, "ip").strip()
        requested_by = _field(fields, "requested_by").strip() or "desconocido"

        if action != UNBAN_ACTION:
            logger.warning(
                "Mensaje %s ignorado: acción %r no soportada", message_id, action
            )
            self._ack(message_id)
            return False

        try:
            normalized = normalize_ip(ip)
        except ValueError as exc:
            logger.error(
                "Mensaje %s descartado: %s", message_id, exc
            )
            self._ack(message_id)
            return False

        try:
            removed = self.bans.unban(
                normalized, reason="manual", requested_by=requested_by
            )
        except BanError as exc:
            # No se confirma: el mensaje sigue pendiente para reintentar.
            logger.error(
                "Desbaneo manual de %s falló (%s); mensaje %s queda pendiente",
                normalized,
                exc,
                message_id,
            )
            return False

        self._ack(message_id)
        logger.info(
            "Desbaneo manual confirmado: ip=%s solicitado_por=%s hash_activo=%s",
            normalized,
            requested_by,
            removed,
        )
        return True

    def _ack(self, message_id: str) -> None:
        self.redis.xack(self.stream, self.group, message_id)
