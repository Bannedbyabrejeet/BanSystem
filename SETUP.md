# Bannedbyabrejeet — Guía de puesta en marcha

Este documento describe cómo levantar **todos los componentes** del proyecto desde cero:

| Componente | Tecnología | Cómo se ejecuta | Puerto |
|---|---|---|---|
| Redis 7.2 | Docker | `docker compose up -d redis` | `127.0.0.1:6379` |
| Servicio 1 (API FastAPI) | Python local | `python -m uvicorn app.main:app` | `127.0.0.1:8000` |
| Servicio 2 (motor de seguridad) | Python local (`sudo`) | `python -m app` | — (proceso continuo) |
| Servicio 2 (telemetría Flask) | Python local | `flask --app app.main run` | `127.0.0.1:5000` |
| Frontend A (React) | Node/Vite local | `npm run dev` | `127.0.0.1:3000` |
| Frontend B (Vue) | Node/Vite local | `npm run dev` | `127.0.0.1:3001` (vía `:3000/logs/`) |

Solo Redis está dockerizado. El backend y los frontends corren directamente en la máquina.

---

## 0. Requisitos previos

- **Docker** con Compose (para Redis).
- **Python 3.12** y `pip`.
- **Node.js 18.18+** con `npm`.
- Acceso a **sudo/root** (necesario para que el Servicio 2 lea `/var/log/auth.log` y ejecute `ufw`).

Verificá las versiones:

```bash
python3 --version
node --version
npm --version
docker compose version
```

---

## 1. Clonar / verificar el repositorio

```bash
cd /home/santimulet/BanSystem
git status
git branch --show-current   # debe mostrar 11-issue-9-visor-formateado-de-logs-ssh-y-estado-de-ips-frontend-b
```

---

## 2. Configuración de entorno (`.env`)

El repositorio incluye `.env.example`. Copialo y ajustalo si es necesario:

```bash
cp .env.example .env
```

El `.env` ya incluido en el proyecto tiene los valores usados en este entorno:

```env
REDIS_PASSWORD=mipasswordsegura
JWT_SECRET=entorno-local-cambiar-este-secreto-jwt-64-caracteres
FRONTEND_BASE_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
...
SSH_LOG_PATH=/var/log/auth.log
LOG_READ_FROM_START=false
UFW_DRY_RUN=false
UFW_BINARY=/usr/sbin/ufw
UFW_USE_SUDO=false
```

> **Importante:** `UFW_DRY_RUN=false` hace que el Servicio 2 ejecute reglas reales de UFW. Si querés solo simular (sin tocar el firewall), dejalo en `true`.

---

## 3. Levantar Redis (lo único dockerizado)

```bash
docker compose up -d redis
```

Verificá que responde:

```bash
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning PING
# Debe devolver: PONG
```

Redis queda expuesto solo en loopback (`127.0.0.1:6379`), que es el valor por defecto que usan los backends.

---

## 4. Levantar el Servicio 1 (API FastAPI)

El proyecto ya tiene una carpeta `backend-service1/.pylibs/` con las dependencias instaladas, por lo que no hace falta volver a instalar nada.

```bash
cd backend-service1
PYTHONPATH=.pylibs python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verificá:

```bash
curl -s http://127.0.0.1:8000/health
# Debe devolver: {"status":"ok","redis":"up",...}
```

La API queda disponible en:

- OpenAPI/Swagger: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`
- API base: `http://localhost:8000/api/v1`

> Si querés usar un entorno virtual en lugar de `.pylibs`:
> ```bash
> python -m venv .venv && source .venv/bin/activate
> pip install -r requirements.txt
> python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
> ```

---

## 5. Levantar el Servicio 2 (motor de seguridad + telemetría)

El Servicio 2 necesita **root** porque:

1. Lee `/var/log/auth.log` (pertenece a `syslog:adm`).
2. Ejecuta `ufw` para bloquear IPs.

Desde la raíz del repositorio, corré el motor con `sudo`:

```bash
cd backend-service2
echo 'TU_CONTRASEÑA_ROOT' | sudo -S PYTHONPATH=../backend-service1/.pylibs python3 -m app
```

En otra terminal, levantá la API de telemetría (Flask):

```bash
cd backend-service2
PYTHONPATH=../backend-service1/.pylibs python3 -m flask --app app.main run --host 127.0.0.1 --port 5000
```

Verificá ambos:

```bash
curl -s http://127.0.0.1:5000/health
# Debe devolver: {"status":"ok","redis":"up","ufw":{"dry_run":false,...}}
```

> Si no querés modificar el firewall real, poné `UFW_DRY_RUN=true` en `.env` y relanzá el motor. Los comandos de UFW se registrarán en los logs pero no se ejecutarán.

### Alternativa: leer auth.log sin root (puente Docker)

Si no querés correr el motor como root, usá el script incluido que transmite `/var/log/auth.log` a un archivo legible por tu usuario mediante Docker:

```bash
./scripts/stream-auth-log.sh
# Imprime la ruta del espejo, ej.:
# /home/<usuario>/.local/state/bansystem/auth.log
```

Luego arrancá el motor apuntando a ese archivo (sin sudo para leer el archivo, pero todavía necesitás sudo/root para `ufw` si `UFW_DRY_RUN=false`):

```bash
cd backend-service2
SSH_LOG_PATH="$HOME/.local/state/bansystem/auth.log" \
  LOG_READ_FROM_START=false \
  PYTHONPATH=../backend-service1/.pylibs python3 -m app
```

Para detener el puente:

