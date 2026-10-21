# Bannedbyabrejeet: Estado Actual y Tareas Pendientes

> **Última actualización:** 2026-10-21
> **Rama activa:** `8-issue-6-api-de-configuración-de-baneos-y-dashboard` (aún sin pushear)
> **Rama de referencia:** `main` — ya incluye el PR #25 (migración a Argon2id, fix de correo y documentación), merge `dc35f40`
> **Entregado hasta ahora:** Servicio 1 (FastAPI) + Frontend A (React), con autenticación de administrador completa sobre Redis dockerizado.

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
| **#6** | Parámetros de baneo (API + vista) | ⏳ Pendiente | — |
| **#7** | IPs baneadas, historial y desbaneo manual | ⏳ Pendiente | — |
| **#8** | Servicio 2 (parser SSH + UFW) y visor de logs | ⏳ Pendiente | — |
| **#24** | Migración de bcrypt a Argon2id | ✅ Completada | `backend-service1/app/core/security.py` |

**Leyenda:** ✅ Cerrada · 🚧 En curso · ⏳ Pendiente

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
- El Dashboard muestra la sesión activa; las secciones de parámetros, IPs y logs quedan como marcadores de las issues #6, #7 y #8.

### 2.6 Pruebas

- **48 tests** en `backend-service1/tests/` (seguridad + API de autenticación).
- Si no se define `TEST_REDIS_URL`, se ejecutan 18 y se omiten 30 (las que necesitan Redis).
- Requieren un **Redis aparte del de desarrollo** (por ejemplo `redis://127.0.0.1:6399/15`), porque hacen `FLUSHDB`.

---

## 3. Lo pendiente (detalle)

### Issue #3 — Privilegios de Docker y ruta de logs SSH

- Definir si el Servicio 2 corre en el host o en un contenedor.
- Si es contenedor: manejo de `CAP_NET_ADMIN`, `network_mode: host` y acceso al socket/`ufw`.
- Ruta exacta de logs SSH (`/var/log/auth.log`, `/var/log/secure` o `journalctl`).

### Issue #6 — Parámetros de baneo

- Persistir `config:settings` (intentos fallidos, tiempo de baneo y ventana de tolerancia) vía Servicio 1.
- Endpoints `GET`/`PUT` de configuración y vista en el Dashboard.
- Validación de enteros positivos estrictos.
- El contrato de claves ya está cerrado en [`docs/REDIS_SCHEMA.md`](../docs/REDIS_SCHEMA.md) §2 (valores por defecto de `maxretry`, `bantime` y `findtime`) y §3 (`config:whitelist` con `127.0.0.1` y `::1` protegidas e inmutables).

### Issue #7 — IPs baneadas, historial y desbaneo

- Claves `ips:banned`, `ips:history` y `failed:<IP>`.
- Endpoints para listar IPs activas, historial y solicitar desbaneo.
- Vista con clasificación "Baneadas en el momento" / "Historial".

### Issue #8 — Servicio 2 (Flask) y visor de logs

- Parser de logs SSH (intentos fallidos y exitosos).
- Motor de reglas con ventana temporal (`findtime`).
- Bloqueo/desbloqueo con **UFW**.
- Broker de desbaneo `security:events:unban` (contrato en `docs/contrato-desbaneo.yaml`).
- Frontend B (Vue) con el visor de logs formateado y el control de desbaneo manual.

### Otros pendientes menores

- **Lista blanca (US-08):** `config:whitelist`, con `127.0.0.1` protegida e inmutable.
- **Ventana temporal (US-09):** parámetro `findtime` en la evaluación del Servicio 2.
- **Frontend B (Vue):** aún no iniciado.

> Nota: el TTL estricto de tokens (US-10) **ya está implementado** con `SETEX` en la Issue #5.

---

## 4. División de tareas (roadmap)

### Desarrollador 1: Infraestructura, API Web y Gestión de Configuración

| ID | Tarea | Estado | Dependencias |
|----|-------|--------|--------------|
| **INFRA-01** | Setup de Redis en Docker | ✅ Completada | Issue #4 |
| **BACK1-01** | Autenticación de Administrador | ✅ Completada | Issue #4 |
| **BACK1-02** | API de Configuración de Baneos | ⏳ Pendiente | Issue #5 |
| **BACK1-03** | API de Historial y Monitoreo de IPs | ⏳ Pendiente | Issue #5 |
| **FRONT-01** | Pantalla de Login (y setup/recuperación) | ✅ Completada | BACK1-01 |
| **FRONT-02** | Formulario de Parámetros de Baneo | ⏳ Pendiente | BACK1-02 |
| **FRONT-03** | Vista de Historial y Estado de IPs | ⏳ Pendiente | BACK1-03 |

