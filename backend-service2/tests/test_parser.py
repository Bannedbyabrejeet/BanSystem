"""Pruebas del parser de auth logs SSH."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import Outcome
from app.parser import SSHParser

REFERENCE = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
PARSER = SSHParser()


@pytest.mark.parametrize(
    ("line", "event_type", "username", "ip", "port", "countable"),
    [
        (
            "Oct 28 11:42:01 server sshd[123]: Failed password for root "
            "from 203.0.113.42 port 4242 ssh2",
            "failed_password",
            "root",
            "203.0.113.42",
            4242,
            True,
        ),
        (
            "Oct 28 11:42:02 server sshd[123]: Failed password for invalid user "
            "admin from 198.51.100.7 port 50122 ssh2",
            "failed_password",
            "admin",
            "198.51.100.7",
            50122,
            True,
        ),
        (
            "Oct 28 11:42:03 server sshd[123]: Failed publickey for deploy from "
            "2001:db8::17 port 2222 ssh2",
            "failed_publickey",
            "deploy",
            "2001:db8::17",
            2222,
            True,
        ),
    ],
)
def test_parses_countable_failed_attempts(
    line: str,
    event_type: str,
    username: str,
    ip: str,
    port: int,
    countable: bool,
) -> None:
    event = PARSER.parse(line, reference=REFERENCE)

    assert event is not None
    assert event.outcome is Outcome.FAILED
    assert event.event_type == event_type
    assert event.username == username
    assert event.ip == ip
    assert event.port == port
    assert event.countable is countable
    assert event.raw_line == line


@pytest.mark.parametrize(
    ("line", "event_type"),
    [
        (
            "Oct 28 11:43:01 server sshd[123]: Accepted password for root "
            "from 192.0.2.10 port 22 ssh2",
            "accepted_password",
        ),
        (
            "Oct 28 11:43:02 server sshd[123]: Accepted publickey for deploy "
            "from 2001:db8::20 port 5522 ssh2: RSA SHA256:abc",
            "accepted_publickey",
        ),
    ],
)
def test_parses_successful_attempts(line: str, event_type: str) -> None:
    event = PARSER.parse(line, reference=REFERENCE)

    assert event is not None
    assert event.outcome is Outcome.SUCCESS
    assert event.event_type == event_type
    assert event.ip in {"192.0.2.10", "2001:db8::20"}


@pytest.mark.parametrize(
    ("line", "event_type"),
    [
        (
            "Oct 28 11:44:01 server sshd[123]: Invalid user oracle from "
            "203.0.113.50",
            "invalid_user",
        ),
        (
            "Oct 28 11:44:02 server sshd[123]: pam_unix(sshd:auth): "
            "authentication failure; logname= uid=0 euid=0 tty=ssh ruser= "
            "rhost=203.0.113.51  user=root",
            "pam_failure",
        ),
        (
            "Oct 28 11:44:03 server sshd[123]: Connection closed by "
            "authenticating user root 203.0.113.52 port 4000 [preauth]",
            "connection_closed",
        ),
        (
            "Oct 28 11:44:04 server sshd[123]: error: maximum authentication "
            "attempts exceeded for root from 203.0.113.53 port 4001 ssh2",
            "max_attempts",
        ),
    ],
)
def test_auxiliary_failure_lines_are_not_countable(
    line: str, event_type: str
) -> None:
    event = PARSER.parse(line, reference=REFERENCE)

    assert event is not None
    assert event.outcome is Outcome.FAILED
    assert event.event_type == event_type
    assert event.countable is False


def test_syslog_timestamp_uses_reference_year() -> None:
    line = (
        "Oct 28 11:42:01 server sshd[1]: Failed password for root from "
        "203.0.113.42 port 22 ssh2"
    )
    event = PARSER.parse(line, reference=REFERENCE)

    assert event is not None
    assert event.timestamp == int(
        datetime(2026, 10, 28, 11, 42, 1, tzinfo=timezone.utc).timestamp()
    )


def test_syslog_december_line_processed_in_january_uses_previous_year() -> None:
    line = (
        "Dec 31 23:59:59 server sshd[1]: Failed password for root from "
        "203.0.113.42 port 22 ssh2"
    )
    event = PARSER.parse(line, reference=datetime(2027, 1, 1, tzinfo=timezone.utc))

    assert event is not None
    assert event.timestamp == int(
        datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp()
    )


def test_iso_timestamp_is_supported() -> None:
    line = (
        "2026-10-28T11:42:01+00:00 server sshd[1]: Failed password for root "
        "from 203.0.113.42 port 22 ssh2"
    )
    event = PARSER.parse(line)

    assert event is not None
    assert event.timestamp == int(
        datetime(2026, 10, 28, 11, 42, 1, tzinfo=timezone.utc).timestamp()
    )


def test_line_without_timestamp_uses_reference() -> None:
    line = "Failed password for root from 203.0.113.42 port 22 ssh2"
    event = PARSER.parse(line, reference=REFERENCE)

    assert event is not None
    assert event.timestamp == int(REFERENCE.timestamp())


@pytest.mark.parametrize(
    "line",
    [
        "",
        "   ",
        "Oct 28 11:42:01 server systemd[1]: Started Daily apt download activities.",
        "Oct 28 11:42:01 server sshd[1]: Failed password for root from "
        "999.1.1.1 port 22 ssh2",
    ],
)
def test_non_ssh_or_invalid_lines_return_none(line: str) -> None:
    assert PARSER.parse(line, reference=REFERENCE) is None
