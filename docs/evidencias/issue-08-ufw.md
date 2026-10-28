# Issue #8 — Integración UFW: bloqueo automático y desbaneo manual

**Fecha:** 2026-10-28  
**Rama:** `10-issue-8-integración-ufw-bloqueo-automático-y-desbaneo-manual`  
**Alcance entregado:** `BACK2-03` (bloqueo automático en UFW) y `BACK2-04`
(desbaneo manual + expiración). Incluye el worker de timeout en Redis y el
consumidor del stream `security:events:unban`.

## 1. Criterios de aceptación

| Criterio | Implementación | Prueba |
|---|---|---|
| Al alcanzar `maxretry`, el Servicio 2 ejecuta `ufw deny from <IP> to any port 22` | `app/ufw.py` + `BanService.ban` invocados desde `LogMonitor._apply_ban` | `tests/test_ufw.py`, `tests/test_bans.py::test_ban_blocks_ufw_and_persists_state`, `tests/test_monitor.py::test_monitor_applies_ufw_ban_when_threshold_is_reached` |
| La IP queda registrada en `ips:banned` con timestamps y duración | `BanService._persist_ban` escribe hash, historial y `bans:expirations` en una transacción | `tests/test_bans.py::test_ban_blocks_ufw_and_persists_state` |
| Transcurrido `bantime`, se elimina la regla UFW automáticamente (US-05) | `BanService.expire_due` + `ZRANGEBYSCORE bans:expirations -inf now`; el monitor lo ejecuta cada `BAN_MAINTENANCE_INTERVAL` | `tests/test_bans.py::test_expire_due_unblocks_only_after_bantime`, `tests/test_bans.py::test_failed_expiration_keeps_the_ban_for_a_retry` |
| El estado pasa de "Baneada" a "Historial" | `BanService.unban` agrega `action="unbanned"` y `unban_reason="timeout"` a `ips:history` | `tests/test_bans.py::test_expire_due_unblocks_only_after_bantime` |
| Se reciben órdenes manuales del dashboard y se remueve el timeout en Redis (US-07) | `UnbanWorker` consume `security:events:unban` (grupo `ufw_workers`), ejecuta `ufw delete deny ...`, `HDEL ips:banned`, `ZREM bans:expirations` y `XACK` | `tests/test_unban_worker.py` |
| Si UFW falla, el baneo no se persiste y el desbaneo se reintenta | `BanService.ban` revierte UFW si Redis falla; `UnbanWorker` no hace `XACK` y usa `XAUTOCLAIM` | `tests/test_bans.py::test_ufw_failure_does_not_persist_the_ban`, `tests/test_unban_worker.py::test_ufw_failure_keeps_the_message_pending_for_retry` |
| Una IP en whitelist no se bloquea | Se mantiene la comprobación de la Issue #7 antes de llegar a UFW | `tests/test_engine.py::test_failed_attempt_from_whitelisted_ip_is_ignored` |

## 2. Pruebas unitarias

Comando:

```bash
cd backend-service2
PYTHONPATH=../backend-service1/.pylibs python -m pytest -q
```

Resultado real:

```text
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 0.26s
```

La suite usa `fakeredis` y un ejecutor UFW falso. No modifica el firewall del
host ni las claves reales del proyecto. El Servicio 1 conserva sus **88 tests**
(se agregaron 3 de regresión para baneo/desbaneo manual).

## 3. Evidencia de consola — bloqueo y expiración (simulación)

Comando:

```bash
cd backend-service2
PYTHONPATH=../backend-service1/.pylibs python scripts/demo_ufw.py
```

Salida real (el reloj de simulación avanza hasta después de `expires_at`):

```text
INFO     [UFW dry-run] sudo -n ufw deny from 203.0.113.42 to any port 22
WARNING  IP 203.0.113.42 bloqueada en UFW hasta 1793201316 (1 min, motivo=SSH brute force)
INFO     [UFW dry-run] sudo -n ufw delete deny from 203.0.113.42 to any port 22
INFO     IP 203.0.113.42 desbloqueada en UFW (timeout, solicitado por service2)
Modo: SIMULACIÓN
IP de prueba: 203.0.113.42
bantime: 1 minuto(s)

Baneo registrado: BanRecord(ip='203.0.113.42', banned_at=1793201256, expires_at=1793201316, duration_min=1, reason='SSH brute force')
ips:banned: {"banned_at": 1793201256, "expires_at": 1793201316, "duration_min": 1, "reason": "SSH brute force"}
bans:expirations: [('203.0.113.42', 1793201316.0)]

Reloj de simulación avanzado hasta después de expires_at

expire_due() -> ['203.0.113.42']
ips:banned después: None
bans:expirations después: []
```

