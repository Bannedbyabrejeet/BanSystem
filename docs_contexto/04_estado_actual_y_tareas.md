# Bannedbyabrejeet: Estado Actual y Tareas Pendientes

> **Última actualización:** 2026-10-30
> **Rama activa:** `11-issue-9-visor-formateado-de-logs-ssh-y-estado-de-ips-frontend-b`
> **Rama de referencia:** `main` — incluye las Issues #1 a #8 y #24 mergeadas
> **Entregado hasta ahora:** Servicio 1 (FastAPI) + Frontend A (React) + Servicio 2 (Flask/motor/UFW) + Frontend B (Vue). **La Issue #9 agrega el visor de logs SSH, el estado de IPs y el desbaneo manual en `frontend-ops/`, con la API `/telemetry` del Servicio 2.**

Este documento reemplaza las estimaciones iniciales por el **estado real del repositorio**. Indica qué issues están cerradas, cuáles en curso y qué queda por hacer, con la evidencia correspondiente.

---

## 1. Resumen de Issues

| Issue | Título | Estado | Evidencia |
|---|---|---|---|
| **#1** | Estrategia de integración de frontends (spike) | ✅ Resuelta | `docs/ADR001-UnificacionMultifrontend.md` |
| **#2** | Comunicación inter-servicios / desbaneo (spike) | ✅ Definida | `docs/contrato-desbaneo.yaml`, `docs/REDIS_SCHEMA.md` |
| **#3** | Privilegios de Docker y ruta de logs SSH (spike) | ⏳ Pendiente | — |
| **#4** | Setup de infraestructura y base de datos (Redis) | ✅ Completada | `docker-compose.yml`, `redis/redis.conf`, `scripts/verify_redis.sh`, `docs/DOCKER_REDIS.md` |
| **#5** | Autenticación de administrador | ✅ Completada | `backend-service1/`, `frontend-admin/`, `README.md` |
| **#6** | Parámetros de baneo, findtime y whitelist (API + vista) | ✅ Completada | `app/api/v1/endpoints/config.py`, `app/services/config_service.py`, `tests/test_config_api.py`, `frontend-admin/src/components/config/` |
| **#7** | Servicio 2: lector de logs SSH y motor de seguridad (Backend B) | ✅ Completada | `backend-service2/`, `tests/`, `docs/evidencias/issue-07-backend-b.md` |
| **#8** | Integración UFW, expiración y desbaneo manual (Backend B) | ✅ Completada | `backend-service2/app/ufw.py`, `bans.py`, `unban_worker.py`, `docs/evidencias/issue-08-ufw.md` |
| **#9** | Visor de logs SSH y estado de IPs (Frontend B) | ✅ Completada | `frontend-ops/`, `backend-service2/app/api.py`, `telemetry.py`, `docs/evidencias/issue-09-frontend-b.md` |
| **#24** | Migración de bcrypt a Argon2id | ✅ Completada | `backend-service1/app/core/security.py` |

**Leyenda:** ✅ Cerrada · 🚧 En curso · ⏳ Pendiente

> La API del Servicio 1 para IPs baneadas, historial y desbaneo manual
> (`/api/v1/banned-ips/`, merge `df10bbf`) ya está en `main`. La Issue #8
> completó el **Backend B** (UFW, expiración y stream de desbaneo) y la Issue
> #9 agregó la consola operativa Vue con logs, estado de IPs e historial.

---

## 2. Lo implementado (detalle)

### 2.1 Infraestructura Redis — Issue #4

- Redis **7.2-alpine** dockerizado en el contenedor `bannedbyabrejeet_redis`.
- Publicado en **`127.0.0.1:6379`** (solo loopback del host); el backend corre en la máquina y lo alcanza por loopback, no por una red de Docker.
- Persistencia **híbrida AOF + RDB** sobre el volumen nombrado `redis_data` (`appendonly yes`, snapshots `900/1`, `300/10`, `60/10000`).
- Contraseña obligatoria vía `REDIS_PASSWORD` (`--requirepass`, inyectada desde `.env`).
- Healthcheck nativo (`redis-cli ... ping`) y script de verificación `scripts/verify_redis.sh`.
- Esquema de claves completo y acordado inter-servicios en `docs/REDIS_SCHEMA.md`.

