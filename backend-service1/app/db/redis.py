"""Capa de acceso a datos: cliente asíncrono de Redis (``redis.asyncio``)."""

from __future__ import annotations

import asyncio
import logging

import redis.asyncio as aioredis
from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class RedisUnavailableError(RuntimeError):
    """Redis no está accesible (arranque, healthcheck o dependencia)."""


def create_redis_client(settings: Settings | None = None) -> Redis:
    """Crea el cliente asíncrono de Redis con decodificación a ``str``."""
    active_settings = settings or get_settings()
    return aioredis.Redis.from_url(
        active_settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=active_settings.redis_max_connections,
        socket_timeout=active_settings.redis_socket_timeout,
        socket_connect_timeout=active_settings.redis_socket_connect_timeout,
        socket_keepalive=True,
        health_check_interval=active_settings.redis_health_check_interval,
    )


async def ping_redis(client: Redis) -> bool:
    """Devuelve ``True`` si Redis responde ``PONG``."""
    try:
        response = await client.ping()
    except (RedisError, OSError) as exc:
        logger.warning("Ping a Redis falló: %s", exc)
        return False
    return bool(response)


async def wait_for_redis(client: Redis, settings: Settings | None = None) -> None:
    """Espera a que Redis responda, reintentando con backoff fijo.

    Cubre la condición de carrera habitual en Docker Compose: el contenedor
    de la API puede arrancar antes de que Redis esté listo.

    Raises:
        RedisUnavailableError: se agotaron los reintentos.
    """
    active_settings = settings or get_settings()
    attempts = active_settings.redis_startup_retries
    delay = active_settings.redis_startup_retry_delay
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            await client.ping()
        except (RedisError, OSError) as exc:  # pragma: no cover - depende del entorno
            last_error = exc
            logger.warning(
                "Redis no disponible (intento %d/%d): %s", attempt, attempts, exc
            )
            if attempt < attempts:
                await asyncio.sleep(delay)
        else:
            logger.info(
                "Conexión con Redis establecida en %s (intento %d)",
                active_settings.redis_url.split("@")[-1],
                attempt,
            )
            return

    raise RedisUnavailableError(
        f"Redis no respondió tras {attempts} intentos: {last_error}"
    )


async def close_redis(client: Redis) -> None:
    """Cierra el pool de conexiones de Redis de forma segura."""
    try:
        await client.aclose()
    except (RedisError, OSError) as exc:  # pragma: no cover - defensivo
        logger.warning("Error al cerrar la conexión con Redis: %s", exc)


def get_redis(request: Request) -> Redis:
    """Dependencia de FastAPI: entrega el cliente Redis del ciclo de vida."""
    client = getattr(request.app.state, "redis", None)
    if client is None:  # pragma: no cover - solo si el lifespan no corrió
        raise RedisUnavailableError("El cliente de Redis no fue inicializado")
    return client
