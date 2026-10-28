"""Punto de entrada del motor continuo (``python -m app``)."""

from __future__ import annotations

import logging

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

logger = logging.getLogger(__name__)


def main(settings: Settings | None = None) -> int:
    """Inicia la lectura continua de logs y el motor de seguridad."""
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)
    logger.info(
        "Iniciando %s v%s", active_settings.project_name, active_settings.version
    )

    client = create_redis_client(active_settings)
    try:
        wait_for_redis(client, active_settings)
        config_reader = RedisConfigReader(client)
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
        )
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Detención solicitada por el operador")
    except RedisUnavailableError as exc:
        logger.error("No se pudo iniciar el motor: %s", exc)
        return 1
    finally:
        client.close()

    return 0