### 2.2 Autenticación de administrador — Issue #5

Claves Redis (detalle en `docs/REDIS_SCHEMA.md`):

- `admin:credentials`: string JSON persistente (sin TTL) con `admin_id`, `username`, `password_hash`, `email`, timestamps y `session_version`.
- `admin:initialized`: marcador permanente sin TTL.
- `admin:reset_tokens`: set sin TTL que indexa los tokens emitidos (`<admin_id>|<token>`) para revocar enlaces anteriores.
- `reset_token:<token>`: string JSON temporal creado con `SETEX` y TTL de **900 s** (configurable con `RESET_TOKEN_TTL`).

Comportamiento:

- **Setup único y atómico** mediante script Lua: comprueba `admin:initialized` y `admin:credentials` y escribe ambas en una sola operación. Peticiones simultáneas no pueden crear dos administradores (la segunda recibe `409`).
- **Login con JWT** firmado en HMAC-SHA256, con `iss`, `aud`, `sub`, `jti`, `iat`, `nbf`, `exp`, rol y `session_version`.
- **Recuperación de contraseña**: token aleatorio opaco de 256 bits; solo existe **un enlace vigente** por administrador. El reset incrementa `session_version`, de modo que todos los JWT previos dejan de ser válidos.
- **Política de contraseñas**: mínimo 12 caracteres, al menos una mayúscula, una minúscula y un dígito, rechazo de contraseñas comunes y tope de **1024 bytes**.

Endpoints expuestos (bajo `/api/v1`):

| Método | Ruta | Resultado |
|---|---|---|
| `GET` | `/auth/status` | `{ "initialized": bool }` |
| `POST` | `/auth/setup` | Crea la cuenta única; después responde `409` |
| `POST` | `/auth/login` | JWT; credenciales incorrectas: `401` |
| `POST` | `/auth/forgot-password` | Crea el token con `SETEX` y envía el enlace |
| `GET` | `/auth/verify-reset-token/{token}` | Indica si Redis todavía conserva el token |
| `POST` | `/auth/reset-password` | Consume el token, cambia el hash e invalida sesiones previas |
| `GET` | `/auth/me` | Valida el JWT y su versión contra Redis |

### 2.3 Migración de bcrypt a Argon2id — Issue #24

- Dependencia **`argon2-cffi==25.1.0`** en lugar de `bcrypt`.
- Algoritmo **Argon2id** (`argon2.Type.ID`) con `m=65536 KiB` (64 MiB), `t=3`, `p=4`, `hash_len=32`, `salt_len=16` (por encima del mínimo recomendado por OWASP).
- Parámetros configurables con `ARGON2_TIME_COST`, `ARGON2_MEMORY_COST_KIB` y `ARGON2_PARALLELISM`; el validador exige `memory_cost_kib >= 8 × parallelism`.
- Se elimina el truncamiento a 72 bytes propio de bcrypt; el límite de 1024 bytes queda solo como defensa anti-DoS durante el hashing.
- Formato del hash en runtime: `$argon2id$v=19$m=65536,t=3,p=4$...`.

### 2.4 Correo electrónico (SMTP)

- Dos modos según `MAIL_MODE`:
  - `log` (por defecto, desarrollo): escribe el enlace completo en el log del backend.
  - `smtp`: entrega el mensaje con `smtplib`, soportando STARTTLS (`SMTP_USE_TLS`) o SSL directo (`SMTP_USE_SSL`).
- El envío se ejecuta en un hilo aparte para no bloquear el event loop de FastAPI.
- Probado contra **Gmail** (`smtp.gmail.com:587` con contraseña de aplicación). El enlace se envía siempre al **correo del administrador registrado**, y `MAIL_FROM` debe coincidir con `SMTP_USERNAME`.
- **Corrección aplicada:** `mail_service.py` construía las cabeceras con objetos `Header`, que fallan en Python 3.12 (`'Header' object is not subscriptable`). Ahora se pasan `str` y es `EmailMessage` el que aplica RFC 2047. El bug estaba latente porque los tests corren con `MAIL_MODE=log`.

### 2.5 Frontend A (Administración) — React

