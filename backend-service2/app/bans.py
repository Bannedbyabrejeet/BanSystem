"""Ciclo de vida de un baneo: UFW + Redis (Issue #8).

Responsabilidades:

* **Baneo automático (US-04):** al recibir ``BAN_REQUIRED`` del motor, ejecuta
  ``ufw deny from <IP> to any port 22`` y persiste la sanción en
  ``ips:banned`` e ``ips:history``.
* **Expiración (US-05):** mantiene el ZSET ``bans:expirations`` con el
  instante de vencimiento. Un worker llama a :meth:`BanService.expire_due`
  y elimina la regla de UFW y el registro de Redis.
* **Desbaneo manual (US-07):** :meth:`BanService.unban` elimina la regla,
  borra el vencimiento y deja el historial correspondiente.

El hash ``ips:banned`` no admite TTL por campo, por eso el vencimiento se
guarda en un ZSET aparte ordenado por ``expires_at``. Así el worker solo lee
las IPs vencidas (``ZRANGEBYSCORE -inf now``) y no recorre todo el hash.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from redis import Redis

from app.keys import (
    BAN_EXPIRATIONS,
    IPS_BANNED,
    IPS_HISTORY,
    failed_attempts_key,
)
from app.redis_config import RedisConfigReader
from app.ufw import UfwExecutor, UfwError, normalize_ip

logger = logging.getLogger(__name__)

#: Tope de entradas del historial (``LTRIM``), igual que el Servicio 1.
HISTORY_LIMIT: Final[int] = 1_000
#: Motivo por defecto del baneo automático.
AUTO_BAN_REASON: Final[str] = "SSH brute force"


class BanError(RuntimeError):
    """No se pudo completar el ciclo de baneo/desbaneo."""


@dataclass(frozen=True, slots=True)
class BanRecord:
    """Sanción activa guardada en ``ips:banned``."""

    ip: str
    banned_at: int
    expires_at: int
    duration_min: int
    reason: str = AUTO_BAN_REASON

    def to_json(self) -> str:
        return json.dumps(
            {
                "banned_at": self.banned_at,
                "expires_at": self.expires_at,
                "duration_min": self.duration_min,
                "reason": self.reason,
            }
        )

    @classmethod
    def from_json(cls, ip: str, payload: str | bytes) -> "BanRecord | None":
        try:
            data = json.loads(payload.decode() if isinstance(payload, bytes) else payload)
            return cls(
                ip=ip,
                banned_at=int(data.get("banned_at", 0)),
                expires_at=int(data.get("expires_at", 0)),
                duration_min=int(data.get("duration_min", 0)),
                reason=str(data.get("reason", AUTO_BAN_REASON)),
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            logger.warning("Registro corrupto en ips:banned para %s", ip)
            return None


class BanService:
    """Orquesta UFW y las claves Redis del ciclo de vida del baneo."""

    def __init__(
        self,
        redis: Redis,
        executor: UfwExecutor,
        config_reader: RedisConfigReader | None = None,
        *,
        clock: Callable[[], int] | None = None,
        history_limit: int = HISTORY_LIMIT,
    ) -> None:
        self.redis = redis
        self.executor = executor
        self.config_reader = config_reader or RedisConfigReader(redis)
        self.clock = clock or (lambda: int(time.time()))
        self.history_limit = history_limit

    # ------------------------------------------------------------------
    # US-04 — baneo automático
    # ------------------------------------------------------------------
    def ban(
        self,
        ip: str,
        *,
        reason: str = AUTO_BAN_REASON,
    ) -> BanRecord:
        """Bloquea la IP en UFW y registra la sanción en Redis.

        La regla de firewall se aplica **antes** de escribir en Redis. Si la
        escritura falla, se intenta revertir UFW para no dejar una IP
        bloqueada sin trazabilidad.
        """
        normalized = normalize_ip(ip)

        existing = self.redis.hget(IPS_BANNED, normalized)
        if existing is not None:
            record = BanRecord.from_json(normalized, existing)
            if record is not None:
                logger.info("La IP %s ya estaba baneada; no se duplica la regla", normalized)
                return record

        settings = self.config_reader.get_settings()
        duration_min = settings.bantime
        now = self.clock()
        expires_at = now + duration_min * 60
        record = BanRecord(
            ip=normalized,
            banned_at=now,
            expires_at=expires_at,
            duration_min=duration_min,
            reason=reason,
        )

        try:
            self.executor.block(normalized)
        except UfwError as exc:
            logger.critical("No se pudo bloquear %s en UFW: %s", normalized, exc)
            raise BanError(str(exc)) from exc

        history_entry = {
            "ip": normalized,
            "action": "banned",
            "banned_at": now,
            "unbanned_at": None,
            "duration_min": duration_min,
            "reason": reason,
            "unban_reason": None,
        }

        try:
            self._persist_ban(record, history_entry)
        except Exception as exc:  # Redis caído o respuesta inesperada
            logger.critical(
                "El baneo de %s se aplicó en UFW pero no se pudo guardar en Redis: %s",
                normalized,
                exc,
            )
            self._rollback_ufw(normalized)
            raise BanError(f"No se pudo persistir el baneo de {normalized}: {exc}") from exc

        logger.warning(
            "IP %s bloqueada en UFW hasta %s (%d min, motivo=%s)",
            normalized,
            expires_at,
            duration_min,
            reason,
        )
        return record

    def _persist_ban(self, record: BanRecord, history_entry: dict[str, object]) -> None:
        """Escribe hash, vencimiento, historial y limpia el contador."""
        pipe = self.redis.pipeline(transaction=True)
        pipe.hset(IPS_BANNED, record.ip, record.to_json())
        pipe.zadd(BAN_EXPIRATIONS, {record.ip: float(record.expires_at)})
        # La IP ya está sancionada: el contador de intentos deja de ser útil.
        pipe.delete(failed_attempts_key(record.ip))
        pipe.lpush(IPS_HISTORY, json.dumps(history_entry))
        pipe.ltrim(IPS_HISTORY, 0, self.history_limit - 1)
        pipe.execute()

    def _rollback_ufw(self, ip: str) -> None:
        try:
            self.executor.unblock(ip)
        except UfwError as exc:
            logger.critical(
                "No se pudo revertir la regla UFW de %s tras fallar Redis: %s",
                ip,
                exc,
            )

    # ------------------------------------------------------------------
    # US-05 / US-07 — desbaneo (automático o manual)
    # ------------------------------------------------------------------
    def unban(
        self,
        ip: str,
        *,
        reason: str = "manual",
        requested_by: str | None = None,
    ) -> bool:
        """Elimina la regla UFW y el estado del baneo en Redis.

        Returns:
            ``True`` si había un baneo activo en ``ips:banned``; ``False`` si
            solo se limpió el vencimiento (por ejemplo, porque el Servicio 1
            ya había borrado el hash al procesar la orden manual).
        """
        normalized = normalize_ip(ip)
        raw_record = self.redis.hget(IPS_BANNED, normalized)

        # Primero el firewall: si UFW falla, Redis conserva el baneo y el
        # worker volverá a intentarlo en el siguiente ciclo.
        try:
            self.executor.unblock(normalized)
        except UfwError as exc:
            logger.error(
                "No se pudo eliminar la regla UFW de %s (%s); se reintentará",
                normalized,
                exc,
            )
            raise BanError(str(exc)) from exc

        now = self.clock()
        pipe = self.redis.pipeline(transaction=True)
        pipe.hdel(IPS_BANNED, normalized)
        pipe.zrem(BAN_EXPIRATIONS, normalized)
        pipe.delete(failed_attempts_key(normalized))

        record = (
            BanRecord.from_json(normalized, raw_record)
            if raw_record is not None
            else None
        )
        if record is not None:
            history_entry = {
                "ip": normalized,
                "action": "unbanned",
                "banned_at": record.banned_at,
                "unbanned_at": now,
                "duration_min": record.duration_min,
                "reason": record.reason,
                "unban_reason": reason,
            }
            pipe.lpush(IPS_HISTORY, json.dumps(history_entry))
            pipe.ltrim(IPS_HISTORY, 0, self.history_limit - 1)

        pipe.execute()

        if record is not None:
            logger.info(
                "IP %s desbloqueada en UFW (%s%s)",
                normalized,
                reason,
                f", solicitado por {requested_by}" if requested_by else "",
            )
        else:
            logger.info(
                "IP %s sin baneo activo en Redis; regla UFW y vencimiento limpiados (%s)",
                normalized,
                reason,
            )
        return record is not None

    def expire_due(self, now: int | None = None) -> list[str]:
        """Desbanea las IPs cuyo ``expires_at`` ya venció.

        Returns:
            Lista de IPs desbloqueadas en esta pasada. Las que fallen en UFW
            permanecen en ``bans:expirations`` para reintentar después.
        """
        current = self.clock() if now is None else now
        due = self.redis.zrangebyscore(BAN_EXPIRATIONS, "-inf", current)
        expired: list[str] = []

        for raw_ip in due:
            ip = raw_ip.decode() if isinstance(raw_ip, bytes) else raw_ip
            try:
                self.unban(ip, reason="timeout", requested_by="service2")
            except (BanError, ValueError) as exc:
                logger.error("Baneo vencido de %s no pudo retirarse: %s", ip, exc)
                continue
            expired.append(ip)

        return expired

    # ------------------------------------------------------------------
    # Reconciliación tras un reinicio
    # ------------------------------------------------------------------
    def reconcile(self, now: int | None = None) -> list[str]:
        """Sincroniza ``bans:expirations`` con ``ips:banned``.

        Cubre dos casos:

        * el proceso se reinició y perdió el ZSET (se reconstruye desde el
          ``expires_at`` del hash);
        * el Servicio 1 creó un baneo manual y el Servicio 2 debe conocer su
          vencimiento.

        Devuelve las IPs que ya estaban vencidas y se desbloquearon.
        """
        current = self.clock() if now is None else now
        raw_bans = self.redis.hgetall(IPS_BANNED)
        active_ips: set[str] = set()

        for raw_ip, payload in raw_bans.items():
            ip = raw_ip.decode() if isinstance(raw_ip, bytes) else raw_ip
            record = BanRecord.from_json(ip, payload)
            if record is None or record.expires_at <= 0:
                continue
            active_ips.add(ip)
            self.redis.zadd(BAN_EXPIRATIONS, {ip: float(record.expires_at)})

        # Entradas de vencimiento sin baneo asociado (por ejemplo, borrado
        # manual desde Redis): se descartan.
        for raw_ip in self.redis.zrange(BAN_EXPIRATIONS, 0, -1):
            ip = raw_ip.decode() if isinstance(raw_ip, bytes) else raw_ip
            if ip not in active_ips:
                self.redis.zrem(BAN_EXPIRATIONS, ip)

        if not active_ips:
            logger.debug("Reconciliación de baneos: no hay sanciones activas")
            return []

        expired = self.expire_due(current)
        if expired:
            logger.info(
                "Reconciliación de baneos: %d activos, %d vencidos desbloqueados",
                len(active_ips),
                len(expired),
            )
        else:
            logger.debug(
                "Reconciliación de baneos: %d sanciones activas", len(active_ips)
            )
        return expired
