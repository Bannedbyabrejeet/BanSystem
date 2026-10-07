"""Configuración compartida de la suite de pruebas del Servicio 1.

Los tests necesitan Redis porque el servicio usa comandos nativos
(``SETEX``, ``EXPIRE``, ``SCAN``) y scripts Lua para el setup único y el
consumo del token de recuperación. La estrategia es:

Por defecto la suite usa un **Redis real**, porque el consumo del token de
recuperación depende de ``cjson`` dentro de un script Lua. La suite hace
``FLUSHDB``, así que requiere un Redis propio y descartable, separado del de
desarrollo (``redis/redis.conf`` usa ``databases 1`` y su db 0 contiene la
cuenta real del administrador)::

    docker run -d --rm --name bba-test-redis -p 6399:6379 \
        redis:7.2-alpine redis-server --save '' --appendonly no
    TEST_REDIS_URL="redis://127.0.0.1:6399/15" pytest

Si no hay Redis disponible, los tests de API se omiten con un mensaje
explicativo en lugar de fallar. Para forzar el emulado ``fakeredis``
(habilitando antes ``pip install 'fakeredis[lua]'``)::

    BBA_TEST_FAKEREDIS=1 pytest
"""

from __future__ import annotations

import os
from typing import AsyncIterator

import pytest
from redis.asyncio import Redis

from app.core.config import Settings
from app.main import create_app

#: Base de datos dedicada a los tests (nunca tocar la de desarrollo).
DEFAULT_TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@bannedbyabrejeet.com"
ADMIN_PASSWORD = "Banned2024Admin"
NEW_PASSWORD = "NuevaClave2024"

#: Prefijo de las claves que el test limpia entre casos.
MANAGED_KEY_PREFIXES = ("admin:", "reset_token:")


#: El reset de contraseña usa ``cjson`` dentro del script Lua, por lo que la
#: suite necesita un Redis con Lua completo. ``fakeredis`` depende de ``lupa``
#: (binario nativo) y no siempre lo incluye, así que el servidor real es la
#: opción recomendada:  docker compose up -d redis
_LUA_PROBE = "return type(cjson) == 'table' and 1 or 0"

#: Poner en "1" para forzar el Redis emulado en lugar del servidor real.
USE_FAKEREDIS_ENV = "BBA_TEST_FAKEREDIS"


async def _supports_full_lua(client: Redis) -> bool:
    """Comprueba que el servidor soporta ``EVAL`` con ``cjson``."""
    try:
        return int(await client.eval(_LUA_PROBE, 0)) == 1
    except Exception:  # pragma: no cover - depende del entorno
        return False


async def _build_redis_client() -> tuple[Redis | None, str]:
    """Devuelve ``(cliente, origen)``; ``(None, motivo)`` si no hay Redis.

    El origen se usa en el mensaje de ``pytest.skip`` para que quede claro
    contra qué motor se ejecutó la suite.
    """
    from redis.exceptions import RedisError

    def real_client() -> Redis:
        return Redis.from_url(DEFAULT_TEST_REDIS_URL, decode_responses=True)

    # 1) Redis emulado, solo si se pide explícitamente.
    if os.getenv(USE_FAKEREDIS_ENV) == "1":
        try:
            import fakeredis.aioredis as fake_aioredis  # type: ignore[import-untyped]
        except ImportError:
            return None, "fakeredis no está instalado"
        client = fake_aioredis.FakeRedis(decode_responses=True)
        if await _supports_full_lua(client):
            return client, "fakeredis (emulado)"
        await client.aclose()
        return None, "fakeredis sin soporte de cjson (falta lupa)"

    # 2) Redis real (el del proyecto, o el definido en TEST_REDIS_URL).
    client = real_client()
    try:
        await client.ping()
    except (RedisError, OSError):
        await client.aclose()
        return None, f"no responde {DEFAULT_TEST_REDIS_URL}"
    if not await _supports_full_lua(client):
        await client.aclose()
        return None, f"{DEFAULT_TEST_REDIS_URL} no soporta Lua con cjson"
    return client, DEFAULT_TEST_REDIS_URL


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Configuración de tests: bcrypt barato y TTL de 60 s."""
    return Settings(
        environment="testing",
        debug=True,
        jwt_secret="secreto-de-pruebas-bannedbyabrejeet-32bytes-minimo",
        bcrypt_rounds=8,
        reset_token_ttl=60,
        cors_origins="http://localhost:3000",
        mail_mode="log",
    )


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    """Cliente Redis limpio para cada test."""
    client, origin = await _build_redis_client()
    if client is None:
        pytest.skip(
            f"Redis no disponible ({origin}). Los tests hacen FLUSHDB, así que "
            "necesitan un Redis propio y descartable, no el de desarrollo "
            "(redis/redis.conf usa `databases 1`: solo existe la db 0, la del "
            "administrador real). Levantar uno efímero y apuntar TEST_REDIS_URL: "
            '`docker run -d --rm --name bba-test-redis -p 6399:6379 redis:7.2-alpine '
            'redis-server --save "" --appendonly no` y luego '
            'TEST_REDIS_URL="redis://127.0.0.1:6399/15"'
        )

    await _clear_managed_keys(client)
    yield client
    await _clear_managed_keys(client)
    await client.aclose()


async def _clear_managed_keys(client: Redis) -> None:
    """Borra solo las claves que la suite puede crear."""
    for key in await client.keys("*"):
        if key.startswith(MANAGED_KEY_PREFIXES):
            await client.delete(key)


@pytest.fixture
def app(settings: Settings):
    """Aplicación FastAPI sin lifespan (el cliente Redis se inyecta a mano)."""
    return create_app(settings)


@pytest.fixture
async def client(app, redis_client: Redis):
    """Cliente HTTP ASGI conectado a la aplicación de test."""
    from httpx import ASGITransport, AsyncClient

    app.state.redis = redis_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest.fixture
async def admin_credentials(client) -> dict[str, str]:
    """Crea la cuenta única de administrador y devuelve sus credenciales."""
    response = await client.post(
        "/api/v1/auth/setup",
        json={
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "password_confirm": ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 201, response.text
    return {"username": ADMIN_USERNAME, "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}


@pytest.fixture
async def auth_token(client, admin_credentials) -> str:
    """Token JWT de una sesión activa."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": admin_credentials["username"], "password": admin_credentials["password"]},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}
