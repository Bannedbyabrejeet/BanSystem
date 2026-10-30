"""Demostración del bloqueo y la expiración automática en UFW (Issue #8).

Modo seguro (por defecto): simula los comandos UFW y usa ``fakeredis``. No
necesita root ni modifica el firewall.

Modo real (``--real``): ejecuta ``ufw`` de verdad y espera ``--minutes``
minutos antes de llamar al worker de expiración. Usa ``fakeredis`` para no
tocar las claves reales del proyecto y bloquea una IP de documentación
(``203.0.113.42``) que no debería existir en la red local.

Ejemplos::

    cd backend-service2
    python scripts/demo_ufw.py                 # simulación
    python scripts/demo_ufw.py --real          # requiere sudo/root
    python scripts/demo_ufw.py --real --dry-run --minutes 1
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

# Permite ejecutar el script desde backend-service2/ sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fakeredis  # noqa: E402

from app.bans import BanService  # noqa: E402
from app.keys import BAN_EXPIRATIONS, CONFIG_SETTINGS, IPS_BANNED  # noqa: E402
from app.ufw import UfwExecutor  # noqa: E402


def show_status(use_sudo: bool) -> None:
    command = ["sudo", "-n", "ufw", "status"] if use_sudo else ["ufw", "status"]
    print(f"\n$ {' '.join(command)}")
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"No se pudo consultar UFW: {exc}")
        return
    print((completed.stdout or completed.stderr).rstrip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", default="203.0.113.42", help="IP de prueba")
    parser.add_argument(
        "--minutes",
        type=int,
        default=1,
        help="Duración del baneo en minutos (se espera ese tiempo en modo real)",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Ejecuta UFW de verdad (requiere sudo sin contraseña o root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Con --real, registra los comandos sin modificar el firewall",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="No espera: fuerza la expiración inmediatamente",
    )
    parser.add_argument(
        "--no-sudo",
        action="store_true",
        help="Ejecuta 'ufw' directamente (útil si el proceso ya es root)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    if args.minutes < 1:
        print("--minutes debe ser >= 1")
        return 2

    redis = fakeredis.FakeRedis(decode_responses=True)
    redis.hset(
        CONFIG_SETTINGS,
        mapping={
            "maxretry": "1",
            "bantime": str(args.minutes),
            "findtime": "1",
        },
    )
    executor = UfwExecutor(
        use_sudo=not args.no_sudo,
        dry_run=(not args.real) or args.dry_run,
    )

    # En simulación (o con --no-wait) se adelanta el reloj; en modo real se
    # espera el tiempo configurado para que la regla desaparezca de verdad.
    use_fake_clock = (not args.real) or args.no_wait
    clock_state = {"now": int(time.time())}

    def fake_clock() -> int:
        return clock_state["now"]

    service = BanService(redis, executor, clock=fake_clock if use_fake_clock else None)

    print(f"Modo: {'REAL' if args.real else 'SIMULACIÓN'}")
    print(f"IP de prueba: {args.ip}")
    print(f"bantime: {args.minutes} minuto(s)")

    if args.real and not args.dry_run:
        show_status(use_sudo=not args.no_sudo)

    record = service.ban(args.ip)
    print(f"\nBaneo registrado: {record}")
    print(f"ips:banned: {redis.hget(IPS_BANNED, args.ip)}")
    print(
        "bans:expirations:",
        redis.zrange(BAN_EXPIRATIONS, 0, -1, withscores=True),
    )

    if args.real and not args.dry_run:
        show_status(use_sudo=not args.no_sudo)

    if use_fake_clock:
        clock_state["now"] = record.expires_at + 1
        print("\nReloj de simulación avanzado hasta después de expires_at")
    else:
        wait_seconds = args.minutes * 60 + 2
        print(f"\nEsperando {wait_seconds}s para que venza el baneo...")
        time.sleep(wait_seconds)

    expired = service.expire_due()
    print(f"\nexpire_due() -> {expired}")
    print(f"ips:banned después: {redis.hget(IPS_BANNED, args.ip)}")
    print(
        "bans:expirations después:",
        redis.zrange(BAN_EXPIRATIONS, 0, -1, withscores=True),
    )

    if args.real and not args.dry_run:
        show_status(use_sudo=not args.no_sudo)

    redis.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