- **React 18 + Vite 5 + React Router 6** en `frontend-admin/`.
- Vistas: `/setup`, `/login`, `/forgot-password`, `/reset-password` y `/dashboard`.
- JWT en `sessionStorage` (se pierde al cerrar la pestaña); guardas `ProtectedRoute` / `PublicOnlyRoute`.
- Cliente Axios con `ApiError` y mensajes idénticos a los del backend (`app/core/constants.py` ↔ `src/constants/messages.js`).
- El Dashboard muestra la sesión activa, el formulario de parámetros de baneo y la lista blanca. Las secciones de IPs baneadas y logs siguen como marcadores de las issues #7 y #8.

### 2.6 Configuración de baneos y whitelist — Issue #6

Claves Redis (detalle en `docs/REDIS_SCHEMA.md` §2 y §3):

- `config:settings` (hash persistente): `maxretry`, `bantime` y `findtime`. Si falta la clave o un campo es inválido se usan `5`, `30` y `10`.
- `config:whitelist` (set persistente): IPs IPv4/IPv6 y redes CIDR normalizadas. `127.0.0.1` y `::1` se reinsertan en cada lectura y no pueden eliminarse (`409`).

Endpoints bajo `/api/v1/config` (todos con JWT):

| Método | Ruta | Resultado |
|---|---|---|
| `GET` | `/settings` | Valores vigentes; defaults si la clave no existe |
| `PUT` | `/settings` | Persiste los tres enteros positivos estrictos juntos |
| `GET` | `/whitelist` | Entradas ordenadas y `protected_entries` |
| `POST` | `/whitelist` | Agrega IP/subred; normaliza `10.1.2.3/8` a `10.0.0.0/8` |
| `DELETE` | `/whitelist?entry=...` | Baja de una entrada; `409` para IPs locales |

En el Frontend A, los componentes `BanSettingsForm` y `WhitelistPanel` viven en `src/components/config/` (fuera de `ui.jsx`) y el dashboard los integra en un layout ancho. La validación de enteros, IPv4, IPv6 y CIDR se replica en `src/utils/validation.js`.

### 2.7 Pruebas

- **88 tests** en `backend-service1/tests/` (seguridad, autenticación, configuración y baneos).
- Si no se define `TEST_REDIS_URL`, se ejecutan 18 y se omiten 70 (las que necesitan Redis).
- Requieren un **Redis aparte del de desarrollo** (por ejemplo `redis://127.0.0.1:6399/15`), porque hacen `FLUSHDB`.

### 2.8 Lector de logs SSH y motor de seguridad — Issue #7 (Backend B)

Implementado en `backend-service2/` (Python + Flask para el healthcheck):

- **Lector continuo** (`app/tailer.py`): parte al final del archivo por defecto
  (`LOG_READ_FROM_START=false`), espera líneas parciales, detecta truncado y
  rotación por inodo.
- **Parser** (`app/parser.py`): reconoce `Failed password/publickey/...` y
  `Accepted ...` de OpenSSH, además de líneas PAM, `Invalid user`, conexiones
  cerradas y `maximum authentication attempts exceeded`. Las líneas auxiliares
  se marcan como no contables para no duplicar el mismo intento.
- **Motor** (`app/engine.py`): lee `config:settings` y `config:whitelist` en
  cada evento; ignora éxitos, IPs en whitelist (IP exacta o CIDR) e IPs ya
  baneadas; mantiene `failed:<IP>` como ZSET con limpieza por `findtime`,
  transacción `MULTI/EXEC` y TTL renovado. Devuelve `ban_required` al alcanzar
  `maxretry`.
- **Monitoreo y consola** (`app/monitor.py`): imprime el contador `n/maxretry`
  y la ventana en segundos; `python -m app` inicia el proceso continuo.
- **Pruebas:** 53 tests originales de la Issue #7 con `fakeredis` (parser,
  tail, Redis, whitelist, contador, reset por `findtime`, healthcheck).
  Evidencia en `docs/evidencias/issue-07-backend-b.md`.

### 2.9 Integración UFW, expiración y desbaneo manual — Issue #8 (Backend B)

