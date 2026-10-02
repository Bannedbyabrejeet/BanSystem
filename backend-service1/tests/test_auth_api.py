"""Pruebas de la API de autenticación contra los criterios de aceptación.

Cubren US-01.2 (setup único), US-01 (login), US-01.3 (recuperación de
contraseña) y US-10 (expiración estricta por TTL nativo de Redis).
"""

from __future__ import annotations

import asyncio
import json

import pytest
from redis.asyncio import Redis

from app.core import constants
from app.core.keys import ADMIN_CREDENTIALS, ADMIN_INITIALIZED, RESET_TOKEN_PREFIX

from .conftest import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_USERNAME, NEW_PASSWORD

pytestmark = pytest.mark.redis


# ======================================================================
# US-01.2 — Cuenta única de administrador
# ======================================================================
async def test_status_reports_not_initialized_on_empty_redis(client) -> None:
    response = await client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {"initialized": False}


async def test_setup_creates_the_single_admin_account(client) -> None:
    response = await client.post(
        "/api/v1/auth/setup",
        json={
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "password_confirm": ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == ADMIN_USERNAME
    assert body["email"] == ADMIN_EMAIL
    assert "password" not in body and "password_hash" not in body

    assert (await client.get("/api/v1/auth/status")).json() == {"initialized": True}


async def test_setup_persists_bcrypt_hash_without_ttl(client, redis_client: Redis) -> None:
    await client.post(
        "/api/v1/auth/setup",
        json={
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "password_confirm": ADMIN_PASSWORD,
        },
    )

    raw = await redis_client.get(ADMIN_CREDENTIALS)
    assert raw is not None
    assert ADMIN_PASSWORD not in raw  # nunca en claro
    assert '"$2b$' in raw or '"$2a$' in raw or '"$2y$' in raw
    assert int(await redis_client.ttl(ADMIN_CREDENTIALS)) == -1  # permanente
    assert await redis_client.exists(ADMIN_INITIALIZED) == 1


async def test_setup_is_rejected_when_admin_already_exists(client, admin_credentials) -> None:
    response = await client.post(
        "/api/v1/auth/setup",
        json={
            "username": "otro_admin",
            "email": "otro@bannedbyabrejeet.com",
            "password": "OtraClave2024",
            "password_confirm": "OtraClave2024",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == constants.ALREADY_INITIALIZED


async def test_concurrent_setup_creates_exactly_one_admin(client) -> None:
    """Dos peticiones simultáneas no pueden crear dos administradores."""

    async def attempt(index: int):
        return await client.post(
            "/api/v1/auth/setup",
            json={
                "username": f"admin{index}",
                "email": f"admin{index}@bannedbyabrejeet.com",
                "password": ADMIN_PASSWORD,
                "password_confirm": ADMIN_PASSWORD,
            },
        )

    responses = await asyncio.gather(*(attempt(index) for index in range(4)))
    statuses = [response.status_code for response in responses]
    assert statuses.count(201) == 1
    assert statuses.count(409) == 3


async def test_setup_rejects_weak_password(client) -> None:
    response = await client.post(
        "/api/v1/auth/setup",
        json={
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "password": "debil",
            "password_confirm": "debil",
        },
    )
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


async def test_setup_rejects_mismatched_confirmation(client) -> None:
    response = await client.post(
        "/api/v1/auth/setup",
        json={
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "password_confirm": "OtraClave2024",
        },
    )
    assert response.status_code == 422
    assert any("no coinciden" in item for item in response.json()["detail"])


async def test_setup_rejects_invalid_email(client) -> None:
    response = await client.post(
        "/api/v1/auth/setup",
        json={
            "username": ADMIN_USERNAME,
            "email": "no-es-un-correo",
            "password": ADMIN_PASSWORD,
            "password_confirm": ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 422


# ======================================================================
# US-01 — Login
# ======================================================================
async def test_login_with_valid_credentials_returns_jwt(client, admin_credentials) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0
    assert body["admin"]["username"] == ADMIN_USERNAME


async def test_login_accepts_email_as_identifier(client, admin_credentials) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200


async def test_login_with_wrong_password_returns_401_invalid_credentials(
    client, admin_credentials
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": ADMIN_USERNAME, "password": "ClaveIncorrecta2024"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == constants.INVALID_CREDENTIALS
    assert response.json()["detail"] == "Credenciales inválidas"


async def test_login_with_unknown_user_returns_the_same_401(client, admin_credentials) -> None:
    """No se distinguen usuario inexistente de contraseña incorrecta."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "intruso", "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == constants.INVALID_CREDENTIALS


async def test_login_before_setup_returns_401(client) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == constants.INVALID_CREDENTIALS


async def test_me_returns_the_session_admin(client, auth_headers) -> None:
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["admin"]["username"] == ADMIN_USERNAME
    assert body["role"] == "admin"
    assert body["token_expires_at"]


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer token-falso"}, {"Authorization": "Basic abc"}],
)
async def test_me_rejects_invalid_tokens(client, admin_credentials, headers) -> None:
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


async def test_me_rejects_token_with_wrong_secret(client, auth_headers) -> None:
    import jwt

    token = jwt.encode(
        {
            "sub": "otro-admin",
            "iss": "bannedbyabrejeet:service1",
            "aud": "bannedbyabrejeet:admin-console",
            "role": "admin",
            "ver": 1,
            "jti": "falso",
            "iat": 1,
            "nbf": 1,
            "exp": 4_102_444_800,
        },
        "clave-falsa-que-no-es-la-del-servicio-32bytes",
        algorithm="HS256",
    )
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


# ======================================================================
# US-01.3 / US-10 — Recuperación de contraseña
# ======================================================================
async def test_forgot_password_creates_token_with_native_ttl(
    client, admin_credentials, redis_client: Redis
) -> None:
    response = await client.post("/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL})
    assert response.status_code == 202
    assert response.json()["expires_in"] > 0

    keys = [key for key in await redis_client.keys(f"{RESET_TOKEN_PREFIX}*")]
    assert len(keys) == 1
    ttl = int(await redis_client.ttl(keys[0]))
    assert 0 < ttl <= 900  # US-10: expiración estricta por TTL nativo


async def test_forgot_password_does_not_reveal_unknown_accounts(client, admin_credentials) -> None:
    registrado = await client.post(
        "/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL}
    )
    desconocido = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nadie@bannedbyabrejeet.com"}
    )
    assert desconocido.status_code == registrado.status_code == 202
    assert desconocido.json()["message"] == registrado.json()["message"]


async def test_verify_reset_token_returns_remaining_ttl(
    client, admin_credentials, redis_client: Redis
) -> None:
    await client.post("/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL})
    token = (await redis_client.keys(f"{RESET_TOKEN_PREFIX}*"))[0].split(":", 1)[1]

    response = await client.get(f"/api/v1/auth/verify-reset-token/{token}")
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert 0 < body["expires_in"] <= 900


async def test_verify_unknown_token_returns_404_with_exact_message(client, admin_credentials) -> None:
    response = await client.get(
        "/api/v1/auth/verify-reset-token/abcdefghijklmnopqrstuvwxyz1234567890"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "El enlace de recuperación ha caducado o no es válido"


async def test_verify_expired_token_returns_404_after_redis_deletes_it(
    client, admin_credentials, redis_client: Redis
) -> None:
    """Redis elimina la clave por TTL: no hay limpieza del backend (US-10)."""
    await client.post("/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL})
    key = (await redis_client.keys(f"{RESET_TOKEN_PREFIX}*"))[0]

    # Se fuerza el vencimiento nativo con EXPIRE y se espera la eliminación.
    await redis_client.delete(key)
    assert await redis_client.exists(key) == 0

    response = await client.get(f"/api/v1/auth/verify-reset-token/{key.split(':', 1)[1]}")
    assert response.status_code == 404
    assert response.json()["detail"] == constants.RESET_TOKEN_INVALID


async def test_reset_password_updates_credential_and_consumes_token(
    client, redis_client: Redis, auth_headers
) -> None:
    await client.post("/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL})
    token = (await redis_client.keys(f"{RESET_TOKEN_PREFIX}*"))[0].split(":", 1)[1]
    previous_hash = json.loads(await redis_client.get(ADMIN_CREDENTIALS))["password_hash"]

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Contraseña actualizada correctamente"

    raw = await redis_client.get(ADMIN_CREDENTIALS)
    stored = json.loads(raw)
    assert stored["password_hash"] != previous_hash
    assert NEW_PASSWORD not in raw
    assert stored["session_version"] == 2  # invalida los JWT anteriores
    assert await redis_client.exists(f"{RESET_TOKEN_PREFIX}{token}") == 0

    # La sesión previa queda revocada aunque el JWT no haya expirado.
    revoked = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert revoked.status_code == 401

    # Y se puede iniciar sesión con la nueva contraseña.
    login = await client.post(
        "/api/v1/auth/login", json={"identifier": ADMIN_USERNAME, "password": NEW_PASSWORD}
    )
    assert login.status_code == 200


async def test_reset_password_works_with_expired_then_revoked_token(
    client, admin_credentials, redis_client: Redis
) -> None:
    await client.post("/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL})
    primer_token = (await redis_client.keys(f"{RESET_TOKEN_PREFIX}*"))[0].split(":", 1)[1]

    # Un segundo pedido de enlace revoca el anterior.
    await client.post("/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL})
    assert await redis_client.exists(f"{RESET_TOKEN_PREFIX}{primer_token}") == 0

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": primer_token,
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == constants.RESET_TOKEN_INVALID


async def test_reset_password_with_invalid_token_returns_404(client, admin_credentials) -> None:
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "token-inexistente-con-largo-suficiente-123456",
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == constants.RESET_TOKEN_INVALID


async def test_reset_password_rejects_weak_new_password(client, admin_credentials) -> None:
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "x" * 40, "new_password": "123", "confirm_password": "123"},
    )
    assert response.status_code == 422


# ======================================================================
# Sistema y documentación
# ======================================================================
async def test_health_reports_redis_state(client) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["redis"] == "up"


async def test_openapi_documents_auth_endpoints_and_bearer_scheme(client) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    paths = schema["paths"]
    for ruta in (
        "/api/v1/auth/status",
        "/api/v1/auth/setup",
        "/api/v1/auth/login",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/verify-reset-token/{token}",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/me",
    ):
        assert ruta in paths, f"falta documentar {ruta}"

    security_scheme = schema["components"]["securitySchemes"]["JWTAuthentication"]
    assert security_scheme["type"] == "http"
    assert security_scheme["scheme"] == "bearer"
    assert "Autenticación" in schema["tags"][0]["name"]


async def test_cors_allows_only_configured_origin(client) -> None:
    permitido = await client.get(
        "/api/v1/auth/status", headers={"Origin": "http://localhost:3000"}
    )
    assert permitido.headers.get("access-control-allow-origin") == "http://localhost:3000"

    prohibido = await client.get(
        "/api/v1/auth/status", headers={"Origin": "http://sitio-malicioso.local"}
    )
    assert "access-control-allow-origin" not in prohibido.headers
