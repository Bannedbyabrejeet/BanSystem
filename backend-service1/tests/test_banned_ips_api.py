"""Pruebas de la API de IPs baneadas y desbaneo manual (Issue #7 / #8)."""

from __future__ import annotations

import json

import pytest
from redis.asyncio import Redis

pytestmark = pytest.mark.redis

STREAM = "security:events:unban"
IP = "203.0.113.42"


@pytest.fixture(autouse=True)
async def clean_ban_keys(redis_client: Redis):
    """Aísla las claves de baneo, que no forman parte del prefijo limpiado."""
    keys = ("ips:banned", "ips:history", STREAM)
    await redis_client.delete(*keys)
    yield
    await redis_client.delete(*keys)


async def create_ban(redis_client: Redis, ip: str = IP) -> None:
    await redis_client.hset(
        "ips:banned",
        ip,
        json.dumps(
            {
                "banned_at": 1_000,
                "expires_at": 2_800,
                "duration_min": 30,
                "reason": "SSH brute force",
            }
        ),
    )


async def test_manual_unban_removes_redis_state_and_publishes_unban_event(
    client, auth_headers, redis_client: Redis
) -> None:
    await create_ban(redis_client)

    response = await client.delete(
        f"/api/v1/banned-ips/{IP}", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["entry"] == IP
    assert await redis_client.hexists("ips:banned", IP) == 0

    history = json.loads(await redis_client.lindex("ips:history", 0))
    assert history["action"] == "unbanned"
    assert history["unban_reason"] == "manual"

    messages = await redis_client.xrange(STREAM)
    assert len(messages) == 1
    _message_id, fields = messages[0]
    assert fields == {
        "action": "UNBAN",
        "ip": IP,
        "requested_by": "admin",
        "timestamp": fields["timestamp"],
    }


async def test_manual_unban_of_unknown_ip_returns_404(
    client, auth_headers
) -> None:
    response = await client.delete(
        "/api/v1/banned-ips/198.51.100.7", headers=auth_headers
    )

    assert response.status_code == 404


async def test_manual_ban_does_not_publish_an_unban_event(
    client, auth_headers, redis_client: Redis
) -> None:
    """Regresión: un baneo manual no debe desbanearse a sí mismo."""
    response = await client.post(
        "/api/v1/banned-ips/",
        headers=auth_headers,
        params={"ip": IP},
    )

    assert response.status_code == 201
    assert await redis_client.hexists("ips:banned", IP) == 1
    assert await redis_client.xlen(STREAM) == 0