- **Ejecutor UFW** (`app/ufw.py`): construye `ufw insert 1 deny from <IP> to
  any port 22` (para que la denegación tenga prioridad sobre un
  `allow 22/tcp` general) y `ufw delete deny from <IP> to any port 22`.
  Valida la IP con `ipaddress`, usa `subprocess` sin shell y soporta
  `UFW_DRY_RUN`.
- **Ciclo de vida** (`app/bans.py`): al banear escribe `ips:banned`,
  `bans:expirations` (ZSET por `expires_at`) e `ips:history`; borra
  `failed:<IP>`. Si Redis falla tras aplicar UFW, revierte la regla.
- **Expiración (US-05):** cada `BAN_MAINTENANCE_INTERVAL` segundos se leen
  los vencidos con `ZRANGEBYSCORE`, se elimina la regla UFW y la IP pasa al
  historial con `unban_reason="timeout"`.
- **Desbaneo manual (US-07):** `app/unban_worker.py` consume
  `security:events:unban` (grupo `ufw_workers`), ejecuta el desbloqueo,
  limpia `bans:expirations` y confirma con `XACK`; los fallos de UFW se
  reintentan con `XAUTOCLAIM`.
- **Pruebas:** 79 tests de las Issues #7-#8 con `fakeredis` y un ejecutor UFW
  falso. Evidencia en `docs/evidencias/issue-08-ufw.md`.

### 2.10 Frontend B: visor de logs y estado de IPs — Issue #9

- **Nuevo frontend Vue 3** en `frontend-ops/`, servido bajo `/logs/` y con
  rutas `/logs/` (logs) y `/logs/bans` (IPs e historial).
- **US-03 / FRONT-04:** tabla con fecha/hora, IP, usuario, resultado, tipo y
  puerto; filas verdes para éxitos y rojas para fallos; filtros por resultado,
  IP y usuario; actualización automática cada 5 s.
- **US-06:** pestañas “Baneadas en el momento” e “Historial de baneadas
  anteriormente”, con vencimiento, tiempo restante, duración y motivo.
- **US-07 / FRONT-05:** botón **Desbanear** con confirmación; llama a
  `DELETE /telemetry/bans/<ip>` y el worker de la Issue #8 elimina UFW y el
  timeout.
- **Backend de telemetría:** `app/telemetry.py` persiste eventos en
  `ssh:events`; `app/api.py` expone `/telemetry/logs`, `/telemetry/bans`,
  `/telemetry/history` y `/telemetry/bans/<ip>`; `app/auth.py` valida el JWT
  del Servicio 1 y `session_version`.
- **Integración same-origin:** el `vite.config.js` del Frontend A redirige
  `/logs` a `3001` y `/telemetry` a `5000`, compartiendo `sessionStorage`.
- **Pruebas:** 93 tests en el Servicio 2; `frontend-ops` pasa `npm run lint`
  y `npm run build`. Capturas en `docs/evidencias/issue-09-frontend-b.md`.

---

## 3. Lo pendiente (detalle)

### Issue #3 — Privilegios de Docker y ruta de logs SSH

- Definir si el Servicio 2 corre en el host o en un contenedor.
- Si es contenedor: manejo de `CAP_NET_ADMIN`, `network_mode: host` y acceso al socket/`ufw`.
- Ruta exacta de logs SSH (`/var/log/auth.log`, `/var/log/secure` o `journalctl`).

### Issue #7 — IPs baneadas, historial y desbaneo (Servicio 1)

- La API (`GET/POST /banned-ips/`, `DELETE /banned-ips/{ip}`, historial) ya
  está en `main` (merge `df10bbf`).
