"""Fixtures de la suite del Servicio 2."""

from __future__ import annotations

from collections.abc import Iterator

import fakeredis
import pytest
from redis import Redis

from app.config import Settings


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Configuración aislada que no depende del ``.env`` de desarrollo."""
    return Settings(
        environment="testing",
        ssh_log_path=str(tmp_path / "auth.log"),
        log_read_from_start=True,
        log_poll_interval=0.01,
        redis_startup_retries=1,
        redis_startup_retry_delay=0.1,
    )


@pytest.fixture
def redis_client() -> Iterator[Redis]:
    """Redis emulado; se limpia al terminar cada test."""
    client = fakeredis.FakeRedis(decode_responses=True)
    try:
        yield client
    finally:
        client.flushall()
        client.close()
