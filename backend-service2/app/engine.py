"""Motor de reglas del Servicio 2.

Para cada intento fallido:

1. contrasta la IP contra ``config:whitelist`` (US-08);
2. descarta los intentos de esa IP anteriores a ``findtime`` (US-09);
3. agrega el intento actual al ZSET ``failed:<IP>`` y renueva su TTL;
4. compara el contador con ``maxretry`` y emite una decisión.

Este módulo **no ejecuta UFW** ni escribe ``ips:banned``: mantiene la
decisión desacoplada y testeable. El consumidor de ``BAN_REQUIRED`` es
:mod:`app.bans`, que aplica la regla de firewall y persiste la sanción.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from uuid import uuid4

from redis import Redis

from app.keys import IPS_BANNED, failed_attempts_key
from app.models import EngineAction, EngineDecision, Outcome, SSHEvent
from app.redis_config import RedisConfigReader


class SecurityEngine:
    """Evalúa eventos SSH y mantiene el contador deslizante por IP."""

    def __init__(
        self,
        redis: Redis,
        config_reader: RedisConfigReader | None = None,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self.redis = redis
        self.config_reader = config_reader or RedisConfigReader(redis)
        self.clock = clock or (lambda: int(time.time()))

    def process(self, event: SSHEvent) -> EngineDecision:
        """Evalúa un evento y devuelve la decisión del motor.

        Los intentos exitosos se reconocen y se descartan sin tocar el
        contador. Un fallo de una IP en la whitelist tampoco incrementa nada.
        """
        if event.outcome is Outcome.SUCCESS:
            return EngineDecision(EngineAction.SUCCESS, event.ip)

        whitelist = self.config_reader.match_whitelist(event.ip)
        if whitelist.matched:
            return EngineDecision(EngineAction.WHITELISTED, event.ip)

        if not event.countable:
            # Línea auxiliar de un fallo ya contado por ``Failed ...``.
            return EngineDecision(EngineAction.NOT_COUNTABLE, event.ip)

        settings = self.config_reader.get_settings()

        # Si otra componente ya registró el baneo, no se sigue acumulando.
        if self.redis.hexists(IPS_BANNED, event.ip):
            return EngineDecision(
                EngineAction.ALREADY_BANNED,
                event.ip,
                maxretry=settings.maxretry,
                findtime_seconds=settings.findtime_seconds,
            )

        attempt_timestamp = event.timestamp or self.clock()
        attempts = self._record_attempt(
            ip=event.ip,
            timestamp=attempt_timestamp,
            findtime_seconds=settings.findtime_seconds,
        )

        action = (
            EngineAction.BAN_REQUIRED
            if attempts >= settings.maxretry
            else EngineAction.COUNTED
        )
        return EngineDecision(
            action=action,
            ip=event.ip,
            attempts_in_window=attempts,
            maxretry=settings.maxretry,
            findtime_seconds=settings.findtime_seconds,
        )

    def _record_attempt(
        self, ip: str, timestamp: int, findtime_seconds: int
    ) -> int:
        """Registra un fallo y devuelve cuántos quedan dentro de la ventana.

        La transacción agrupa limpieza, alta, conteo y renovación de TTL para
        que dos eventos consecutivos no observen un contador intermedio.
        """
        key = failed_attempts_key(ip)
        window_start = timestamp - findtime_seconds
        member = f"{timestamp}:{uuid4().hex}"

        pipe = self.redis.pipeline(transaction=True)
        # Se elimina lo estrictamente anterior a la ventana; un intento en el
        # borde exacto sigue siendo parte de ella (sintaxis Redis "(score").
        pipe.zremrangebyscore(key, "-inf", f"({window_start}")
        pipe.zadd(key, {member: float(timestamp)})
        pipe.zcard(key)
        pipe.expire(key, findtime_seconds)
        results = pipe.execute()
        return int(results[2])

    def reset(self, ip: str) -> None:
        """Borra el contador de una IP (útil para pruebas o desbaneo futuro)."""
        self.redis.delete(failed_attempts_key(ip))
