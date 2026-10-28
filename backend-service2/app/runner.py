"""Punto de entrada del motor continuo (``python -m app``)."""

from __future__ import annotations

import logging
import threading

from app.bans import BanService
from app.config import Settings, get_settings
from app.engine import SecurityEngine
from app.logging_config import configure_logging
from app.monitor import LogMonitor
from app.parser import SSHParser
from app.redis_client import (
    RedisUnavailableError,
    create_redis_client,
    wait_for_redis,
)
from app.redis_config import RedisConfigReader
from app.tailer import LogTailer
from app.ufw import UfwExecutor
from app.unban_worker import UnbanWorker

logger = logging.getLogger(__name__)


def build_ban_service(client, settings: Settings, config_reader: RedisConfigReader) -> BanService:
    """Construye el ejecutor de UFW y el servicio de baneos."""
    executor = UfwExecutor(
        binary=settings.ufw_binary,
        use_sudo=settings.ufw_use_sudo,
        ssh_port=settings.ufw_ssh_port,
        timeout=settings.ufw_command_timeout,
        dry_run=settings.ufw_dry_run,
    )
    return BanService(client, executor, config_reader)


def main(settings: Settings | None = None) -> int:
    """Inicia el motor de seguridad, el worker de desbaneo y la expiración."""
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)
    logger.info(
        "Iniciando %s v%s", active_settings.project_name, active_settings.version
    )
    if active_settings.ufw_dry_run:
        logger.warning(
            "UFW_DRY_RUN activo: los comandos se registran pero no se ejecutan"
        )

    client = create_redis_client(active_settings)
    stop_event = threading.Event()
    worker_thread: threading.Thread | None = None
    try:
        wait_for_redis(client, active_settings)
        config_reader = RedisConfigReader(client)
        ban_service = build_ban_service(client, active_settings, config_reader)

        # Recupera sanciones que sobrevivieron a un reinicio y desbloquea las
        # que ya vencieron mientras el proceso estaba detenido. Un fallo aquí
        # no debe impedir que el motor siga leyendo logs.
        try:
            ban_service.reconcile()
        except Exception:
            logger.exception("No se pudo reconciliar los baneos al arrancar")

        engine = SecurityEngine(client, config_reader)
        tailer = LogTailer(
            active_settings.ssh_log_path,
            from_start=active_settings.log_read_from_start,
            encoding=active_settings.log_encoding,
        )
        monitor = LogMonitor(
            tailer,
            SSHParser(),
            engine,
            poll_interval=active_settings.log_poll_interval,
            ban_service=ban_service,
            maintenance_interval=active_settings.ban_maintenance_interval,
        )

        worker = UnbanWorker(
            client,
            ban_service,
            stream=active_settings.unban_stream,
            group=active_settings.unban_consumer_group,
            consumer=active_settings.unban_consumer_name or None,
            block_ms=active_settings.unban_block_ms,
            batch_size=active_settings.unban_batch_size,
            retry_min_idle_ms=active_settings.unban_retry_min_idle_ms,
        )
        worker_thread = threading.Thread(
            target=worker.run,
            args=(stop_event,),
            name="unban-worker",
            daemon=True,
        )
        worker_thread.start()

        monitor.run(stop_event)
    except KeyboardInterrupt:
        logger.info("Detención solicitada por el operador")
    except RedisUnavailableError as exc:
        logger.error("No se pudo iniciar el motor: %s", exc)
        return 1
    finally:
        stop_event.set()
        if worker_thread is not None:
            worker_thread.join(timeout=5.0)
        client.close()

    return 0
