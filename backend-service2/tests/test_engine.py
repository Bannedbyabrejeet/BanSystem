"""Pruebas del motor de conteo, whitelist y ventana ``findtime``."""

from __future__ import annotations

import pytest
from redis import Redis

from app.engine import SecurityEngine
from app.keys import CONFIG_SETTINGS, CONFIG_WHITELIST, IPS_BANNED, failed_attempts_key
from app.models import EngineAction, Outcome, SSHEvent


def make_event(
    ip: str = "203.0.113.42",
    timestamp: int = 1_000,
    *,
    outcome: Outcome = Outcome.FAILED,
    countable: bool = True,
    username: str | None = "root",
) -> SSHEvent:
    return SSHEvent(
        timestamp=timestamp,
        ip=ip,
        username=username,
        outcome=outcome,
        event_type="failed_password" if outcome is Outcome.FAILED else "accepted_password",
        raw_line="linea de prueba",
        countable=countable,
    )


def configure(
    redis_client: Redis, *, maxretry: int = 3, findtime: int = 5
) -> None:
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={
            "maxretry": str(maxretry),
            "bantime": "30",
            "findtime": str(findtime),
        },
    )


def test_failed_attempts_increment_until_threshold(redis_client: Redis) -> None:
    configure(redis_client, maxretry=3, findtime=5)
    engine = SecurityEngine(redis_client)

    first = engine.process(make_event(timestamp=1_000))
    second = engine.process(make_event(timestamp=1_010))
    third = engine.process(make_event(timestamp=1_020))

    assert first.action is EngineAction.COUNTED
    assert first.attempts_in_window == 1
    assert second.attempts_in_window == 2
    assert third.action is EngineAction.BAN_REQUIRED
    assert third.should_ban is True
    assert third.attempts_in_window == 3
    assert third.maxretry == 3
    assert third.findtime_seconds == 300
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 3


def test_counter_ttl_is_renewed_with_every_failure(redis_client: Redis) -> None:
    configure(redis_client, findtime=5)
    engine = SecurityEngine(redis_client)

    engine.process(make_event(timestamp=1_000))
    ttl_first = redis_client.ttl(failed_attempts_key("203.0.113.42"))
    engine.process(make_event(timestamp=1_001))
    ttl_second = redis_client.ttl(failed_attempts_key("203.0.113.42"))

    assert 0 < ttl_first <= 300
    assert 0 < ttl_second <= 300


def test_attempts_outside_findtime_are_discarded(redis_client: Redis) -> None:
    configure(redis_client, maxretry=3, findtime=5)
    engine = SecurityEngine(redis_client)
    key = failed_attempts_key("203.0.113.42")

    engine.process(make_event(timestamp=1_000))
    engine.process(make_event(timestamp=1_050))
    assert redis_client.zcard(key) == 2

    # 1400 - 300 = 1100: los dos intentos anteriores quedan fuera de la ventana.
    decision = engine.process(make_event(timestamp=1_400))

    assert decision.action is EngineAction.COUNTED
    assert decision.attempts_in_window == 1
    assert redis_client.zcard(key) == 1
    remaining = redis_client.zrange(key, 0, -1, withscores=True)
    assert [score for _, score in remaining] == [1_400.0]


def test_attempt_exactly_on_window_boundary_is_counted(
    redis_client: Redis,
) -> None:
    configure(redis_client, maxretry=3, findtime=5)
    engine = SecurityEngine(redis_client)

    engine.process(make_event(timestamp=1_000))
    decision = engine.process(make_event(timestamp=1_300))

    assert decision.attempts_in_window == 2


def test_attempt_one_second_after_boundary_resets_counter(
    redis_client: Redis,
) -> None:
    configure(redis_client, maxretry=3, findtime=5)
    engine = SecurityEngine(redis_client)

    engine.process(make_event(timestamp=1_000))
    decision = engine.process(make_event(timestamp=1_301))

    assert decision.attempts_in_window == 1


def test_settings_are_read_on_every_event(redis_client: Redis) -> None:
    configure(redis_client, maxretry=5, findtime=5)
    engine = SecurityEngine(redis_client)

    engine.process(make_event(timestamp=1_000))
    engine.process(make_event(timestamp=1_001))

    # El administrador baja el umbral desde el dashboard (Servicio 1).
    configure(redis_client, maxretry=2, findtime=5)
    decision = engine.process(make_event(timestamp=1_002))

    assert decision.maxretry == 2
    assert decision.action is EngineAction.BAN_REQUIRED


@pytest.mark.parametrize("whitelist_entry", ["203.0.113.42", "203.0.113.0/24"])
def test_failed_attempt_from_whitelisted_ip_is_ignored(
    redis_client: Redis, whitelist_entry: str
) -> None:
    configure(redis_client)
    redis_client.sadd(CONFIG_WHITELIST, whitelist_entry)
    engine = SecurityEngine(redis_client)

    decision = engine.process(make_event(timestamp=1_000))

    assert decision.action is EngineAction.WHITELISTED
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 0


def test_successful_attempt_is_recognized_without_incrementing(
    redis_client: Redis,
) -> None:
    configure(redis_client)
    engine = SecurityEngine(redis_client)

    decision = engine.process(make_event(outcome=Outcome.SUCCESS))

    assert decision.action is EngineAction.SUCCESS
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 0


def test_auxiliary_failure_line_does_not_increment(redis_client: Redis) -> None:
    configure(redis_client)
    engine = SecurityEngine(redis_client)

    decision = engine.process(make_event(countable=False))

    assert decision.action is EngineAction.NOT_COUNTABLE
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 0


def test_already_banned_ip_is_not_counted(redis_client: Redis) -> None:
    configure(redis_client)
    redis_client.hset(IPS_BANNED, "203.0.113.42", "{}")
    engine = SecurityEngine(redis_client)

    decision = engine.process(make_event(timestamp=1_000))

    assert decision.action is EngineAction.ALREADY_BANNED
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 0


def test_each_ip_has_an_independent_counter(redis_client: Redis) -> None:
    configure(redis_client, maxretry=2)
    engine = SecurityEngine(redis_client)

    engine.process(make_event(ip="203.0.113.1", timestamp=1_000))
    decision = engine.process(make_event(ip="203.0.113.2", timestamp=1_001))

    assert decision.attempts_in_window == 1
    assert redis_client.zcard(failed_attempts_key("203.0.113.1")) == 1
    assert redis_client.zcard(failed_attempts_key("203.0.113.2")) == 1