### Desarrollador 2: Motor de Seguridad, Parser SSH e Integración UFW

| ID | Tarea | Estado | Dependencias |
|----|-------|--------|--------------|
| **BACK2-01** | Lector y Parser de Logs SSH | ⏳ Pendiente | Issue #3 |
| **BACK2-02** | Motor de Reglas y Evaluación | ⏳ Pendiente | Issue #3, #5, #6 |
| **BACK2-03** | Módulo de Bloqueo Automático (UFW) | ⏳ Pendiente | Issue #3 |
| **BACK2-04** | Módulo de Desbaneo Manual (UFW) | ⏳ Pendiente | Issue #2, #7 |
| **FRONT-04** | Visor de Logs SSH Formateado | ⏳ Pendiente | BACK2-01 |
| **FRONT-05** | Control de Desbaneo Manual | ⏳ Pendiente | BACK2-04 |

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
TEST_REDIS_URL="redis://127.0.0.1:6399/15" PYTHONPATH=.pylibs python -m pytest -q    # -> 48 passed
```

El hash almacenado debe comenzar por `$argon2id$`:

```bash
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning \
  GET admin:credentials | python3 -c "import sys,json;print(json.load(sys.stdin)['password_hash'])"
```

---

## 7. Estado de la infraestructura local

- Únicamente **Redis está dockerizado**; el backend (uvicorn) y el Frontend A (Vite) corren en la máquina.
- El puerto **6379 del host debe quedar libre** para el contenedor. Si un Redis del sistema (por ejemplo el de `ntopng`) lo ocupa, el contenedor no podrá publicar el puerto; deténgalo (`sudo systemctl stop redis-server`) o mueva el proyecto a otro puerto.
- `.env` (raíz, ignorado por git) contiene los secretos reales: `REDIS_PASSWORD`, `JWT_SECRET` y, opcionalmente, las credenciales SMTP.
- El `main` **local quedó 9 commits atrás** de `origin/main` (que ya incluye el PR #25). Actualizalo antes de abrir el PR de la Issue #6: `git checkout main && git pull`.

---

## 8. Evaluación de calidad (cátedra)

> Documento **generado automáticamente** por la cátedra de Programación III: [`docs/EVALUACION.md`](../docs/EVALUACION.md). **No editar a mano** (se regenera en cada evaluación). Generado el 2026-10-17 sobre `main`.

**Veredicto:** perfil *exigente* — índice de calidad **7/100** (mínimo exigido: 60), **9/15** criterios cumplidos, **NO aprobado**.

| Criterio | Resultado | Observación |
|---|---|---|
| Duplicación | 9.9% | ✅ |
| SQL / DBG / Any / HTTP / Capas / Vistas | 0 / 0 / 0 / 0 / 3 / 11 | ✅ |
| Secretos hardcodeados | 1 | 🔴 Señalado en `app/core/constants.py`, que solo contiene cadenas de mensajes: es un **falso positivo** del detector por regex |
| Tests | 4 archivos (mínimo 5) | 🔴 La Issue #6, con su archivo de pruebas, alcanza el mínimo |
| Componente grande | 2 (máximo 1) | 🔴 `components/ui.jsx` y `pages/ResetPasswordPage.jsx` |
| Baja cohesión | 2 | 🔴 `core/config.py` y `schemas/auth.py` |
| Complejidad | 25 bloques (máximo 5 por cada 1000 LOC) | 🔴 |

**Acciones derivadas para las próximas issues:**

- **No engordar `components/ui.jsx`**: los formularios de la Issue #6 van en componentes nuevos.
- **Mantener la cobertura de pruebas**: el criterio pide 5 archivos de test y 15 de aceptación; la Issue #6 debe sumar ambos.
- **Revisar la complejidad y la cohesión** de los archivos nuevos antes de abrir el PR (el detector marca `config.py` y `schemas/auth.py`).
- **Autoría:** `SantiMulet` concentra el 100% del código; `manu_abrego_1913` aporta 5 commits solo de documentación. La cátedra lo señala como señal de que la integración en equipo no ocurrió.