## 3.1. Validación contra Redis real

Además de `fakeredis`, se ejecutó el flujo completo contra un Redis 7.2
efímero en el puerto 6399 (db 14), con un ejecutor UFW falso para no tocar el
firewall:

```text
ban BanRecord(ip='203.0.113.42', banned_at=1793201649, expires_at=1793201709, duration_min=1, reason='SSH brute force') blocked ['203.0.113.42']
hash {"banned_at": 1793201649, "expires_at": 1793201709, "duration_min": 1, "reason": "SSH brute force"}
zset [('203.0.113.42', 1793201709.0)]
history ['{"ip": "203.0.113.42", "action": "banned", "banned_at": 1793201649, "unbanned_at": null, "duration_min": 1, "reason": "SSH brute force", "unban_reason": null}']
processed 1
unblocked ['203.0.113.42'] hash False zset None
pending {'pending': 0, 'min': None, 'max': None, 'consumers': []}
```

Esto valida `HSET`, `ZADD`, `LPUSH`, `XADD`, `XGROUP`, `XREADGROUP`,
`XAUTOCLAIM` y `XACK` contra el motor real, no solo contra el emulador.

## 4. Evidencia real en el host

La prueba se ejecutó en el host de desarrollo con **UFW real**, Redis aislado
en el puerto 6399 y el Servicio 2 corriendo como root
(`UFW_DRY_RUN=false`, `UFW_USE_SUDO=false`).

### 4.1. Estado inicial de UFW

UFW estaba instalado pero **inactivo**:

```text
$ sudo ufw status verbose
Estado: inactivo
```

Aun así, el Servicio 2 escribió correctamente las reglas en
`/etc/ufw/user.rules`:

```text
$ sudo grep -n '203.0.113' /etc/ufw/user.rules
20:### tuple ### deny any 22 0.0.0.0/0 any 203.0.113.70 in
21:-A ufw-user-input -p tcp --dport 22 -s 203.0.113.70 -j DROP
22:-A ufw-user-input -p udp --dport 22 -s 203.0.113.70 -j DROP
24:### tuple ### deny any 22 0.0.0.0/0 any 203.0.113.80 in
25:-A ufw-user-input -p tcp --dport 22 -s 203.0.113.80 -j DROP
26:-A ufw-user-input -p udp --dport 22 -s 203.0.113.80 -j DROP
```

### 4.2. Bloqueo real con UFW activo

Se habilitó UFW permitiendo SSH previamente:

```bash
sudo ufw allow 22/tcp
sudo ufw enable
```

Estado observado:

```text
$ sudo ufw status verbose
Estado: activo
Acceso: on (low)
Predeterminado: deny (entrantes), allow (salientes), deny (enrutados)

Hasta                      Acción      Desde
-----                      ------      -----
22                         DENY IN     203.0.113.70
22                         DENY IN     203.0.113.80
22/tcp                     ALLOW IN    Anywhere
22/tcp (v6)                ALLOW IN    Anywhere (v6)
```

El Servicio 2 ejecutó los comandos reales (sin `dry-run`):

```text
INFO     app.ufw: Ejecutando UFW: ufw deny from 203.0.113.70 to any port 22
WARNING  app.bans: IP 203.0.113.70 bloqueada en UFW hasta 1793202931 (5 min, motivo=SSH brute force)
INFO     app.ufw: Ejecutando UFW: ufw deny from 203.0.113.80 to any port 22
WARNING  app.bans: IP 203.0.113.80 bloqueada en UFW hasta 1793204581 (30 min, motivo=SSH brute force)
```

### 4.3. Expiración automática

Al vencer `bantime`, el worker eliminó la regla sin intervención manual:

