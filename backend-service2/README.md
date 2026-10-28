# Servicio 2 — Lector de logs SSH y motor de seguridad

Motor continuo que lee el auth log del sistema, parsea los intentos SSH y
evalúa cada fallo contra la configuración que el Servicio 1 guarda en Redis.

**Alcance de esta entrega (Issue #7, Backend B):**

- streaming incremental del archivo (`tail -f`, rotación y truncado);
- parser de intentos fallidos y exitosos de OpenSSH/PAM;
- lectura dinámica de `config:settings` y `config:whitelist`;
- contador deslizante por IP en `failed:<IP>` con TTL = `findtime`;
- decisión `ban_required` al alcanzar `maxretry`.

**Fuera de alcance:** ejecutar `ufw deny`, escribir `ips:banned`, consumir el
stream de desbaneo y el visor del Frontend B.

## Estructura

```text
backend-service2/
├── app/
│   ├── parser.py         # auth.log -> SSHEvent
│   ├── tailer.py         # lectura continua y rotación
│   ├── redis_config.py   # lectura de config:settings y whitelist
│   ├── engine.py         # ventana findtime + umbral maxretry
│   ├── monitor.py        # tailer + parser + engine
│   ├── runner.py         # python -m app
│   └── main.py           # healthcheck Flask
├── tests/                # 53 pruebas con fakeredis
└── scripts/demo_engine.py
```

## Ejecutar el motor

Requiere el `.env` de la raíz (o variables de entorno equivalentes):

```bash
cd backend-service2
python -m pip install -r requirements.txt
python -m app
```

Variables propias:

| Variable | Por defecto | Descripción |
|---|---|---|
| `SSH_LOG_PATH` | `/var/log/auth.log` | Archivo a monitorear (`/var/log/secure` en RHEL). |
| `LOG_READ_FROM_START` | `false` | `false` = solo eventos nuevos; `true` = procesa el archivo completo. |
| `LOG_POLL_INTERVAL` | `0.5` | Segundos entre sondeos. |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | `127.0.0.1:6379/0` | Misma instancia que el Servicio 1. |
| `REDIS_PASSWORD` | vacío | Contraseña de Redis. |

Si el archivo no existe al arrancar, el proceso espera y lo lee desde el
principio cuando aparezca. Si `logrotate` cambia el inodo, reabre el archivo
nuevo; si lo trunca, vuelve al offset 0.

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
```

La suite usa `fakeredis` y no toca la base de desarrollo. El demo imprime el
incremento `1 -> 2 -> 3`, la decisión `ban_required` y el reinicio a `1`
cuando el evento cae fuera de `findtime`.
