"""Cliente Redis síncrono y espera de arranque del Servicio 2."""

from __future__ import annotations

import logging
import time

import redis
from redis import Redis
from redis.exceptions import RedisError

from app.config import Settings

logger = logging.getLogger(__name__)


class RedisUnavailableError(RuntimeError):
    """Redis no está accesible."""


def create_redis_client(settings: Settings) -> Redis:
    """Crea el cliente con decodificación a ``str`` y timeouts acotados."""
    return redis.Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        socket_keepalive=True,
        health_check_interval=settings.redis_health_check_interval,
    )


def ping_redis(client: Redis) -> bool:
    """``True`` si Redis responde."""
    try:
        return bool(client.ping())
    except (RedisError, OSError) as exc:
        logger.warning("Ping a Redis falló: %s", exc)
        return False


def wait_for_redis(client: Redis, settings: Settings) -> None:
    """Espera a que Redis esté disponible al arrancar el motor."""
    for attempt in range(1, settings.redis_startup_retries + 1):
        try:
            client.ping()
        except (RedisError, OSError) as exc:
            logger.warning(
                "Redis no disponible (intento %d/%d): %s",
                attempt,
                settings.redis_startup_retries,
                exc,
            )
            if attempt < settings.redis_startup_retries:
                time.sleep(settings.redis_startup_retry_delay)
        else:
            logger.info(
                "Conexión con Redis establecida en %s",
                settings.redis_url.split("@")[-1],
            )
            return

    raise RedisUnavailableError(
        f"Redis no respondió tras {settings.redis_startup_retries} intentos"
    )
