"""Pruebas del ejecutor UFW: comandos, validación y errores."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence

import pytest

from app.ufw import UfwError, UfwExecutor, normalize_ip


class FakeRunner:
    """Captura comandos y devuelve una salida configurable."""

    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.commands: list[list[str]] = []

    def __call__(self, command: Sequence[str], **kwargs) -> subprocess.CompletedProcess[str]:
        self.commands.append(list(command))
        return subprocess.CompletedProcess(
            args=list(command),
            returncode=self.returncode,
            stdout=self.stdout,
            stderr=self.stderr,
        )


def test_block_builds_the_documented_ufw_command() -> None:
    runner = FakeRunner()
    executor = UfwExecutor(use_sudo=False, runner=runner)

    result = executor.block("203.0.113.42")

    assert result.succeeded
    assert runner.commands == [
        [
            "ufw",
            "insert",
            "1",
            "deny",
            "from",
            "203.0.113.42",
            "to",
            "any",
            "port",
            "22",
        ]
    ]


def test_unblock_builds_the_delete_command() -> None:
    runner = FakeRunner()
    executor = UfwExecutor(use_sudo=False, runner=runner)

    executor.unblock("203.0.113.42")

    assert runner.commands == [
        [
            "ufw",
            "delete",
            "deny",
            "from",
            "203.0.113.42",
            "to",
            "any",
            "port",
            "22",
        ]
    ]


def test_sudo_prefix_and_custom_port() -> None:
    runner = FakeRunner()
    executor = UfwExecutor(
        use_sudo=True, ssh_port=2222, binary="/usr/sbin/ufw", runner=runner
    )

    executor.block("2001:db8::1")

    assert runner.commands[0][:3] == ["sudo", "-n", "/usr/sbin/ufw"]
    assert runner.commands[0][-1] == "2222"
    assert "2001:db8::1" in runner.commands[0]


def test_dry_run_does_not_invoke_the_runner() -> None:
    runner = FakeRunner()
    executor = UfwExecutor(dry_run=True, runner=runner)

    result = executor.block("203.0.113.42")

    assert result.succeeded
    assert runner.commands == []


@pytest.mark.parametrize("ip", ["no-es-ip", "203.0.113.0/24", "", "1.2.3.4; rm -rf /"])
def test_invalid_ips_are_rejected_before_running_ufw(ip: str) -> None:
    runner = FakeRunner()
    executor = UfwExecutor(use_sudo=False, runner=runner)

    with pytest.raises(ValueError):
        executor.block(ip)

    assert runner.commands == []


def test_normalize_ip_returns_canonical_form() -> None:
    assert normalize_ip(" 2001:0db8::1 ") == "2001:db8::1"
    assert normalize_ip("192.168.1.10") == "192.168.1.10"


def test_ufw_failure_raises_with_command_and_stderr() -> None:
    runner = FakeRunner(returncode=1, stderr="ERROR: no se pudo aplicar")
    executor = UfwExecutor(use_sudo=False, runner=runner)

    with pytest.raises(UfwError) as exc_info:
        executor.block("203.0.113.42")

    message = str(exc_info.value)
    assert "203.0.113.42" in message
    assert "no se pudo aplicar" in message


def test_unblock_treats_missing_rule_as_success() -> None:
    runner = FakeRunner(
        returncode=1,
        stderr="Could not delete non-existent rule",
    )
    executor = UfwExecutor(use_sudo=False, runner=runner)

    result = executor.unblock("203.0.113.42")

    assert result.returncode == 1
    assert "non-existent" in result.stderr


def test_is_blocked_parses_ufw_status() -> None:
    status = (
        "Status: active\n\n"
        "To                         Action      From\n"
        "--                         ------      ----\n"
        "22/tcp                     DENY        203.0.113.42\n"
    )
    runner = FakeRunner(stdout=status)
    executor = UfwExecutor(use_sudo=False, runner=runner)

    assert executor.is_blocked("203.0.113.42") is True
    assert executor.is_blocked("198.51.100.7") is False
