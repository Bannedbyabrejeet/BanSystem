"""Pruebas de la API /telemetry consumida por el Frontend B (Issue #9)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from redis import Redis

from app.config import Settings
from app.keys import ADMIN_CREDENTIALS, IPS_BANNED, IPS_HISTORY, SSH_EVENTS, UNBAN_STREAM
from app.main import create_app
from app.models import Outcome, SSHEvent
from app.telemetry import TelemetryStore

ADMIN_ID = "11111111-1111-1111-1111-111111111111"
STREAM = UNBAN_STREAM


def make_token(settings: Settings, *, version: int = 1, expires_in: int = 300) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": ADMIN_ID,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "role": "admin",
            "ver": version,
            "jti": "test-jti",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


@pytest.fixture
def app(settings: Settings, redis_client: Redis):
    redis_client.set(
        ADMIN_CREDENTIALS,
        json.dumps(
            {
                "admin_id": ADMIN_ID,
                "username": "admin",
                "session_version": 1,
            }
        ),
    )
    return create_app(settings, redis_client=redis_client)


@pytest.fixture
def auth_headers(settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(settings)}"}


def seed_event(
    redis_client: Redis,
    *,
    ip: str = "203.0.113.42",
    timestamp: int = 1_000,
    outcome: Outcome = Outcome.FAILED,
    username: str = "root",
) -> None:
    TelemetryStore(redis_client).record_event(
        SSHEvent(
            timestamp=timestamp,
            ip=ip,
            username=username,
            outcome=outcome,
            event_type="failed_password" if outcome is Outcome.FAILED else "accepted_password",
            raw_line="linea de prueba",
            port=22,
        )
    )


def test_telemetry_requires_a_bearer_token(app) -> None:
    response = app.test_client().get("/telemetry/logs")

    assert response.status_code == 401
    assert response.get_json()["detail"] == "Sesión no válida"


def test_invalid_token_is_rejected(app) -> None:
    response = app.test_client().get(
        "/telemetry/logs", headers={"Authorization": "Bearer no-es-un-jwt"}
    )

    assert response.status_code == 401


def test_revoked_session_is_rejected(
    app, settings: Settings, redis_client: Redis
) -> None:
    redis_client.set(
        ADMIN_CREDENTIALS,
        json.dumps(
            {
                "admin_id": ADMIN_ID,
                "username": "admin",
                "session_version": 2,
            }
        ),
    )
    token = make_token(settings, version=1)

    response = app.test_client().get(
        "/telemetry/logs", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert response.get_json()["detail"] == "La sesión fue revocada"


def test_logs_returns_items_and_stats(app, auth_headers, redis_client: Redis) -> None:
    seed_event(redis_client, timestamp=1_000, outcome=Outcome.FAILED)
    seed_event(
        redis_client,
        ip="198.51.100.7",
        timestamp=1_001,
        outcome=Outcome.SUCCESS,
        username="admin",
    )

    response = app.test_client().get("/telemetry/logs", headers=auth_headers)

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 2
    assert body["stats"] == {"total": 2, "success": 1, "failed": 1}
    assert [item["timestamp"] for item in body["items"]] == [1_001, 1_000]


def test_logs_supports_filters_and_pagination(
    app, auth_headers, redis_client: Redis
) -> None:
    seed_event(redis_client, ip="203.0.113.1", timestamp=1_000)
    seed_event(redis_client, ip="203.0.113.2", timestamp=1_001)
    seed_event(
        redis_client,
        ip="198.51.100.7",
        timestamp=1_002,
        outcome=Outcome.SUCCESS,
        username="deploy",
    )

    client = app.test_client()
    filtered = client.get(
        "/telemetry/logs?outcome=success&username=deploy", headers=auth_headers
    )
    assert filtered.status_code == 200
    assert filtered.get_json()["total"] == 1
    assert filtered.get_json()["items"][0]["ip"] == "198.51.100.7"

    paged = client.get("/telemetry/logs?limit=1&offset=1", headers=auth_headers)
    assert paged.status_code == 200
    assert len(paged.get_json()["items"]) == 1

    invalid = client.get("/telemetry/logs?outcome=otro", headers=auth_headers)
    assert invalid.status_code == 400


def test_bans_and_history_are_exposed(
    app, auth_headers, redis_client: Redis
) -> None:
    redis_client.hset(
        IPS_BANNED,
        "203.0.113.42",
        json.dumps(
            {
                "banned_at": 1_000,
                "expires_at": 2_800,
                "duration_min": 30,
                "reason": "SSH brute force",
            }
        ),
    )
    redis_client.lpush(
        IPS_HISTORY,
        json.dumps(
            {
                "ip": "203.0.113.42",
                "action": "banned",
                "banned_at": 1_000,
                "unbanned_at": None,
                "duration_min": 30,
                "reason": "SSH brute force",
                "unban_reason": None,
            }
        ),
    )

    client = app.test_client()
    bans = client.get("/telemetry/bans", headers=auth_headers)
    assert bans.status_code == 200
    assert bans.get_json()["items"][0]["ip"] == "203.0.113.42"

    history = client.get("/telemetry/history", headers=auth_headers)
    assert history.status_code == 200
    assert history.get_json()["total"] == 1
    assert history.get_json()["items"][0]["action"] == "banned"


def test_unban_publishes_the_contract_event(
    app, auth_headers, redis_client: Redis
) -> None:
    redis_client.hset(
        IPS_BANNED,
        "203.0.113.42",
        json.dumps(
            {
                "banned_at": 1_000,
                "expires_at": 2_800,
                "duration_min": 30,
                "reason": "SSH brute force",
            }
        ),
    )

    response = app.test_client().delete(
        "/telemetry/bans/203.0.113.42", headers=auth_headers
    )

    assert response.status_code == 202
    body = response.get_json()
    assert body["ip"] == "203.0.113.42"
    assert body["event_id"]

    messages = redis_client.xrange(STREAM)
    assert len(messages) == 1
    _message_id, fields = messages[0]
    assert fields["action"] == "UNBAN"
    assert fields["ip"] == "203.0.113.42"
    assert fields["requested_by"] == "admin"
    assert int(fields["timestamp"]) <= int(time.time())


def test_unban_unknown_ip_returns_404(app, auth_headers) -> None:
    response = app.test_client().delete(
        "/telemetry/bans/198.51.100.7", headers=auth_headers
    )

    assert response.status_code == 404


def test_unban_invalid_ip_returns_422(app, auth_headers) -> None:
    response = app.test_client().delete(
        "/telemetry/bans/no-es-ip", headers=auth_headers
    )

    assert response.status_code == 422


def test_empty_telemetry_is_reported(app, auth_headers, redis_client: Redis) -> None:
    redis_client.delete(SSH_EVENTS)
    response = app.test_client().get("/telemetry/logs", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [],
        "total": 0,
        "stats": {"total": 0, "success": 0, "failed": 0},
        "limit": 50,
        "offset": 0,
    }
