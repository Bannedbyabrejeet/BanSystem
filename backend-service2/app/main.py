"""Aplicación Flask del Servicio 2: healthcheck y telemetría (Issue #9).

El motor de logs se ejecuta en su propio proceso con ``python -m app`` para
que un reinicio del servidor web no interrumpa la lectura continua. Flask
expone el healthcheck y la API ``/telemetry`` que consume el Frontend B.
"""

from __future__ import annotations

from flask import Flask

from app.api import telemetry
from app.config import Settings, get_settings
from app.logging_config import configure_logging
from app.redis_client import create_redis_client, ping_redis
from app.telemetry import TelemetryStore


def create_app(
    settings: Settings | None = None,
    *,
    redis_client=None,
    telemetry_store: TelemetryStore | None = None,
) -> Flask:
    """Fábrica de la aplicación Flask (inyectable en pruebas)."""
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    app = Flask(__name__)
    app.config["SETTINGS"] = active_settings
    client = redis_client or create_redis_client(active_settings)
    app.extensions["redis"] = client
    store = telemetry_store or TelemetryStore(
        client, event_limit=active_settings.ssh_events_limit
    )
    app.extensions["telemetry"] = store
    app.register_blueprint(telemetry)

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
            "ufw": {
                "binary": active_settings.ufw_binary,
                "ssh_port": active_settings.ufw_ssh_port,
                "dry_run": active_settings.ufw_dry_run,
            },
        }
        return body, 200 if redis_alive else 503

    return app


app = create_app()