```bash
docker rm -f bannedbyabrejeet_authlog_bridge
```

---

## 6. Levantar los frontends

### Frontend A (React — administración)

```bash
cd frontend-admin
cp -n .env.example .env
npm ci
npm run dev
```

Queda disponible en `http://localhost:3000`.

### Frontend B (Vue — consola operativa)

```bash
cd frontend-ops
cp -n .env.example .env
npm ci
npm run dev
```

Queda disponible en `http://localhost:3001/logs/`, pero se recomienda abrirlo a través del Frontend A para compartir la sesión:

```
http://localhost:3000/logs/
```

El `vite.config.js` del Frontend A redirige `/logs` al puerto 3001 y `/telemetry` al puerto 5000, de modo que ambos frontends viven bajo el mismo origen y comparten el token de `sessionStorage`.

---

## 7. Resumen de URLs una vez todo levantado

| Servicio | URL |
|---|---|
| Servicio 1 (FastAPI) | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| Servicio 1 health | `http://localhost:8000/health` |
| Servicio 2 telemetría health | `http://localhost:5000/health` |
| Frontend A (admin) | `http://localhost:3000` |
| Frontend B (consola operativa) | `http://localhost:3000/logs/` |
| Frontend B directo | `http://localhost:3001/logs/` |

---

## 8. Primer uso del sistema

1. Abrí `http://localhost:3000`.
2. Si no hay cuenta de administrador, serás redirigido a `/setup` para crear una (usuario, email y contraseña).
3. Iniciá sesión en `/login`.
4. Desde el Dashboard podés configurar:
   - Parámetros de baneo (`maxretry`, `bantime`, `findtime`).
   - Lista blanca de IPs.
5. Abrí `http://localhost:3000/logs/` para ver la consola operativa:
   - Visor de logs SSH (resultados éxito/fallo, filtros, paginación).
   - IPs baneadas en el momento e historial.
   - Botón **Desbanear** para quitar una sanción manualmente.
   - Botón **Limpiar logs** para vaciar los eventos almacenados (con confirmación).

---

## 9. Probar el baneo automático (fuerza bruta)

El motor detecta automáticamente IPs que superan `maxretry` intentos fallidos dentro de `findtime` y les aplica una regla `deny` en UFW.

Para probar con una IP distinta a `127.0.0.1` (que está en whitelist y nunca se banea), inyectá fallos en el auth log:

```bash
# Ejecutá como root para poder escribir en /var/log/auth.log
echo 'TU_CONTRASEÑA_ROOT' | sudo -S sh -c '
echo "2026-11-11T12:00:01.000000-03:00 host sshd[1001]: Failed password for root from 10.0.0.99 port 60001 ssh2" >> /var/log/auth.log
echo "2026-11-11T12:00:02.000000-03:00 host sshd[1002]: Failed password for root from 10.0.0.99 port 60002 ssh2" >> /var/log/auth.log
echo "2026-11-11T12:00:03.000000-03:00 host sshd[1003]: Failed password for root from 10.0.0.99 port 60003 ssh2" >> /var/log/auth.log
'
```

En pocos segundos deberías ver en los logs del motor:

```
FALLO SSH ip=10.0.0.99 usuario=root tipo=failed_password -> 3/3 intentos en 60s
UMBRAL ALCANZADO 3/3 en 60s; aplicando bloqueo UFW
IP 10.0.0.99 bloqueada en UFW hasta ... (5 min, motivo=SSH brute force)
```

Y en UFW:

```bash
sudo ufw status numbered
# [ 1] 22 DENY IN     10.0.0.99
```

El baneo expira automáticamente después de `bantime` minutos (por defecto 5).

---

## 10. Detener todo

```bash
# Servicios 1 y 2
pkill -f "uvicorn app.main"
pkill -f "python3 -m app"
pkill -f "flask --app app.main"

# Frontends
pkill -f vite

# Redis (opcional)
docker compose down

# Puente de auth.log (si lo usás)
docker rm -f bannedbyabrejeet_authlog_bridge
```

---

## 11. Solución de problemas comunes

| Problema | Causa probable | Solución |
|---|---|---|
| `redis-cli: connection refused` | Redis no está corriendo | `docker compose up -d redis` |
| Servicio 1 responde `503` en auth | Redis no accesible | Verificá que Redis esté en `:6379` |
| Servicio 2 no lee logs | Permisos de `/var/log/auth.log` | Corré el motor con `sudo` o usá `scripts/stream-auth-log.sh` |
| UFW no bloquea ninguna IP | `UFW_DRY_RUN=true` | Poné `false` en `.env` y relanzá el motor como root |
| Frontend B pide login otra vez | Token no compartido | Abrí `/logs/` vía `http://localhost:3000/logs/` (mismo origen) |
| `npm ci` falla | Falta `package-lock.json` | Está incluido en ambos frontends |

---

## 12. Estructura de carpetas relevante

```text
BanSystem/
├── docker-compose.yml          # Solo Redis
├── .env                        # Configuración de entorno
├── SETUP.md                    # Esta guía
├── scripts/
│   └── stream-auth-log.sh      # Puente de auth.log sin root
├── backend-service1/
│   ├── .pylibs/                # Dependencias Python (ya instaladas)
│   └── app/                    # Servicio 1 (FastAPI)
├── backend-service2/
│   └── app/                    # Servicio 2 (motor + telemetría)
├── frontend-admin/             # Frontend A (React, :3000)
└── frontend-ops/               # Frontend B (Vue, :3001)
```

El proyecto está listo para usar una vez completados los pasos 1 a 6.