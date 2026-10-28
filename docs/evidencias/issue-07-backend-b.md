# Issue #7 — Lector de logs SSH y motor de seguridad (Backend B)

**Fecha:** 2026-10-28  
**Rama:** `9-issue-7-lector-de-logs-ssh-y-motor-de-seguridad-backend-b`  
**Alcance entregado:** `BACK2-01` (lector/parser) y `BACK2-02` (motor de reglas,
whitelist y `findtime`). **No incluye UFW ni escritura de `ips:banned`.**

## 1. Criterios de aceptación

| Criterio | Implementación | Prueba |
|---|---|---|
| El Servicio 2 lee los parámetros que guarda el Servicio 1 en Redis | `app/redis_config.py` lee `config:settings` y `config:whitelist` en cada evento | `tests/test_config_reader.py`, `tests/test_engine.py::test_settings_are_read_on_every_event` |
| El parser distingue accesos fallidos y exitosos | `app/parser.py` reconoce `Failed ...`, `Accepted ...` y líneas PAM/auxiliares | `tests/test_parser.py` |
| La IP de un fallo se contrasta con la whitelist y se ignora si coincide | `SecurityEngine.process` + soporte de IP exacta y CIDR | `tests/test_engine.py::test_failed_attempt_from_whitelisted_ip_is_ignored` |
| Se descartan los fallos fuera de `findtime` al momento del último intento | ZSET `failed:<IP>`: `ZREMRANGEBYSCORE`, `ZADD`, `ZCARD` y `EXPIRE` en una transacción | `tests/test_engine.py::test_attempts_outside_findtime_are_discarded` |
| Contadores incrementan y se reinician al expirar `findtime` | Evidencia de consola del demo | `scripts/demo_engine.py` |

## 2. Pruebas unitarias

Comando:

```bash
cd backend-service2
PYTHONPATH=../backend-service1/.pylibs python -m pytest -q
```

Resultado real:

```text
.....................................................                    [100%]
53 passed in 0.29s
```

La suite cubre parser, tail con rotación/truncado, lectura de Redis,
whitelist exacta/CIDR/IPv6, incremento, umbral, TTL, reset por ventana,
éxito sin incremento y healthcheck Flask.

## 3. Evidencia de consola

Comando:

```bash
cd backend-service2
PYTHONPATH=../backend-service1/.pylibs python scripts/demo_engine.py
```

Salida real:

```text
config: maxretry=3 bantime=30 findtime=1 minuto (60 s)
ventana evaluada al momento de cada intento

t=1000s  accion=counted      contador=1  ZCARD=1
t=1010s  accion=counted      contador=2  ZCARD=2
t=1020s  accion=ban_required contador=3  ZCARD=3
t=1400s  accion=counted      contador=1  ZCARD=1  <- findtime expirado, contador reiniciado
t=1401s  accion=whitelisted  contador=0  ZCARD=0  <- whitelist, sin incremento
```

## 4. Validación adicional contra Redis real

Además de `fakeredis`, se ejecutó el motor contra un contenedor efímero
`redis:7.2-alpine` en el puerto 6399 (sin tocar la base de desarrollo):

```text
1000 counted 1 1
1010 counted 2 2
1020 ban_required 3 3
1400 counted 1 1 ttl 60
```

El resultado confirma que Redis real acepta la transacción con
`ZREMRANGEBYSCORE ... (<score)`, renueva el TTL a 60 s (`findtime=1`) y
reinicia el contador cuando los intentos quedan fuera de la ventana.

## 5. Contrato Redis utilizado

- `config:settings` → `maxretry`, `bantime`, `findtime` (minutos). Defaults
  `5 / 30 / 10` si la clave o un campo faltan.
- `config:whitelist` → IPs y redes CIDR. `127.0.0.1` y `::1` se consideran
  protegidas incluso si Redis aún no las contiene.
- `failed:<IP>` → ZSET con score = timestamp UNIX del intento. El TTL se
  renueva a `findtime * 60` en cada fallo. Los intentos anteriores al inicio
  de la ventana se eliminan antes de contar el actual.
- `ips:banned` → solo lectura: si la IP ya está baneada por otra componente,
  el motor no acumula más intentos.

## 6. Decisión al alcanzar el umbral

El motor devuelve `EngineAction.BAN_REQUIRED` y registra en consola una
advertencia. En esta entrega **no ejecuta UFW** ni escribe `ips:banned`,
porque esa orden de firewall pertenece a la siguiente etapa
(`BACK2-03`/`BACK2-04`). De este modo la decisión queda desacoplada y es
testeable sin privilegios de root.

> **Continuación:** la Issue #8 conecta esta decisión con
> `backend-service2/app/bans.py` y `app/ufw.py`. Ver
> [`issue-08-ufw.md`](issue-08-ufw.md).
