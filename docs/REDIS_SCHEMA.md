# Redis Data Schema — Bannedbyabrejeet

## Tabla de Contenidos
1. [Visión General](#visión-general)
2. [Credenciales de Administrador](#1-credenciales-de-administrador)
3. [Parámetros de Configuración del Firewall](#2-parámetros-de-configuración-del-firewall)
4. [Lista Blanca (Whitelist)](#3-lista-blanca-whitelist)
5. [Contador de Intentos Fallidos (Sliding Window)](#4-contador-de-intentos-fallidos-sliding-window)
6. [IPs Baneadas Activas](#5-ips-baneadas-activas)
7. [Historial de IPs](#6-historial-de-ips)
8. [Broker de Desbaneo Manual (Redis Streams)](#7-broker-de-desbaneo-manual-redis-streams)
9. [Resumen de TTLs y Políticas](#resumen-de-ttls-y-políticas)

---

## Visión General

| Tipo de Clave | Estructura | Uso Principal | Servicios |
|---|---|---|---|
| `user:*` | Hash | Credenciales admin | Servicio 1 (FastAPI) |
| `config:*` | Hash / Set | Parámetros y whitelist | Servicio 1 + Servicio 2 |
| `failed:<IP>` | Sorted Set | Contador de intentos fallidos | Servicio 2 (Flask) |
| `ips:banned` | Hash | IPs baneadas activas | Servicio 1 + Servicio 2 |
| `ips:history` | List | Historial de auditoría | Servicio 1 (FastAPI) |
| `security:events:*` | Stream | Broker de eventos (desbaneo) | Servicio 1 → Servicio 2 |

Todos los valores de TTL se expresan en **segundos**. Los timestamps son **UNIX epoch** (enteros).

---

## 1. Credenciales de Administrador

### Clave
```
user:admin
```

### Tipo
**Hash**

### Campos
| Campo | Tipo | Descripción |
|---|---|---|
| `username` | String | Nombre de usuario del administrador |
| `password_hash` | String | Hash bcrypt/argon2 de la contraseña |
| `email` | String | Correo electrónico registrado |
| `created_at` | Integer | Timestamp UNIX de creación |

### Ejemplo `redis-cli`
```bash
# Set
HSET user:admin username "admin" password_hash "$2b$12$LJ3m4ys..." email "admin@bannedbyabrejeet.local" created_at 1725484800

# Get
HGETALL user:admin

# TTL opcional (sesión activa)
TTL user:admin
```

### Equivalente `redis-py` (Python)
```python
import redis

r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)

# Set
r.hset('user:admin', mapping={
    'username': 'admin',
    'password_hash': '$2b$12$LJ3m4ys...',
    'email': 'admin@bannedbyabrejeet.local',
    'created_at': str(1725484800),
})

# Get
creds = r.hgetall('user:admin')
# {'username': 'admin', 'password_hash': '$2b$12$LJ3m4ys...', ...}
```

---

## 2. Parámetros de Configuración del Firewall

### Clave
```
config:settings
```

### Tipo
**Hash**

### Campos
| Campo | Tipo | Descripción |
|---|---|---|
| `maxretry` | Integer | Máximo de intentos fallidos antes del baneo |
| `bantime` | Integer | Duración del baneo en minutos |
| `findtime` | Integer | Ventana temporal (minutos) para acumular intentos |

### Ejemplo `redis-cli`
```bash
# Set
HSET config:settings maxretry 5 bantime 30 findtime 10

# Get
HGETALL config:settings

# Campo individual
HGET config:settings maxretry
```

### Equivalente `redis-py`
```python
# Set
r.hset('config:settings', mapping={
    'maxretry': '5',
    'bantime': '30',
    'findtime': '10',
})

# Get
settings = r.hgetall('config:settings')
# {'maxretry': '5', 'bantime': '30', 'findtime': '10'}

# Obtener un campo como entero
maxretry = int(r.hget('config:settings', 'maxretry'))
```

---

## 3. Lista Blanca (Whitelist)

### Clave
```
config:whitelist
```

### Tipo
**Set**

### Valores
Direcciones IP o rangos CIDR. Por defecto incluye `127.0.0.1` y `::1`.

### Ejemplo `redis-cli`
```bash
# Agregar
SADD config:whitelist "192.168.1.100" "10.0.0.0/8"

# Verificar pertenencia
SISMEMBER config:whitelist "192.168.1.100"  # → (integer) 1

# Listar todos
SMEMBERS config:whitelist

# Remover
SREM config:whitelist "192.168.1.100"

# Cantidad de elementos
SCARD config:whitelist
```

### Equivalente `redis-py`
```python
# Agregar
r.sadd('config:whitelist', '192.168.1.100', '10.0.0.0/8')

# Verificar
is_whitelisted = r.sismember('config:whitelist', '192.168.1.100')  # True

# Listar
whitelist = r.smembers('config:whitelist')
# {'192.168.1.100', '10.0.0.0/8'}

# Remover
r.srem('config:whitelist', '192.168.1.100')
```

---

## 4. Contador de Intentos Fallidos (Sliding Window)

### Clave
```
failed:<IP>
```
Ejemplo: `failed:203.0.113.42`

### Tipo
**Sorted Set (ZSET)**

| Elemento | Valor (Score) | Miembro |
|---|---|---|
| Score | Timestamp UNIX | ID único del evento (UUID o counter) |

### TTL
Se establece igual a `findtime` (en segundos) desde `config:settings`. Se renueva con cada nuevo intento fallido.

### Operaciones
```
ZADD failed:203.0.113.42 <unix_timestamp> <event_id>
ZRANGEBYSCORE failed:203.0.113.42 <now - findtime> <now>
ZCARD failed:203.0.113.42
PEXPIRE failed:203.0.113.42 <findtime * 1000>
ZREMRANGEBYSCORE failed:203.0.113.42 -inf <now - findtime>
```

### Ejemplo `redis-cli`
```bash
# Registrar intento fallido
NOW=$(date +%s)
EVENT_ID="evt_$(uuidgen)"
ZADD "failed:203.0.113.42" "$NOW" "$EVENT_ID"

# Contar intentos en ventana actual (findtime=600s = 10 min)
CURRENT_WINDOW=$(ZRANGEBYSCORE "failed:203.0.113.42" $(( NOW - 600 )) "$NOW")
COUNT=$(echo "$CURRENT_WINDOW" | wc -l)

# Limpiar entradas fuera de ventana
ZREMRANGEBYSCORE "failed:203.0.113.42" "-inf" $(( NOW - 600 ))

# Renovar TTL (findtime = 10 min = 600 seg)
EXPIRE "failed:203.0.113.42" 600
```

### Equivalente `redis-py`
```python
import uuid
import time

ip = '203.0.113.42'
key = f'failed:{ip}'
now = int(time.time())
event_id = f'evt_{uuid.uuid4().hex[:8]}'

# Registrar intento fallido
r.zadd(key, {event_id: now})

# Contar en ventana deslizante (findtime en segundos)
findtime = int(r.hget('config:settings', 'findtime')) or 600
window_start = now - findtime

count_in_window = r.zcount(key, window_start, now)

if count_in_window >= int(r.hget('config:settings', 'maxretry')):
    print(f"[!] IP {ip} superó el umbral de intentos ({count_in_window}/{int(r.hget('config:settings', 'maxretry'))})")

# Renovar TTL
r.expire(key, findtime)

# Limpieza periódica de eventos fuera de ventana
r.zremrangebyscore(key, '-inf', window_start)
```

---

## 5. IPs Baneadas Activas

### Clave
```
ips:banned
```

### Tipo
**Hash**

| Campo (IP) | Valor (JSON string) |
|---|---|
| `<IP>` | `{"banned_at": <unix_ts>, "expires_at": <unix_ts>, "duration_min": <int>, "reason": "<string>"}` |

### Ejemplo `redis-cli`
```bash
# Baneo
JSON.SET ips:banned $.ban0 '{"banned_at":1725484800,"expires_at":1725486600,"duration_min":30,"reason":"SSH brute force"}'

# O usando HSET con valor JSON como string
HSET ips:banned "203.0.113.42" '{"banned_at":1725484800,"expires_at":1725486600,"duration_min":30,"reason":"SSH brute force"}'

# Leer
HGET ips:banned "203.0.113.42"

# Verificar si una IP está baneada
HEXISTS ips:banned "203.0.113.42"

# Listar todas
HGETALL ips:banned

# Remover (desbaneo)
HDEL ips:banned "203.0.113.42"
```

### Equivalente `redis-py`
```python
import json
import time

ip = '203.0.113.42'
bantime_minutes = 30
now = int(time.time())
banned_info = json.dumps({
    'banned_at': now,
    'expires_at': now + (bantime_minutes * 60),
    'duration_min': bantime_minutes,
    'reason': 'SSH brute force',
})

# Registrar baneo
r.hset('ips:banned', ip, banned_info)

# Verificar
is_banned = r.hexists('ips:banned', ip)

# Leer info completa
if is_banned:
    info = json.loads(r.hget('ips:banned', ip))
    print(f"Baneada hasta: {info['expires_at']} ({info['reason']})")

# Desbanear
r.hdel('ips:banned', ip)

# Listar todas las IPs baneadas
for ip_addr, info_json in r.hgetall('ips:banned').items():
    info = json.loads(info_json)
    print(f"{ip_addr}: {info}")
```

---

## 6. Historial de IPs

### Clave
```
ips:history
```

### Tipo
**List (LPUSH / LRANGE)**

### Formato de Entrada
Cada elemento es un **string JSON** con la auditoría completa del evento de baneo.

```json
{
  "ip": "203.0.113.42",
  "action": "banned",
  "banned_at": 1725484800,
  "unbanned_at": 1725486600,
  "duration_min": 30,
  "reason": "SSH brute force",
  "unban_reason": "manual"
}
```

### Ejemplo `redis-cli`
```bash
# Insertar al inicio
LPUSH ips:history '{"ip":"203.0.113.42","action":"banned","banned_at":1725484800,"unbanned_at":1725486600,"duration_min":30,"reason":"SSH brute force","unban_reason":"manual"}'

# Consultar últimas 50
LRANGE ips:history 0 49

# Cantidad total
LLEN ips:history

# Limitar tamaño (mantener últimas N entradas)
LTRIM ips:history 0 999
```

### Equivalente `redis-py`
```python
import json
import time

entry = {
    'ip': '203.0.113.42',
    'action': 'banned',
    'banned_at': 1725484800,
    'unbanned_at': int(time.time()),
    'duration_min': 30,
    'reason': 'SSH brute force',
    'unban_reason': 'manual',
}

# Insertar
r.lpush('ips:history', json.dumps(entry))

# Mantener tope de 1000 entradas
r.ltrim('ips:history', 0, 999)

# Consultar últimas 50
history = r.lrange('ips:history', 0, 49)
for h in history:
    print(json.loads(h))
```

---

## 7. Broker de Desbaneo Manual (Redis Streams)

### Stream
```
security:events:unban
```

### Consumer Group
```
ufw_workers
```

### Payload (campo-value)
| Campo | Tipo | Descripción |
|---|---|---|
| `action` | String | Siempre `"UNBAN"` |
| `ip` | String | Dirección IP a desbloquear |
| `requested_by` | String | Identificador del solicitante (ej: admin username) |
| `timestamp` | String | Timestamp UNIX de la petición |

### Ejemplo `redis-cli`
```bash
# Crear Consumer Group (una sola vez)
XGROUP CREATE security:events:unban ufw_workers 0 MKSTREAM

# Publicar evento (Servicio 1 - FastAPI)
XADD security:events:unban * action UNBAN ip 203.0.113.42 requested_by admin timestamp 1725484800

# Consumir (Servicio 2 - Flask)
XREADGROUP GROUP ufw_workers worker1 COUNT 1 BLOCK 5000 STREAMS security:events:unban >

# Acknowledge después de procesar
XACK security:events:unban ufw_workers <id_del_mensaje>
```

### Equivalente `redis-py`

#### Productor (Servicio 1 — FastAPI)
```python
from redis.asyncio import Redis as AsyncRedis

stream = 'security:events:unban'

async def publish_unban(ip: str, requested_by: str):
    """Publica una solicitud de desbaneo al stream."""
    msg_id = await r.xadd(
        stream,
        {
            'action': 'UNBAN',
            'ip': ip,
            'requested_by': requested_by,
            'timestamp': str(int(time.time())),
        },
        maxlen=10000,          # Limitar tamaño del stream
        approximate=True,     # ~ para mantenimiento eficiente
    )
    return msg_id
    # Retorna: '1725484800000-0'
```

#### Consumidor (Servicio 2 — Flask)
```python
from redis.asyncio import Redis as AsyncRedis

stream = 'security:events:unban'
group = 'ufw_workers'
consumer = 'worker1'

# Crear grupo si no existe (una sola vez al iniciar)
try:
    await r.xgroup_create(stream, group, id='0', mkstream=True)
except redis.exceptions.ResponseError:
    pass  # Ya existe

async def consume_unban_events():
    """Bucle de consumo de eventos de desbaneo."""
    messages = await r.xreadgroup(
        group,
        consumer,
        {stream: '>'},   # '>' = solo mensajes nuevos
        count=1,
        block=5000,       # Esperar hasta 5s si no hay mensajes
    )
    for stream_name, entries in messages:
        for msg_id, fields in entries:
            ip = fields[b'ip'].decode()
            requested_by = fields[b'requested_by'].decode()

            # --- Ejecutar desbaneo en UFW aquí ---
            # run_ufw_unban(ip)

            # Confirmar procesamiento
            await r.xack(stream, group, msg_id)
```

#### Con `aioredis` (alternativa)
```python
import aioredis

r = aioredis.from_url('redis://127.0.0.1:6379', decode_responses=True)

# Productor
await r.xadd('security:events:unban', {
    'action': 'UNBAN',
    'ip': '203.0.113.42',
    'requested_by': 'admin',
    'timestamp': str(int(time.time())),
})

# Consumidor
messages = await r.xreadgroup(
    group='ufw_workers',
    consumer='worker1',
    streams={'security:events:unban': '>'},
    count=1,
    block=5000,
)
```

---

## Resumen de TTLs y Políticas

| Clave | Tipo | TTL | Política | Propietario |
|---|---|---|---|---|
| `user:admin` | Hash | Ninguno (persistente) | Nunca expira | Servicio 1 |
| `config:settings` | Hash | Ninguno | Persistente | Servicio 1 |
| `config:whitelist` | Set | Ninguno | Persistente | Servicio 1 + 2 |
| `failed:<IP>` | ZSET | `findtime` segundos | Auto-expira | Servicio 2 |
| `ips:banned` | Hash | `bantime * 60` segundos | Auto-expira al vencer | Servicio 1 + 2 |
| `ips:history` | List | Sin límite (LTRIM a 1000) | Retención acotada | Servicio 1 |
| `security:events:unban` | Stream | MaxLen ~10000 | Appender-only | Servicio 1 → 2 |
