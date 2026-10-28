"""Aplicación Flask mínima del Servicio 2 (healthcheck).

El motor de logs se ejecuta en su propio proceso con ``python -m app`` para
que un reinicio del servidor web no interrumpa la lectura continua. Flask
queda como fachada operativa del servicio y base para el visor de logs de
una issue posterior.
"""

from __future__ import annotations

from flask import Flask, jsonify

from app.config import Settings, get_settings
from app.logging_config import configure_logging
from app.redis_client import create_redis_client, ping_redis


def create_app(
    settings: Settings | None = None,
    *,
    redis_client=None,
) -> Flask:
    """Fábrica de la aplicación Flask (inyectable en pruebas)."""
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    app = Flask(__name__)
    app.config["SETTINGS"] = active_settings
    client = redis_client or create_redis_client(active_settings)
    app.extensions["redis"] = client

    @app.get("/health")
    def health() -> tuple[dict[str, object], int]:
        redis_alive = ping_redis(client)
        body = {
            "status": "ok" if redis_alive else "degraded",
            "service": "service2-engine",
            "version": active_settings.version,
            "environment": active_settings.environment,
            "redis": "up" if redis_alive else "down",
            "log_path": active_settings.ssh_log_path,
        }
        return body, 200 if redis_alive else 503

    return app


app = create_app()
