"""API de telemetría del Servicio 2 para el Frontend B (Issue #9).

Expone bajo ``/telemetry``:

* ``GET /logs`` — eventos SSH parseados, con filtros y paginación.
* ``GET /bans`` — IPs baneadas en este momento.
* ``GET /history`` — historial de baneos/desbaneos.
* ``DELETE /bans/<ip>`` — encola una orden de desbaneo manual.

Todas las rutas exigen el JWT emitido por el Servicio 1. El desbaneo se
publica en ``security:events:unban`` para que el worker del proceso motor
ejecute UFW, igual que el flujo de la Issue #8.
"""

from __future__ import annotations

import time
from functools import wraps
from ipaddress import ip_address

from flask import Blueprint, current_app, g, jsonify, request
from redis.exceptions import RedisError

from app.auth import AuthError, authenticate
from app.keys import IPS_BANNED, UNBAN_STREAM
from app.telemetry import MAX_PAGE_SIZE, TelemetryStore

telemetry = Blueprint("telemetry", __name__, url_prefix="/telemetry")


def _error(message: str, status: int = 400):
    return jsonify({"detail": message}), status


def _store() -> TelemetryStore:
    return current_app.extensions["telemetry"]


def _int_arg(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = request.args.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"El parámetro {name} debe ser un entero") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"El parámetro {name} debe estar entre {minimum} y {maximum}")
    return value


def _require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return _error("Sesión no válida", 401)
        try:
            g.identity = authenticate(
                current_app.extensions["redis"],
                current_app.config["SETTINGS"],
                token.strip(),
            )
        except AuthError as exc:
            return _error(str(exc), 401)
        return view(*args, **kwargs)

    return wrapper


@telemetry.get("/logs")
@_require_auth
def list_logs():
    """``GET /telemetry/logs`` — flujo SSH parseado."""
    try:
        limit = _int_arg("limit", 50, 1, MAX_PAGE_SIZE)
        offset = _int_arg("offset", 0, 0, 1_000_000)
    except ValueError as exc:
        return _error(str(exc))

    outcome = (request.args.get("outcome") or "").strip() or None
    if outcome not in (None, "success", "failed"):
        return _error("El resultado debe ser 'success' o 'failed'")

    ip = (request.args.get("ip") or "").strip() or None
    if ip:
        try:
            ip = str(ip_address(ip))
        except ValueError:
            return _error("La IP del filtro no es válida")

    username = (request.args.get("username") or "").strip() or None
    if username and len(username) > 64:
        return _error("El usuario del filtro es demasiado largo")

    page = _store().list_events(
        limit=limit,
        offset=offset,
        outcome=outcome,
        ip=ip,
        username=username,
    )
    return jsonify(
        {
            "items": page.items,
            "total": page.total,
            "stats": {
                "total": page.total,
                "success": page.success,
                "failed": page.failed,
            },
            "limit": limit,
            "offset": offset,
        }
    )


@telemetry.get("/bans")
@_require_auth
def list_bans():
    """``GET /telemetry/bans`` — sanciones activas."""
    bans = _store().list_bans()
    return jsonify({"items": bans, "total": len(bans)})


@telemetry.get("/history")
@_require_auth
def list_history():
    """``GET /telemetry/history`` — historial de baneos y desbaneos."""
    try:
        limit = _int_arg("limit", 50, 1, MAX_PAGE_SIZE)
        offset = _int_arg("offset", 0, 0, 1_000_000)
    except ValueError as exc:
        return _error(str(exc))

    items, total = _store().list_history(limit=limit, offset=offset)
    return jsonify(
        {"items": items, "total": total, "limit": limit, "offset": offset}
    )


@telemetry.delete("/bans/<ip>")
@_require_auth
def request_unban(ip: str):
    """``DELETE /telemetry/bans/<ip>`` — encola el desbaneo manual."""
    try:
        normalized = str(ip_address(ip.strip()))
    except ValueError:
        return _error("La IP no es válida", 422)

    redis = current_app.extensions["redis"]
    if not redis.hexists(IPS_BANNED, normalized):
        return _error("La IP no está baneada en este momento", 404)

    try:
        event_id = redis.xadd(
            UNBAN_STREAM,
            {
                "action": "UNBAN",
                "ip": normalized,
                "requested_by": g.identity.username,
                "timestamp": str(int(time.time())),
            },
            maxlen=10_000,
            approximate=True,
        )
    except RedisError:
        current_app.logger.exception("No se pudo publicar el desbaneo de %s", normalized)
        return _error("No se pudo encolar la solicitud de desbaneo", 503)

    return (
        jsonify(
            {
                "message": "Solicitud de desbaneo encolada",
                "ip": normalized,
                "event_id": event_id,
            }
        ),
        202,
    )
