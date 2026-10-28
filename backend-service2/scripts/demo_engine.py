"""Demostración reproducible del contador y del reset por ``findtime``.

Usa ``fakeredis`` para no tocar la base real del proyecto::

    cd backend-service2
    python -m pip install -r requirements-dev.txt
    python scripts/demo_engine.py

El resultado muestra el incremento 1 -> 2 -> 3 (umbral) y, tras avanzar el
reloj más allá de la ventana, el reinicio del contador a 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar el script desde backend-service2/ sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fakeredis  # noqa: E402

from app.engine import SecurityEngine  # noqa: E402
from app.keys import CONFIG_SETTINGS, CONFIG_WHITELIST, failed_attempts_key  # noqa: E402
from app.models import Outcome, SSHEvent  # noqa: E402


def event(ip: str, timestamp: int, username: str = "root") -> SSHEvent:
    return SSHEvent(
        timestamp=timestamp,
        ip=ip,
        username=username,
        outcome=Outcome.FAILED,
        event_type="failed_password",
        raw_line=(
            f"Failed password for {username} from {ip} port 22 ssh2"
        ),
    )


def main() -> int:
    redis = fakeredis.FakeRedis(decode_responses=True)
    redis.hset(
        CONFIG_SETTINGS,
        mapping={"maxretry": "3", "bantime": "30", "findtime": "1"},
    )
    redis.sadd(CONFIG_WHITELIST, "127.0.0.1", "::1", "10.0.0.0/8")

    engine = SecurityEngine(redis)
    ip = "203.0.113.42"
    key = failed_attempts_key(ip)

    print("config: maxretry=3 bantime=30 findtime=1 minuto (60 s)")
    print("ventana evaluada al momento de cada intento\n")

    for timestamp in (1_000, 1_010, 1_020):
        decision = engine.process(event(ip, timestamp))
        print(
            f"t={timestamp}s  accion={decision.action.value:<12} "
            f"contador={decision.attempts_in_window}  ZCARD={redis.zcard(key)}"
        )

    # 1_400 - 60 = 1_340: los tres intentos anteriores quedaron fuera.
    decision = engine.process(event(ip, 1_400))
    print(
        f"t=1400s  accion={decision.action.value:<12} "
        f"contador={decision.attempts_in_window}  ZCARD={redis.zcard(key)}"
        "  <- findtime expirado, contador reiniciado"
    )

    redis.sadd(CONFIG_WHITELIST, "198.51.100.0/24")
    whitelisted = engine.process(event("198.51.100.7", 1_401))
    print(
        f"t=1401s  accion={whitelisted.action.value:<12} "
        f"contador={whitelisted.attempts_in_window}  "
        f"ZCARD={redis.zcard(failed_attempts_key('198.51.100.7'))}"
        "  <- whitelist, sin incremento"
    )

    redis.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
