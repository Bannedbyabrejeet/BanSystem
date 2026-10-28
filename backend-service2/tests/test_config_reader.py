"""Pruebas de lectura de ``config:settings`` y ``config:whitelist``."""

from __future__ import annotations

import pytest
from redis import Redis

from app.keys import CONFIG_SETTINGS, CONFIG_WHITELIST
from app.models import BanSettings
from app.redis_config import RedisConfigReader


def test_defaults_when_redis_is_empty(redis_client: Redis) -> None:
    reader = RedisConfigReader(redis_client)

    assert reader.get_settings() == BanSettings(maxretry=5, bantime=30, findtime=10)


def test_reads_parameters_saved_by_service1(redis_client: Redis) -> None:
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "3", "bantime": "15", "findtime": "2"},
    )

    settings = RedisConfigReader(redis_client).get_settings()

    assert settings == BanSettings(maxretry=3, bantime=15, findtime=2)
    assert settings.findtime_seconds == 120


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"maxretry": "no-es-numero"}, BanSettings()),
        ({"maxretry": "0", "bantime": "-1", "findtime": "999999"}, BanSettings()),
        ({"maxretry": "999999"}, BanSettings()),
    ],
)
def test_invalid_fields_fall_back_to_defaults(
    redis_client: Redis, raw: dict[str, str], expected: BanSettings
) -> None:
    redis_client.hset(CONFIG_SETTINGS, mapping=raw)

    assert RedisConfigReader(redis_client).get_settings() == expected


def test_whitelist_always_contains_local_entries(redis_client: Redis) -> None:
    entries = RedisConfigReader(redis_client).get_whitelist()

    assert entries == ("127.0.0.1", "::1")


@pytest.mark.parametrize(
    ("entry", "ip", "matched"),
    [
        ("192.0.2.10", "192.0.2.10", True),
        ("192.0.2.0/24", "192.0.2.55", True),
        ("2001:db8::/32", "2001:db8::99", True),
        ("10.0.0.0/8", "192.0.2.10", False),
        ("2001:db8::/32", "192.0.2.10", False),
    ],
)
def test_matches_exact_ips_and_cidr_networks(
    redis_client: Redis, entry: str, ip: str, matched: bool
) -> None:
    redis_client.sadd(CONFIG_WHITELIST, entry)

    result = RedisConfigReader(redis_client).match_whitelist(ip)

    assert result.matched is matched
    if matched:
        assert result.entry == entry


def test_localhost_is_whitelisted_even_if_missing_in_redis(
    redis_client: Redis,
) -> None:
    reader = RedisConfigReader(redis_client)

    assert reader.match_whitelist("127.0.0.1").matched is True
    assert reader.match_whitelist("::1").matched is True


def test_invalid_whitelist_entry_is_ignored(redis_client: Redis) -> None:
    redis_client.sadd(CONFIG_WHITELIST, "no-es-una-red")

    result = RedisConfigReader(redis_client).match_whitelist("203.0.113.9")

    assert result.matched is False


def test_invalid_source_ip_is_not_whitelisted(redis_client: Redis) -> None:
    assert RedisConfigReader(redis_client).match_whitelist("no-es-ip").matched is False
