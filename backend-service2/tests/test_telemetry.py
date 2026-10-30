"""Pruebas del almacén de telemetría del Frontend B (Issue #9)."""

from __future__ import annotations

import json

from redis import Redis

from app.keys import IPS_BANNED, IPS_HISTORY, SSH_EVENTS
from app.models import Outcome, SSHEvent
from app.telemetry import TelemetryStore


def make_event(
    ip: str = "203.0.113.42",
    timestamp: int = 1_000,
    *,
    outcome: Outcome = Outcome.FAILED,
    username: str | None = "root",
    event_type: str = "failed_password",
) -> SSHEvent:
    return SSHEvent(
        timestamp=timestamp,
        ip=ip,
        username=username,
        outcome=outcome,
        event_type=event_type,
        raw_line=f"{event_type} from {ip}",
        countable=True,
        port=22,
    )


def test_record_event_keeps_newest_first_and_respects_limit(
    redis_client: Redis,
) -> None:
    store = TelemetryStore(redis_client, event_limit=2)

    store.record_event(make_event(timestamp=1_000))
    store.record_event(make_event(timestamp=1_001))
    store.record_event(make_event(timestamp=1_002))

    items = json.loads(redis_client.lrange(SSH_EVENTS, 0, -1)[0])
    assert items["timestamp"] == 1_002
    assert redis_client.llen(SSH_EVENTS) == 2


def test_list_events_filters_and_reports_stats(redis_client: Redis) -> None:
    store = TelemetryStore(redis_client)
    store.record_event(
        make_event(ip="203.0.113.1", timestamp=1_000, outcome=Outcome.FAILED)
    )
    store.record_event(
        make_event(
            ip="203.0.113.2",
            timestamp=1_001,
            outcome=Outcome.SUCCESS,
            event_type="accepted_password",
        )
    )
    store.record_event(
        make_event(
            ip="198.51.100.7",
            timestamp=1_002,
            outcome=Outcome.FAILED,
            username="admin",
        )
    )

    page = store.list_events(limit=10)
    assert page.total == 3
    assert page.success == 1
    assert page.failed == 2
    assert [item["timestamp"] for item in page.items] == [1_002, 1_001, 1_000]

    successes = store.list_events(outcome="success")
    assert successes.total == 1
    assert successes.items[0]["ip"] == "203.0.113.2"

    by_ip = store.list_events(ip="198.51.100.7")
    assert by_ip.total == 1
    assert by_ip.items[0]["username"] == "admin"

    by_user = store.list_events(username="ADM")
    assert by_user.total == 1

    page_two = store.list_events(limit=1, offset=1)
    assert page_two.total == 3
    assert len(page_two.items) == 1
    assert page_two.items[0]["timestamp"] == 1_001


def test_list_bans_sorts_by_banned_at(redis_client: Redis) -> None:
    redis_client.hset(
        IPS_BANNED,
        mapping={
            "203.0.113.1": json.dumps(
                {
                    "banned_at": 1_000,
                    "expires_at": 2_000,
                    "duration_min": 30,
                    "reason": "SSH brute force",
                }
            ),
            "203.0.113.2": json.dumps(
                {
                    "banned_at": 1_500,
                    "expires_at": 2_500,
                    "duration_min": 30,
                    "reason": "Manual administration",
                }
            ),
        },
    )

    bans = TelemetryStore(redis_client).list_bans()

    assert [ban["ip"] for ban in bans] == ["203.0.113.2", "203.0.113.1"]
    assert bans[0]["reason"] == "Manual administration"


def test_list_history_paginates(redis_client: Redis) -> None:
    for index in range(3):
        redis_client.lpush(
            IPS_HISTORY,
            json.dumps(
                {
                    "ip": f"203.0.113.{index}",
                    "action": "banned",
                    "banned_at": 1_000 + index,
                }
            ),
        )

    store = TelemetryStore(redis_client)
    items, total = store.list_history(limit=2, offset=0)
    assert total == 3
    assert [item["ip"] for item in items] == ["203.0.113.2", "203.0.113.1"]

    second_page, _ = store.list_history(limit=2, offset=2)
    assert [item["ip"] for item in second_page] == ["203.0.113.0"]
