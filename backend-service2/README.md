# Servicio 2 — Lector de logs SSH, motor de seguridad e integración UFW

Motor continuo que lee el auth log del sistema, parsea los intentos SSH,
evalúa cada fallo contra la configuración que el Servicio 1 guarda en Redis y
ejecuta el ciclo de vida completo del baneo: **bloqueo en UFW, expiración
automática y desbaneo manual**.

**Alcance de esta entrega (Issues #7 y #8, Backend B):**

- streaming incremental del archivo (`tail -f`, rotación y truncado);
- parser de intentos fallidos y exitosos de OpenSSH/PAM;
- lectura dinámica de `config:settings` y `config:whitelist`;
- contador deslizante por IP en `failed:<IP>` con TTL = `findtime`;
- decisión `ban_required` al alcanzar `maxretry`;
- **UFW** (US-04): `ufw deny from <IP> to any port 22`;
- **expiración** (US-05): worker sobre `bans:expirations` que ejecuta
  `ufw delete deny ...` y pasa la IP al historial;
- **desbaneo manual** (US-07): consumidor del stream
  `security:events:unban` con el grupo `ufw_workers`.

**Fuera de alcance:** el visor de logs del Frontend B (Vue) y la interfaz de
control de IPs.

## Estructura

```text
backend-service2/
├── app/
│   ├── parser.py         # auth.log -> SSHEvent
│   ├── tailer.py         # lectura continua y rotación
│   ├── redis_config.py   # lectura de config:settings y whitelist
│   ├── engine.py         # ventana findtime + umbral maxretry
│   ├── ufw.py            # ejecutor seguro de comandos UFW
│   ├── bans.py           # ciclo de vida: UFW + ips:banned + expiración
│   ├── unban_worker.py   # consumidor de security:events:unban
│   ├── monitor.py        # tailer + parser + engine + UFW
│   ├── runner.py         # python -m app
│   └── main.py           # healthcheck Flask
├── tests/                # 79 pruebas con fakeredis
└── scripts/
    ├── demo_engine.py    # evidencia del contador y findtime
    └── demo_ufw.py       # evidencia de bloqueo y expiración UFW
```

## Ejecutar el motor

Requiere el `.env` de la raíz (o variables de entorno equivalentes):

```bash
cd backend-service2
python -m pip install -r requirements.txt
python -m app
```

El proceso necesita poder ejecutar `ufw` (root o `sudo` sin contraseña). Para
desarrollo sin privilegios, `UFW_DRY_RUN=true` registra los comandos sin
tocar el firewall.

Variables propias:

| Variable | Por defecto | Descripción |
|---|---|---|
| `SSH_LOG_PATH` | `/var/log/auth.log` | Archivo a monitorear (`/var/log/secure` en RHEL). |
| `LOG_READ_FROM_START` | `false` | `false` = solo eventos nuevos; `true` = procesa el archivo completo. |
| `LOG_POLL_INTERVAL` | `0.5` | Segundos entre sondeos. |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | `127.0.0.1:6379/0` | Misma instancia que el Servicio 1. |
| `REDIS_PASSWORD` | vacío | Contraseña de Redis. |
| `UFW_DRY_RUN` | `false` | Simula UFW (no modifica el firewall). |
| `UFW_BINARY` | `ufw` | Ruta o nombre del binario. |
| `UFW_USE_SUDO` | `true` | Ejecuta `sudo -n ufw ...`. |
| `UFW_SSH_PORT` | `22` | Puerto bloqueado por la regla. |
| `UFW_COMMAND_TIMEOUT` | `10` | Timeout de cada comando UFW. |
| `BAN_MAINTENANCE_INTERVAL` | `5` | Cada cuántos segundos se revisan baneos vencidos. |
| `UNBAN_STREAM` | `security:events:unban` | Stream del contrato de desbaneo. |
| `UNBAN_CONSUMER_GROUP` | `ufw_workers` | Consumer group del stream. |
| `UNBAN_CONSUMER_NAME` | `service2-<host>-<pid>` | Nombre del consumidor. |
| `UNBAN_BLOCK_MS` | `1000` | `XREADGROUP BLOCK` en ms. |
| `UNBAN_BATCH_SIZE` | `10` | Mensajes por iteración. |
| `UNBAN_RETRY_MIN_IDLE_MS` | `5000` | Espera antes de reintentar un mensaje pendiente. |

Si el archivo no existe al arrancar, el proceso espera y lo lee desde el
principio cuando aparezca. Si `logrotate` cambia el inodo, reabre el archivo
nuevo; si lo trunca, vuelve al offset 0.

## Ciclo de vida del baneo

1. `SecurityEngine` detecta `maxretry` fallos dentro de `findtime` y devuelve
   `BAN_REQUIRED`.
2. `BanService.ban` ejecuta `ufw deny from <IP> to any port 22`.
3. Si UFW responde bien, escribe en una transacción:
   - `ips:banned` (hash con `banned_at`, `expires_at`, `duration_min` y
     `reason`);
   - `bans:expirations` (ZSET con score = `expires_at`);
   - `ips:history` (`LPUSH` + `LTRIM` a 1000);
   - borra `failed:<IP>`.
4. Cada `BAN_MAINTENANCE_INTERVAL` segundos, el worker lee
   `ZRANGEBYSCORE bans:expirations -inf now`, ejecuta
   `ufw delete deny from <IP> to any port 22`, elimina el hash y el
   vencimiento y agrega la entrada `unbanned` (`unban_reason="timeout"`).
5. Una orden manual del dashboard llega por `security:events:unban`. El
   `UnbanWorker` valida la IP, ejecuta el mismo desbloqueo, limpia el
   vencimiento y confirma con `XACK`. Si UFW falla, no confirma y reintenta
   con `XAUTOCLAIM`.

La regla se aplica antes de escribir en Redis. Si Redis falla, `BanService`
intenta revertir UFW para no dejar una IP bloqueada sin trazabilidad.

## Healthcheck Flask

```bash
flask --app app.main run --host 127.0.0.1 --port 5000
curl -s http://127.0.0.1:5000/health
```

## Pruebas y evidencia

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/demo_engine.py
python scripts/demo_ufw.py            # simulación, sin root
python scripts/demo_ufw.py --real     # UFW real; requiere sudo/root
```

La suite usa `fakeredis` y un ejecutor UFW falso: no toca la base de
desarrollo ni el firewall. `demo_ufw.py` muestra el comando de bloqueo, el
estado en `ips:banned`/`bans:expirations` y su desaparición al vencer el
tiempo. En modo `--real` consulta `ufw status` antes y después y espera el
`bantime` configurado.

## Evidencia

La evidencia completa de la Issue #8 está en
[`docs/evidencias/issue-08-ufw.md`](../docs/evidencias/issue-08-ufw.md).
