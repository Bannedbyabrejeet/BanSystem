"""Pruebas de la API de configuración (Issue #6).

Cubren US-02 (umbral y duración del baneo), US-09 (ventana de tolerancia) y
US-08 (lista blanca con IPs locales protegidas).
"""

from __future__ import annotations

import pytest
from redis.asyncio import Redis

from app.core import constants
from app.core.keys import CONFIG_SETTINGS, CONFIG_WHITELIST

pytestmark = pytest.mark.redis

DEFAULT_SETTINGS = {"maxretry": 5, "bantime": 30, "findtime": 10}


# ======================================================================
# Autenticación obligatoria
# ======================================================================
@pytest.mark.parametrize(
    ("method", "url", "kwargs"),
    [
        ("GET", "/api/v1/config/settings", {}),
        ("PUT", "/api/v1/config/settings", {"json": DEFAULT_SETTINGS}),
        ("GET", "/api/v1/config/whitelist", {}),
        ("POST", "/api/v1/config/whitelist", {"json": {"entry": "192.168.1.10"}}),
        ("DELETE", "/api/v1/config/whitelist", {"params": {"entry": "192.168.1.10"}}),
    ],
)
async def test_config_endpoints_require_an_admin_session(
    client, method: str, url: str, kwargs: dict
) -> None:
    response = await client.request(method, url, **kwargs)
    assert response.status_code == 401


# ======================================================================
# US-02 / US-09 — parámetros de baneo
# ======================================================================
async def test_settings_return_defaults_when_redis_is_empty(client, auth_headers) -> None:
    response = await client.get("/api/v1/config/settings", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == DEFAULT_SETTINGS


async def test_settings_return_defaults_for_missing_or_invalid_fields(
    client, auth_headers, redis_client: Redis
) -> None:
    """Contrato de Redis: un campo ausente o inválido usa su valor por defecto."""
    await redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "8", "bantime": "no-es-un-numero"},
    )

    body = (await client.get("/api/v1/config/settings", headers=auth_headers)).json()
    assert body == {"maxretry": 8, "bantime": 30, "findtime": 10}


async def test_settings_out_of_range_field_falls_back_to_default(
    client, auth_headers, redis_client: Redis
) -> None:
    await redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "999999", "bantime": "45", "findtime": "0"},
    )

    body = (await client.get("/api/v1/config/settings", headers=auth_headers)).json()
    assert body == {"maxretry": 5, "bantime": 45, "findtime": 10}


async def test_update_settings_persists_all_fields_in_redis(
    client, auth_headers, redis_client: Redis
) -> None:
    payload = {"maxretry": 7, "bantime": 45, "findtime": 15}

    response = await client.put(
        "/api/v1/config/settings", headers=auth_headers, json=payload
    )
    assert response.status_code == 200
    assert response.json() == payload

    stored = await redis_client.hgetall(CONFIG_SETTINGS)
    assert stored == {"maxretry": "7", "bantime": "45", "findtime": "15"}
    assert int(await redis_client.ttl(CONFIG_SETTINGS)) == -1  # persistente

    # La lectura posterior devuelve lo mismo que se guardó.
    readback = await client.get("/api/v1/config/settings", headers=auth_headers)
    assert readback.json() == payload


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("maxretry", 0),
        ("maxretry", -3),
        ("maxretry", "5"),  # se exige un número JSON, no una cadena
        ("bantime", 1.5),
        ("bantime", 0),
        ("findtime", 0),
        ("findtime", -10),
        ("findtime", None),
    ],
)
async def test_update_settings_rejects_non_positive_or_non_integer_values(
    client, auth_headers, redis_client: Redis, field: str, invalid_value
) -> None:
    payload = {**DEFAULT_SETTINGS, field: invalid_value}

    response = await client.put(
        "/api/v1/config/settings", headers=auth_headers, json=payload
    )
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    # Un valor inválido no debe dejar escrituras parciales.
    assert await redis_client.exists(CONFIG_SETTINGS) == 0


async def test_update_settings_requires_every_field(client, auth_headers) -> None:
    response = await client.put(
        "/api/v1/config/settings",
        headers=auth_headers,
        json={"maxretry": 5, "bantime": 30},
    )
    assert response.status_code == 422


async def test_update_settings_rejects_unknown_fields(client, auth_headers) -> None:
    response = await client.put(
        "/api/v1/config/settings",
        headers=auth_headers,
        json={**DEFAULT_SETTINGS, "extra": 1},
    )
    assert response.status_code == 422


