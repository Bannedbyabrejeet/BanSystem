"""Pruebas del consumidor de órdenes de desbaneo (US-07)."""

from __future__ import annotations

from redis import Redis

from app.bans import BanService
from app.keys import CONFIG_SETTINGS, IPS_BANNED, UNBAN_STREAM
from app.unban_worker import UnbanWorker
from tests.test_bans import Clock, FakeExecutor


def make_worker(redis_client: Redis, executor: FakeExecutor | None = None) -> UnbanWorker:
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "3", "bantime": "30", "findtime": "5"},
    )
    bans = BanService(
        redis_client,
        executor or FakeExecutor(),
        clock=Clock(1_000),
    )
    worker = UnbanWorker(
        redis_client,
        bans,
        consumer="test-worker",
        block_ms=0,
        retry_min_idle_ms=0,
    )
    worker.ensure_group()
    return worker


def publish(redis_client: Redis, **fields: str) -> str:
    payload = {
        "action": "UNBAN",
        "ip": "203.0.113.42",
        "requested_by": "admin",
        "timestamp": "1000",
        **fields,
    }
    return redis_client.xadd(UNBAN_STREAM, payload)


def pending_count(redis_client: Redis) -> int:
    summary = redis_client.xpending(UNBAN_STREAM, "ufw_workers")
    return int(summary["pending"])


def test_manual_unban_message_removes_ufw_rule_and_acks(
    redis_client: Redis,
) -> None:
    executor = FakeExecutor()
    worker = make_worker(redis_client, executor)
    redis_client.hset(
        IPS_BANNED,
        "203.0.113.42",
        '{"banned_at": 900, "expires_at": 2700, "duration_min": 30, "reason": "SSH brute force"}',
    )
    message_id = publish(redis_client)

    processed = worker.process_once(block_ms=0)

    assert processed == 1
    assert executor.unblocked == ["203.0.113.42"]
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 0
    assert pending_count(redis_client) == 0
    assert redis_client.xpending_range(
        UNBAN_STREAM, "ufw_workers", min="-", max="+", count=10
    ) == []
    assert message_id


def test_invalid_ip_is_discarded_and_acked(redis_client: Redis) -> None:
    worker = make_worker(redis_client)
    publish(redis_client, ip="no-es-ip")

    assert worker.process_once(block_ms=0) == 0
    assert pending_count(redis_client) == 0


def test_unknown_action_is_discarded_and_acked(redis_client: Redis) -> None:
    worker = make_worker(redis_client)
    publish(redis_client, action="BAN")

    assert worker.process_once(block_ms=0) == 0
    assert pending_count(redis_client) == 0


def test_ufw_failure_keeps_the_message_pending_for_retry(
    redis_client: Redis,
) -> None:
    executor = FakeExecutor(fail_unblock=True)
    worker = make_worker(redis_client, executor)
    redis_client.hset(
        IPS_BANNED,
        "203.0.113.42",
        '{"banned_at": 900, "expires_at": 2700, "duration_min": 30, "reason": "SSH brute force"}',
    )
    publish(redis_client)

    assert worker.process_once(block_ms=0) == 0
    assert pending_count(redis_client) == 1
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 1

    executor.fail_unblock = False
    assert worker.process_once(block_ms=0) == 1
    assert pending_count(redis_client) == 0
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 0