- La consola operativa del Frontend B ya cubre la clasificación “Baneadas en
  el momento” / “Historial” y el desbaneo manual (Issue #9).
- Queda pendiente, si se desea, una vista integrada equivalente dentro del
  dashboard React del Frontend A.

### Issue #8 — UFW, desbaneo y visor de logs

- ✅ Bloqueo/desbloqueo con **UFW** a partir de la decisión `ban_required` del
  motor y de la orden manual.
- ✅ Broker de desbaneo `security:events:unban` consumido por el Servicio 2
  (`app/unban_worker.py`).
- ✅ Expiración automática con `bans:expirations` y worker periódico.
- ✅ Visor de logs y control de desbaneo en el Frontend B (Issue #9).
- La ejecución real de UFW requiere root o `sudo` sin contraseña; en
  desarrollo se puede usar `UFW_DRY_RUN=true`.

### Otros pendientes menores

- **Frontend A:** vista integrada de IPs baneadas/historial (la consola
  operativa de la Issue #9 ya lo cubre del lado Vue).
- **Despliegue:** proxy inverso Nginx para publicar ambos frontends bajo el
  mismo origen (`/` para React y `/logs/` para Vue) según el ADR 001.

> Nota: el TTL estricto de tokens (US-10) **ya está implementado** con `SETEX` en la Issue #5.

---

## 4. División de tareas (roadmap)

### Desarrollador 1: Infraestructura, API Web y Gestión de Configuración

| ID | Tarea | Estado | Dependencias |
|----|-------|--------|--------------|
| **INFRA-01** | Setup de Redis en Docker | ✅ Completada | Issue #4 |
| **BACK1-01** | Autenticación de Administrador | ✅ Completada | Issue #4 |
| **BACK1-02** | API de Configuración de Baneos | ✅ Completada | Issue #5 |
| **BACK1-03** | API de Historial y Monitoreo de IPs | 🚧 API completada; vista pendiente | Issue #5 |
| **FRONT-01** | Pantalla de Login (y setup/recuperación) | ✅ Completada | BACK1-01 |
| **FRONT-02** | Formulario de Parámetros de Baneo | ✅ Completada | BACK1-02 |
| **FRONT-03** | Vista de Historial y Estado de IPs | ⏳ Pendiente | BACK1-03 |

### Desarrollador 2: Motor de Seguridad, Parser SSH e Integración UFW

| ID | Tarea | Estado | Dependencias |
|----|-------|--------|--------------|
| **BACK2-01** | Lector y Parser de Logs SSH | ✅ Completada | Issue #3 (ruta configurable) |
| **BACK2-02** | Motor de Reglas y Evaluación | ✅ Completada | Issue #3, #5, #6 |
| **BACK2-03** | Módulo de Bloqueo Automático (UFW) | ✅ Completada | Issue #3 |
| **BACK2-04** | Módulo de Desbaneo Manual (UFW) | ✅ Completada | Issue #2, #7 |
| **FRONT-04** | Visor de Logs SSH Formateado | ✅ Completada | BACK2-01 |
| **FRONT-05** | Control de Desbaneo Manual | ✅ Completada | BACK2-04 |

---

## 5. Hitos de Coordinación Conjunta (Sync Points)

1. **Definición de Esquema en Redis** — ✅ Resuelto: `docs/REDIS_SCHEMA.md` cubre credenciales, configuración, whitelist, contadores, baneos, historial y streams.
2. **Definición de Contrato de API** — ✅ Resuelto: `docs/contrato-desbaneo.yaml` (stream `security:events:unban`, grupo `ufw_workers`).
3. **Integración Frontend** — ✅ Resuelto: `docs/ADR001-UnificacionMultifrontend.md` (proxy inverso Nginx con enrutamiento por rutas + design tokens compartidos).

---

## 6. Cómo verificar el estado actual

```bash
# 1. Redis arriba y respondiendo
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning PING   # -> PONG

# 2. Backend arriba
curl -s http://localhost:8000/health        # -> {"status":"ok",...,"redis":"up"}
curl -s http://localhost:8000/api/v1/auth/status   # -> {"initialized":true}

# 3. Tests del backend (Redis aparte requerido)
cd backend-service1
TEST_REDIS_URL="redis://127.0.0.1:6399/15" PYTHONPATH=.pylibs python -m pytest -q    # -> 88 passed

# 4. Configuración persistida (tras guardar en el dashboard)
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning \
  HGETALL config:settings
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning \
  SMEMBERS config:whitelist

# 5. Tests del Servicio 2 (no necesitan Redis real)
cd ../backend-service2
PYTHONPATH=../backend-service1/.pylibs python -m pytest -q            # -> 93 passed
PYTHONPATH=../backend-service1/.pylibs python scripts/demo_engine.py  # contador y reset
PYTHONPATH=../backend-service1/.pylibs python scripts/demo_ufw.py     # UFW simulado

# 6. Frontend B (Vue)
cd ../frontend-ops
npm ci && npm run lint && npm run build

# 7. Motor continuo (en otra terminal; sin privilegios UFW usar UFW_DRY_RUN=true)
SSH_LOG_PATH=/tmp/auth.log LOG_READ_FROM_START=true UFW_DRY_RUN=true \
  PYTHONPATH=../backend-service1/.pylibs python -m app

# 8. Evidencia UFW real (host con sudo sin contraseña)
cd ../backend-service2
PYTHONPATH=../backend-service1/.pylibs python scripts/demo_ufw.py --real
```

El hash almacenado debe comenzar por `$argon2id$`:

```bash
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning \
  GET admin:credentials | python3 -c "import sys,json;print(json.load(sys.stdin)['password_hash'])"
```

---

## 7. Estado de la infraestructura local

- Únicamente **Redis está dockerizado**; el backend (uvicorn), el motor del Servicio 2 (`python -m app`), el Flask de telemetría y los dos frontends (Vite) corren en la máquina.
- El puerto **6379 del host debe quedar libre** para el contenedor. Si un Redis del sistema (por ejemplo el de `ntopng`) lo ocupa, el contenedor no podrá publicar el puerto; deténgalo (`sudo systemctl stop redis-server`) o mueva el proyecto a otro puerto.
- `.env` (raíz, ignorado por git) contiene los secretos reales: `REDIS_PASSWORD`, `JWT_SECRET` y, opcionalmente, las credenciales SMTP. El Servicio 2 agrega `SSH_LOG_PATH`, `LOG_READ_FROM_START`, `LOG_POLL_INTERVAL`, `SSH_EVENTS_LIMIT` y las variables `UFW_*` / `UNBAN_*`.
- La rama de la Issue #9 parte de `main` con la Issue #8 mergeada. Antes de abrir el PR, verificar que la rama esté sincronizada con `origin/main`.
- La ejecución real de UFW requiere root o `sudo` sin contraseña. En desarrollo, `UFW_DRY_RUN=true` permite ejecutar el motor completo sin privilegios.

---

## 8. Evaluación de calidad (cátedra)

> Documento **generado automáticamente** por la cátedra de Programación III: [`docs/EVALUACION.md`](../docs/EVALUACION.md). **No editar a mano** (se regenera en cada evaluación). Generado el 2026-10-17 sobre `main`.

**Veredicto:** perfil *exigente* — índice de calidad **7/100** (mínimo exigido: 60), **9/15** criterios cumplidos, **NO aprobado**.

| Criterio | Resultado | Observación |
|---|---|---|
| Duplicación | 9.9% | ✅ |
| SQL / DBG / Any / HTTP / Capas / Vistas | 0 / 0 / 0 / 0 / 3 / 11 | ✅ |
| Secretos hardcodeados | 1 | 🔴 Señalado en `app/core/constants.py`, que solo contiene cadenas de mensajes: es un **falso positivo** del detector por regex |
| Tests | 4 archivos (mínimo 5) | 🟡 Tras la Issue #6 se sumó `tests/test_config_api.py`; el informe se regenera sobre `main` |
| Componente grande | 2 (máximo 1) | 🔴 `components/ui.jsx` y `pages/ResetPasswordPage.jsx` |
| Baja cohesión | 2 | 🔴 `core/config.py` y `schemas/auth.py` |
| Complejidad | 25 bloques (máximo 5 por cada 1000 LOC) | 🔴 |

**Acciones derivadas para las próximas issues:**

- **No engordar `components/ui.jsx`**: los formularios de la Issue #6 se implementaron en `components/config/`, fuera del archivo compartido.
- **Mantener la cobertura de pruebas**: el criterio pide 5 archivos de test y 15 de aceptación; la Issue #6 sumó `test_config_api.py` y 37 casos de configuración.
- **Revisar la complejidad y la cohesión** de los archivos nuevos antes de abrir el PR (el detector marca `config.py` y `schemas/auth.py`).
- **Autoría:** `SantiMulet` concentra el 100% del código; `manu_abrego_1913` aporta 5 commits solo de documentación. La cátedra lo señala como señal de que la integración en equipo no ocurrió.