# ======================================================================
# US-08 — lista blanca
# ======================================================================
async def test_whitelist_includes_localhost_by_default(client, auth_headers) -> None:
    response = await client.get("/api/v1/config/whitelist", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    assert set(body["entries"]) == {"127.0.0.1", "::1"}
    assert body["protected_entries"] == ["127.0.0.1", "::1"]


async def test_protected_entries_are_reinserted_if_missing_in_redis(
    client, auth_headers, redis_client: Redis
) -> None:
    await redis_client.srem(CONFIG_WHITELIST, "127.0.0.1")
    assert await redis_client.sismember(CONFIG_WHITELIST, "127.0.0.1") == 0

    body = (await client.get("/api/v1/config/whitelist", headers=auth_headers)).json()
    assert "127.0.0.1" in body["entries"]
    assert await redis_client.sismember(CONFIG_WHITELIST, "127.0.0.1") == 1


async def test_add_ip_and_subnet_persists_in_redis(
    client, auth_headers, redis_client: Redis
) -> None:
    first = await client.post(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        json={"entry": "192.168.1.10"},
    )
    assert first.status_code == 201
    assert first.json()["entry"] == "192.168.1.10"
    assert first.json()["message"] == constants.WHITELIST_ENTRY_ADDED
    assert "192.168.1.10" in first.json()["entries"]

    second = await client.post(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        json={"entry": "10.1.2.3/8"},
    )
    assert second.status_code == 201
    assert second.json()["entry"] == "10.0.0.0/8"  # normalizado a nivel de red

    stored = await redis_client.smembers(CONFIG_WHITELIST)
    assert {"127.0.0.1", "::1", "192.168.1.10", "10.0.0.0/8"} <= stored


async def test_adding_an_existing_entry_is_idempotent(
    client, auth_headers, redis_client: Redis
) -> None:
    payload = {"entry": "203.0.113.42"}
    await client.post("/api/v1/config/whitelist", headers=auth_headers, json=payload)

    response = await client.post(
        "/api/v1/config/whitelist", headers=auth_headers, json=payload
    )
    assert response.status_code == 201
    assert response.json()["message"] == constants.WHITELIST_ENTRY_EXISTS
    assert int(await redis_client.scard(CONFIG_WHITELIST)) == 3


async def test_add_ipv6_entry(client, auth_headers, redis_client: Redis) -> None:
    response = await client.post(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        json={"entry": "2001:db8::/32"},
    )
    assert response.status_code == 201
    assert response.json()["entry"] == "2001:db8::/32"
    assert await redis_client.sismember(CONFIG_WHITELIST, "2001:db8::/32") == 1


async def test_remove_non_protected_entry(
    client, auth_headers, redis_client: Redis
) -> None:
    await client.post(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        json={"entry": "198.51.100.0/24"},
    )

    response = await client.delete(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        params={"entry": "198.51.100.0/24"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == constants.WHITELIST_ENTRY_REMOVED
    assert response.json()["entry"] == "198.51.100.0/24"
    assert "198.51.100.0/24" not in response.json()["entries"]
    assert await redis_client.sismember(CONFIG_WHITELIST, "198.51.100.0/24") == 0


@pytest.mark.parametrize("entry", ["127.0.0.1", "127.0.0.1/32", "::1", "::1/128"])
async def test_localhost_cannot_be_removed(
    client, auth_headers, redis_client: Redis, entry: str
) -> None:
    response = await client.delete(
        "/api/v1/config/whitelist", headers=auth_headers, params={"entry": entry}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == constants.PROTECTED_WHITELIST_ENTRY

    assert await redis_client.sismember(CONFIG_WHITELIST, "127.0.0.1") == 1
    assert await redis_client.sismember(CONFIG_WHITELIST, "::1") == 1


async def test_removing_unknown_entry_returns_404(client, auth_headers) -> None:
    response = await client.delete(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        params={"entry": "203.0.113.99"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == constants.WHITELIST_ENTRY_NOT_FOUND


@pytest.mark.parametrize(
    "entry",
    ["no-es-una-ip", "999.1.1.1", "10.0.0.0/33", "2001:db8::/129", "127.0.0.1/abc"],
)
async def test_add_rejects_invalid_ip_or_cidr(client, auth_headers, entry: str) -> None:
    response = await client.post(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        json={"entry": entry},
    )
    assert response.status_code == 422
    assert any("IP o subred" in item for item in response.json()["detail"])


async def test_delete_rejects_invalid_ip_or_cidr(client, auth_headers) -> None:
    response = await client.delete(
        "/api/v1/config/whitelist",
        headers=auth_headers,
        params={"entry": "no-es-una-ip"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == constants.INVALID_NETWORK_ENTRY


# ======================================================================
# Documentación
# ======================================================================
async def test_openapi_documents_config_endpoints(client, auth_headers) -> None:
    schema = (await client.get("/openapi.json")).json()

    for route in (
        "/api/v1/config/settings",
        "/api/v1/config/whitelist",
    ):
        assert route in schema["paths"], f"falta documentar {route}"

    assert any(tag["name"] == "Configuración" for tag in schema["tags"])
