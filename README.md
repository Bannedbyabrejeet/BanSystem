<!-- calidad:inicio -->
![Calidad](https://img.shields.io/badge/Calidad-7%2F100-red) ![Cumple](https://img.shields.io/badge/Cumple-9%2F15-yellow) ![Aprobado](https://img.shields.io/badge/Aprobado-NO-red)

**Calidad de servicios (heurístico):** índice **7/100** · cumple **9/15** · aprobado **NO** · capas **3**
`SEC 1 · SQL 0 · DBG 0 · duplicación 9.9% · vistas 11 · tests 4`
<!-- calidad:fin -->

# BannedbyAbrejeet — Issue #5: autenticación de administrador

Implementación de Backend A (FastAPI + Redis) y Frontend A (React + React Router v6) para el setup único, login, sesión JWT y recuperación de contraseña. Esta entrega no incluye configuración UFW ni Servicio 2 (Flask).

## Arquitectura de autenticación

- `admin:credentials`: string JSON persistente con `admin_id`, `username`, `password_hash` bcrypt, `email`, timestamps y `session_version`. No tiene TTL.
- `admin:initialized`: marcador permanente sin TTL. El setup usa un script Lua atómico que comprueba esta clave y `admin:credentials` y escribe ambas en una sola operación; dos peticiones simultáneas no pueden crear dos administradores.
- `admin:reset_tokens`: set sin TTL que indexa los tokens emitidos como `<admin_id>|<token>`. Permite revocar los enlaces anteriores al pedir uno nuevo, de modo que solo existe un enlace vigente por administrador.
- `reset_token:<token>`: string JSON temporal creado con `SETEX` y TTL de `900` segundos. El token del enlace es aleatorio, opaco y tiene 256 bits de entropía.
- JWT de acceso: firmado con HMAC SHA-256, con `iss`, `aud`, `sub`, `jti`, `iat`, `nbf`, `exp`, rol y versión de sesión. Tras un reset, la versión cambia y los JWT anteriores dejan de ser válidos.

Las contraseñas nunca se guardan en claro. Bcrypt usa 12 rounds por defecto y el backend rechaza contraseñas de más de 72 bytes para evitar truncamiento silencioso.

El detalle completo del esquema Redis está en [`docs/REDIS_SCHEMA.md`](docs/REDIS_SCHEMA.md).

## Estructura del proyecto

```text
.
├── backend-service1/          # Backend A — FastAPI + Redis
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py            # Inyección de dependencias (settings, servicio, admin actual)
│   │   │   └── v1/
│   │   │       ├── router.py       # Incluye el router de auth bajo /api/v1
│   │   │       └── endpoints/auth.py
│   │   ├── core/
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   ├── constants.py       # Mensajes contractuales
│   │   │   ├── keys.py            # Nombres de claves Redis
│   │   │   ├── logging.py
│   │   │   └── security.py        # bcrypt, JWT, tokens opacos, política de contraseñas
│   │   ├── db/redis.py            # Cliente Redis con espera de arranque y ping
│   │   ├── schemas/auth.py        # Modelos Pydantic de entrada/salida
│   │   ├── services/
│   │   │   ├── auth_service.py    # Lógica central (Lua atómico para setup y reset)
│   │   │   └── mail_service.py    # Envío SMTP o log en modo desarrollo
│   │   └── main.py                # App, lifespan, CORS, handlers de error
│   ├── tests/                     # Pytest (48 tests)
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend-admin/            # Frontend A — React 18 + Vite
│   └── src/
│       ├── api/client.js          # Axios + ApiError + almacenamiento del token
│       ├── components/ui.jsx      # Componentes compartidos
│       ├── constants/messages.js  # Mensajes idénticos a app/core/constants.py
│       ├── context/               # AuthContext.js + AuthProvider.jsx
│       ├── pages/                 # Setup, Login, ForgotPassword, ResetPassword, Dashboard
│       ├── routes/                # ProtectedRoute, PublicOnlyRoute
│       ├── styles/global.css
│       └── utils/                 # validation.js, formatRemaining.js
├── docs/REDIS_SCHEMA.md        # Esquema completo de claves Redis
├── docker-compose.yml          # Únicamente Redis
└── .env.example
```

## Arquitectura de ejecución

**Solo la base de datos está dockerizada.** El backend y el frontend corren en la máquina:

| Componente | Cómo se ejecuta | Puerto |
|---|---|---|
| Redis 7.2 | `docker compose up -d redis` | `127.0.0.1:6379` |
| Servicio 1 (FastAPI) | `python -m uvicorn` local | `127.0.0.1:8000` |
| Frontend A (React) | `npm run dev` local | `127.0.0.1:3000` |

Redis queda en un contenedor porque necesita un servidor real con persistencia en disco (AOF + RDB sobre volumen nombrado). El backend lo alcanza por `127.0.0.1`, así que la comunicación es por el loopback del host, no por una red de Docker.

## Requisitos

- Docker con Compose, **solo para Redis**.
- Python 3.12 y Node.js 18.18 o superior con npm.

## Configuración

1. Cree la configuración local a partir del ejemplo:

   ```bash
   cp .env.example .env
   ```

2. Genere secretos fuertes. Para JWT, por ejemplo:

   ```bash
   openssl rand -hex 32
   ```

3. Ajuste `FRONTEND_BASE_URL` a la URL pública del frontend y `CORS_ORIGINS` a los orígenes exactos permitidos, separados por comas.

4. Para correo real, configure `MAIL_MODE=smtp`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` y `MAIL_FROM`. Con `MAIL_MODE=log`, el backend registra el enlace completo en el log; este modo es únicamente para desarrollo.

`JWT_SECRET` debe tener al menos 32 bytes. `RESET_TOKEN_TTL` usa 900 segundos por defecto y puede ajustarse, con un mínimo de 60 segundos.

`REDIS_HOST`, `REDIS_PORT` y `REDIS_DB` tienen valores por defecto adequate para ejecución local (`127.0.0.1:6379/0`), así que no hace falta definirlos en `.env` salvo que cambie el puerto.

## Levantar Redis (lo único dockerizado)

```bash
docker compose up -d redis
```

Verifique que responde:

```bash
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning PING
```

## Levantar el Servicio 1 (local, sin Docker)

Con entorno virtual (opción habitual):

```bash
cd backend-service1
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Si `python -m venv` falla** con `No module named ensurepip` (típico en instalaciones de sistema como Debian/Ubuntu, que además bloquean `pip install` con PEP 668), use una carpeta de dependencias dentro del propio proyecto:

```bash
cd backend-service1
python -m pip install --target .pylibs -r requirements.txt
PYTHONPATH=.pylibs python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`.pylibs/` está en `.gitignore`. Esta variante no modifica el Python del sistema, así que es segura en entornos gestionados.

El proceso lee la configuración de `.env` en la raíz del repositorio (`Settings` busca `.env` y `../.env`).

La API queda disponible en:

- OpenAPI/Swagger: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`
- API base: `http://localhost:8000/api/v1`

Si Redis no está levantado, el arranque espera `REDIS_STARTUP_RETRIES` intentos y después termina con error. Los endpoints de autenticación devuelven `503` con el detalle `Servicio de autenticación no disponible` mientras Redis no responda.

## Levantar Frontend A

```bash
cd frontend-admin
cp .env.example .env
npm ci
npm run dev
```

React queda disponible en `http://localhost:3000`. Otros comandos:

| Comando | Descripción |
|---|---|
| `npm run dev` | Servidor de desarrollo con proxy a la API |
| `npm run build` | Bundle de producción en `build/` |
| `npm run preview` | Sirve localmente el bundle ya construido |
| `npm run lint` | ESLint (`--max-warnings 0`): debe terminar en 0 errores y 0 avisos |

El repositorio incluye `package-lock.json`, por lo que `npm ci` instala exactamente las versiones versionadas. Use `npm install` solo si va a modificar dependencias.

### Configuración del frontend

| Variable | Por defecto | Descripción |
|---|---|---|
| `VITE_API_BASE_URL` | vacío | Vacío = mismo origen, el frontend llama a `/api/v1` y el proxy de Vite reenvía al backend. Con URL absoluta (p. ej. `http://localhost:8000/api/v1`) hace peticiones cross-origin y exige `CORS_ORIGINS` en el backend. |
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:8000` | Backend al que apunta el proxy de Vite. Cámbielo si la API corre en otro puerto. |
| `VITE_APP_NAME` | `Bannedbyabrejeet` | Nombre mostrado en la interfaz. |

El JWT se guarda en `sessionStorage`, de modo que se pierde al cerrar la pestaña.

El servidor que aloje `build/` debe usar fallback de History API hacia `index.html` para que funcionen rutas como `/reset-password?token=...` al abrirse o recargarse directamente.

## Endpoints

| Método | Ruta | Resultado |
|---|---|---|
| `GET` | `/api/v1/auth/status` | `{ "initialized": false }` |
| `POST` | `/api/v1/auth/setup` | Crea la cuenta única; después responde `409` |
| `POST` | `/api/v1/auth/login` | JWT; credenciales incorrectas: `401` con `Credenciales inválidas` |
| `POST` | `/api/v1/auth/forgot-password` | Crea un token con `SETEX` y envía el enlace |
| `GET` | `/api/v1/auth/verify-reset-token/{token}` | Indica si Redis todavía conserva el token |
| `POST` | `/api/v1/auth/reset-password` | Consume el token, cambia hash e invalida sesiones previas |
| `GET` | `/api/v1/auth/me` | Valida el JWT y su versión contra Redis |

Cuando Redis no responde, los endpoints de autenticación devuelven `503` con el detalle `Servicio de autenticación no disponible`, en lugar de un `500`.

## Tests del backend

Los tests usan la base de datos que indique `TEST_REDIS_URL`. Si no se define, las pruebas que requieren Redis se omiten y las restantes se ejecutan.

**Los tests necesitan su propio Redis, separado del de desarrollo.** La razón es concreta: hacen `FLUSHDB` al empezar, y `redis/redis.conf` está configurado con `databases 1` (solo existe la db 0, la del administrador real). Apuntarlos a `db 0` borraría la cuenta de administrador.

```bash
# 1. Redis efímero solo para tests (db 15 disponible, datos descartables)
docker run -d --rm --name bba-test-redis -p 6399:6379 \
  redis:7.2-alpine redis-server --save '' --appendonly no

# 2. Dependencias
cd backend-service1
python -m pip install --target .pylibs -r requirements.txt -r requirements-dev.txt

# 3. Tests
TEST_REDIS_URL="redis://127.0.0.1:6399/15" PYTHONPATH=.pylibs python -m pytest -q
```

Sin `TEST_REDIS_URL` se ejecutan 18 tests y se omiten 30, con un mensaje explicativo en la salida.

## Verificación manual del flujo

1. Abra `http://localhost:3000`. Sin cuenta, el frontend redirige a setup.
2. Cree una cuenta con una contraseña de al menos 12 caracteres, una mayúscula, una minúscula y un número.
3. El setup exitoso redirige a login. Repita setup concurrentemente: solo una petición puede crear la cuenta; las restantes reciben `409`.
4. Pruebe el login con datos incorrectos: la API responde `401` y la interfaz muestra exactamente `Credenciales inválidas`.
5. Pruebe el login correcto: la interfaz redirige a `/dashboard` y `/auth/me` valida el JWT.
6. Abra "Olvidé mi contraseña". En `MAIL_MODE=log`, copie el enlace completo del log del proceso de FastAPI (la terminal donde corre `uvicorn`).
7. Verifique que el enlace muestra el formulario, establece una contraseña nueva, consume el token y vuelve a login con `Contraseña actualizada correctamente`.
8. Reutilice el mismo enlace: debe mostrarse `El enlace de recuperación ha caducado o no es válido`.
9. Pida un segundo enlace sin usar el primero: el anterior deja de funcionar de inmediato, porque solo puede haber un enlace vigente por administrador.

## Comprobar `SETEX` y expiración real con `redis-cli`

Defina la contraseña de Redis y obtenga el token del log. La clave contiene el token recibido:

```bash
REDIS_PASSWORD='TU_CONTRASEÑA_DE_REDIS'
TOKEN='PEGAR_AQUI_EL_TOKEN_DEL_ENLACE'
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning \
  TTL "reset_token:$TOKEN"
```

Inmediatamente después del envío, `TTL` debe devolver un entero entre `1` y `900`. Para observar la eliminación nativa:

```bash
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning \
  EXISTS "reset_token:$TOKEN"
```

- `1`: el token sigue vigente.
- `0`: fue consumido o ya no existe.

Espere 900 segundos y ejecute de nuevo `TTL`:

- `-1`: la clave existe pero no tiene TTL; sería una configuración incorrecta para tokens de recuperación.
- `-2`: la clave ya no existe porque Redis aplicó su expiración.

Para una prueba más corta, configure `RESET_TOKEN_TTL=60` en `.env`, reinicie `uvicorn` y solicite un enlace nuevo.

El índice de tokens emitidos se comprueba aparte:

```bash
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning \
  SMEMBERS admin:reset_tokens
```

Debe contener un único miembro con la forma `<admin_id>|<token>`, y `TTL admin:reset_tokens` debe devolver `-1`.

Finalmente, `GET admin:credentials` debe mostrar un JSON cuyo campo `password_hash` comienza por `$2b$`; `TTL admin:credentials` debe ser `-1`, porque las credenciales son permanentes.