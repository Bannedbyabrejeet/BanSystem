"""Prueba de integración: archivo de log -> parser -> motor -> Redis."""

from __future__ import annotations

from pathlib import Path

from redis import Redis

from app.bans import BanService
from app.engine import SecurityEngine
from app.keys import CONFIG_SETTINGS, CONFIG_WHITELIST, IPS_BANNED, failed_attempts_key
from app.models import EngineAction
from app.monitor import LogMonitor
from app.parser import SSHParser
from app.tailer import LogTailer
from tests.test_bans import Clock, FakeExecutor


def append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def test_monitor_processes_file_lines_and_applies_config(
    tmp_path: Path, redis_client: Redis
) -> None:
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "2", "bantime": "30", "findtime": "5"},
    )
    redis_client.sadd(CONFIG_WHITELIST, "198.51.100.0/24")

    path = tmp_path / "auth.log"
    path.write_text("", encoding="utf-8")
    monitor = LogMonitor(
        LogTailer(path, from_start=True),
        SSHParser(),
        SecurityEngine(redis_client),
    )

    append(
        path,
        "Oct 28 11:42:01 server sshd[1]: Failed password for root from "
        "203.0.113.42 port 22 ssh2\n",
    )
    first = monitor.process_available()
    assert [decision.action for decision in first] == [EngineAction.COUNTED]

    append(
        path,
        "Oct 28 11:42:02 server sshd[1]: Failed password for root from "
        "203.0.113.42 port 23 ssh2\n",
    )
    second = monitor.process_available()
    assert [decision.action for decision in second] == [EngineAction.BAN_REQUIRED]
    assert second[0].attempts_in_window == 2
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 2

    # Whitelist y éxito no tocan el contador de la IP atacante.
    append(
        path,
        "Oct 28 11:42:03 server sshd[1]: Failed password for root from "
        "198.51.100.7 port 24 ssh2\n"
        "Oct 28 11:42:04 server sshd[1]: Accepted password for root from "
        "203.0.113.42 port 25 ssh2\n",
    )
    third = monitor.process_available()
    assert [decision.action for decision in third] == [
        EngineAction.WHITELISTED,
        EngineAction.SUCCESS,
    ]
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 2


def test_monitor_ignores_non_ssh_lines(tmp_path: Path, redis_client: Redis) -> None:
    path = tmp_path / "auth.log"
    path.write_text(
        "Oct 28 11:42:01 server systemd[1]: Started something.\n",
        encoding="utf-8",
    )
    monitor = LogMonitor(
        LogTailer(path, from_start=True),
        SSHParser(),
        SecurityEngine(redis_client),
    )

    assert monitor.process_available() == []


def test_monitor_applies_ufw_ban_when_threshold_is_reached(
    tmp_path: Path, redis_client: Redis
) -> None:
    """US-04: ``ban_required`` ejecuta UFW y persiste ``ips:banned``."""
    redis_client.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "2", "bantime": "30", "findtime": "5"},
    )
    executor = FakeExecutor()
    bans = BanService(redis_client, executor, clock=Clock(1_000))

    path = tmp_path / "auth.log"
    path.write_text("", encoding="utf-8")
    monitor = LogMonitor(
        LogTailer(path, from_start=True),
        SSHParser(),
        SecurityEngine(redis_client),
        ban_service=bans,
        maintenance_interval=0,
    )

    lines = [
        "Oct 28 11:42:01 server sshd[1]: Failed password for root from "
        "203.0.113.42 port 22 ssh2\n",
        "Oct 28 11:42:02 server sshd[1]: Failed password for root from "
        "203.0.113.42 port 23 ssh2\n",
    ]
    decisions = monitor.process_lines(lines)

    assert decisions[-1].action is EngineAction.BAN_REQUIRED
    assert executor.blocked == ["203.0.113.42"]
    assert redis_client.hexists(IPS_BANNED, "203.0.113.42") == 1
    # El contador se limpia al banear.
    assert redis_client.zcard(failed_attempts_key("203.0.113.42")) == 0