```text
INFO     app.ufw: Ejecutando UFW: ufw delete deny from 203.0.113.70 to any port 22
INFO     app.bans: IP 203.0.113.70 desbloqueada en UFW (timeout, solicitado por service2)
WARNING  app.monitor: UFW: baneo vencido, regla eliminada para 203.0.113.70
```

La IP pasó al historial con `unban_reason="timeout"`.

### 4.4. Desbaneo manual

Se llamó `DELETE /api/v1/banned-ips/203.0.113.80` y el worker consumió el
evento del stream:

```text
INFO     app.ufw: Ejecutando UFW: ufw delete deny from 203.0.113.80 to any port 22
INFO     app.bans: IP 203.0.113.80 sin baneo activo en Redis; regla UFW y vencimiento limpiados (manual)
INFO     app.unban_worker: Desbaneo manual confirmado: ip=203.0.113.80 solicitado_por=admin hash_activo=False
```

Después del desbaneo, `sudo ufw show added` solo conservó la regla de SSH:

```text
$ sudo ufw show added
ufw allow 22/tcp
```

Finalmente se repitió el ciclo con `203.0.113.90` y `bantime=2` minutos: el
operador confirmó que la regla apareció en `ufw status` y desapareció sola al
vencer el plazo.

### 4.5. Procedimiento reproducible

Para repetir la prueba en un host con UFW y privilegios:

```bash
cd backend-service2
PYTHONPATH=../backend-service1/.pylibs python scripts/demo_ufw.py --real
```

El script consulta `ufw status`, registra un baneo de prueba, espera el
vencimiento y vuelve a consultar el estado. También se puede verificar con:

```bash
# Mientras el baneo está activo
sudo ufw status | grep 203.0.113.42
redis-cli HGET ips:banned 203.0.113.42
redis-cli ZSCORE bans:expirations 203.0.113.42

# Después del timeout
sudo ufw status | grep 203.0.113.42        # sin salida
redis-cli HEXISTS ips:banned 203.0.113.42  # 0
redis-cli ZSCORE bans:expirations 203.0.113.42  # nil
```

## 5. Evidencia del desbaneo manual (US-07)

Flujo:

1. El dashboard llama `DELETE /api/v1/banned-ips/<IP>` en el Servicio 1.
2. El Servicio 1 elimina el campo de `ips:banned`, agrega la entrada
   `unbanned` al historial y publica:

   ```text
   XADD security:events:unban * action UNBAN ip <IP> requested_by <admin> timestamp <epoch>
   ```

3. El Servicio 2 (`UnbanWorker`) lee el mensaje con el grupo `ufw_workers`,
   ejecuta `ufw delete deny from <IP> to any port 22`, limpia
   `bans:expirations` y confirma con `XACK`.

Prueba automatizada:

```bash
cd backend-service2
PYTHONPATH=../backend-service1/.pylibs python -m pytest -q tests/test_unban_worker.py
```

Resultado:

```text
....                                                                     [100%]
4 passed
```

## 6. Decisiones de seguridad

- La IP se valida con `ipaddress` **antes** de construir el comando; se
  rechazan CIDR y texto arbitrario.
- `subprocess` se ejecuta con lista de argumentos, `shell=False` y timeout;
  no hay interpolación de cadenas en un shell.
- El bloqueo se aplica antes de escribir en Redis. Si la escritura falla, se
  intenta revertir UFW.
- El desbaneo no confirma el mensaje del stream hasta que UFW responde bien;
  los fallos quedan pendientes y se reintentan.
- `UFW_DRY_RUN=true` permite desarrollar sin privilegios y sin tocar el
  firewall.

## 7. Limitaciones conocidas

- UFW debe estar habilitado (`ufw enable`) para que las reglas se apliquen al
  kernel. Si está inactivo, `ufw deny` las escribe en `/etc/ufw/user.rules`
  pero `ufw status` no las muestra como activas. En la prueba real se
  habilitó UFW permitiendo antes el puerto SSH.
- El baneo manual del Servicio 1 (`POST /api/v1/banned-ips/`) registra la
  sanción en Redis y el Servicio 2 la reconcilia para su expiración, pero el
  contrato actual solo define el evento `UNBAN`; no se publica un evento
  `BAN` para forzar la regla UFW de un baneo manual.
- El parser de `ufw status` para `is_blocked` es auxiliar y no se usa en el
  flujo principal de baneo.
