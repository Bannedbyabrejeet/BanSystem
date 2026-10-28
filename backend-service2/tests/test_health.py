"""Pruebas del healthcheck Flask y su conexión con Redis."""

from __future__ import annotations

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.config import Settings
from app.main import create_app


def test_health_reports_redis_up(settings: Settings, redis_client: Redis) -> None:
    app = create_app(settings, redis_client=redis_client)
    response = app.test_client().get("/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["service"] == "service2-engine"
    assert body["redis"] == "up"
    assert body["log_path"] == settings.ssh_log_path


class _BrokenRedis:
    def ping(self) -> bool:
        raise RedisConnectionError("sin conexión")


def test_health_reports_degraded_when_redis_is_down(
    settings: Settings,
) -> None:
    app = create_app(settings, redis_client=_BrokenRedis())
    response = app.test_client().get("/health")

    assert response.status_code == 503
    assert response.get_json()["redis"] == "down"
