"""Pruebas del ciclo de vida del baneo: UFW, Redis y expiración."""

from __future__ import annotations

import json

import pytest
from redis import Redis

from app.bans import BanError, BanRecord, BanService
from app.keys import (
    BAN_EXPIRATIONS,
    CONFIG_SETTINGS,
    IPS_BANNED,
    IPS_HISTORY,
    failed_attempts_key,
)
from app.ufw import UfwError


class FakeExecutor:
    """Doble del ejecutor UFW que registra bloqueos y desbloqueos."""

    def __init__(self, *, fail_block: bool = False, fail_unblock: bool = False) -> None:
        self.fail_block = fail_block
        self.fail_unblock = fail_unblock
        self.blocked: list[str] = []
        self.unblocked: list[str] = []

    def block(self, ip: str) -> None:
        if self.fail_block:
            raise UfwError(f"fallo simulado al bloquear {ip}")
        self.blocked.append(ip)

    def unblock(self, ip: str) -> None:
        if self.fail_unblock:
            raise UfwError(f"fallo simulado al desbloquear {ip}")
        self.unblocked.append(ip)


class Clock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def executor() -> FakeExecutor:
    return FakeExecutor()


@pytest.fixture
def service(
    redis_client: Redis, executor: FakeExecutor, clock: Clock
) -> BanService:
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "3", "bantime": "30", "findtime": "5"},
    )
    return BanService(redis_client, executor, clock=clock)


def test_ban_blocks_ufw_and_persists_state(
    service: BanService, executor: FakeExecutor, redis_client: Redis, clock: Clock
) -> None:
    redis_client.zadd(failed_attempts_key("203.0.113.42"), {"event": 1_000})

    record = service.ban("203.0.113.42")

    assert executor.blocked == ["203.0.113.42"]
    assert record.banned_at == 1_000
    assert record.expires_at == 1_000 + 30 * 60
    assert record.duration_min == 30

    stored = json.loads(redis_client.hget(IPS_BANNED, "203.0.113.42"))
    assert stored["banned_at"] == 1_000
    assert stored["expires_at"] == 2_800
    assert stored["reason"] == "SSH brute force"

    assert redis_client.zscore(BAN_EXPIRATIONS, "203.0.113.42") == 2_800.0
    # El contador de intentos se limpia al quedar la IP sancionada.
    assert redis_client.exists(failed_attempts_key("203.0.113.42")) == 0

    history = json.loads(redis_client.lindex(IPS_HISTORY, 0))
    assert history["action"] == "banned"
    assert history["unbanned_at"] is None


def test_banning_twice_does_not_duplicate_the_ufw_rule(
    service: BanService, executor: FakeExecutor
) -> None:
    service.ban("203.0.113.42")
    service.ban("203.0.113.42")

    assert executor.blocked == ["203.0.113.42"]


def test_ufw_failure_does_not_persist_the_ban(
    redis_client: Redis, clock: Clock
) -> None:
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "3", "bantime": "30", "findtime": "5"},
    )
    executor = FakeExecutor(fail_block=True)
    service = BanService(redis_client, executor, clock=clock)

    with pytest.raises(BanError):
        service.ban("203.0.113.42")

    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 0
    assert redis_client.exists(BAN_EXPIRATIONS) == 0


def test_expire_due_unblocks_only_after_bantime(
    service: BanService,
    executor: FakeExecutor,
    redis_client: Redis,
    clock: Clock,
) -> None:
    service.ban("203.0.113.42")

    clock.advance(30 * 60 - 1)
    assert service.expire_due() == []
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 1

    clock.advance(1)
    assert service.expire_due() == ["203.0.113.42"]
    assert executor.unblocked == ["203.0.113.42"]
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 0
    assert redis_client.zscore(BAN_EXPIRATIONS, "203.0.113.42") is None

    history = json.loads(redis_client.lindex(IPS_HISTORY, 0))
    assert history["action"] == "unbanned"
    assert history["unban_reason"] == "timeout"
    assert history["unbanned_at"] == 2_800


def test_failed_expiration_keeps_the_ban_for_a_retry(
    redis_client: Redis, clock: Clock
) -> None:
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "3", "bantime": "1", "findtime": "5"},
    )
    executor = FakeExecutor()
    service = BanService(redis_client, executor, clock=clock)
    service.ban("203.0.113.42")

    executor.fail_unblock = True
    clock.advance(60)
    assert service.expire_due() == []
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 1
    assert redis_client.zscore(BAN_EXPIRATIONS, "203.0.113.42") is not None

    executor.fail_unblock = False
    assert service.expire_due() == ["203.0.113.42"]


def test_manual_unban_removes_rule_state_and_timeout(
    service: BanService,
    executor: FakeExecutor,
    redis_client: Redis,
    clock: Clock,
) -> None:
    service.ban("203.0.113.42")
    clock.advance(10)

    removed = service.unban("203.0.113.42", reason="manual", requested_by="admin")

    assert removed is True
    assert executor.unblocked == ["203.0.113.42"]
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 0
    assert redis_client.zscore(BAN_EXPIRATIONS, "203.0.113.42") is None

    history = json.loads(redis_client.lindex(IPS_HISTORY, 0))
    assert history["action"] == "unbanned"
    assert history["unban_reason"] == "manual"


def test_manual_unban_without_hash_still_cleans_ufw_and_timeout(
    service: BanService, executor: FakeExecutor, redis_client: Redis
) -> None:
    """El Servicio 1 borra el hash antes de publicar la orden de desbaneo."""
    redis_client.zadd(BAN_EXPIRATIONS, {"203.0.113.42": 9_999})

    removed = service.unban("203.0.113.42", reason="manual")

    assert removed is False
    assert executor.unblocked == ["203.0.113.42"]
    assert redis_client.zscore(BAN_EXPIRATIONS, "203.0.113.42") is None


def test_reconcile_restores_expiration_and_removes_expired(
    redis_client: Redis, clock: Clock
) -> None:
    executor = FakeExecutor()
    service = BanService(redis_client, executor, clock=clock)
    redis_client.hset(
        IPS_BANNED,
        mapping={
            "203.0.113.42": BanRecord(
                ip="203.0.113.42",
                banned_at=1_000,
                expires_at=1_500,
                duration_min=10,
            ).to_json(),
            "198.51.100.7": BanRecord(
                ip="198.51.100.7",
                banned_at=1_000,
                expires_at=5_000,
                duration_min=60,
            ).to_json(),
        },
    )
    clock.value = 2_000

    expired = service.reconcile()

    assert expired == ["203.0.113.42"]
    assert executor.unblocked == ["203.0.113.42"]
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 0
    assert redis_client.hexists(IPS_BANNED, "198.51.100.7") == 1
    assert redis_client.zscore(BAN_EXPIRATIONS, "198.51.100.7") == 5_000.0


def test_invalid_ip_is_rejected(service: BanService) -> None:
    with pytest.raises(ValueError):
        service.ban("203.0.113.0/24")
