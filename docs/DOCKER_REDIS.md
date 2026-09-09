# Issue #4: Setup Inicial de Infraestructura y Base de Datos

## Resumen

Resolución completa del setup inicial de infraestructura con Redis como almacenamiento centralizado en memoria ultrarrápida para el sistema Bannedbyabrejeet.

---

## 1. Objetivo del Proyecto

Desplegar el sistema de almacenamiento en memoria ultrarrápida que sirva como núcleo de persistencia para credenciales, tiempos de expiración y estado temporal del firewall, preparando el terreno para los microservicios.

## 2. Descripción de la Tarea

Configurar y levantar el contenedor Docker con Redis para servir como almacenamiento centralizado de todo el sistema.

## 3. Problema que Resuelve

El sistema requiere un motor de base de datos en memoria que proporcione:
- **Velocidad**: Respuestas en milisegundos para verificaciones de IPs y baneos
- **Persistencia híbrida**: Combinación de AOF (Append Only File) y RDB (Remote Database) para recuperación tras reinicios
- **Comunicación entre servicios**: Broker de eventos via Redis Streams para sincronización entre Servicio 1 (FastAPI) y Servicio 2 (Flask)
- **Gestión de estado temporal**: Control de intentos fallidos con ventanas deslizantes y expiración automática

---

## 4. Alcance

### Incluido ✓
- Archivo `docker-compose.yml` con servicio Redis configurado
- Configuración de persistencia híbrida (AOF + RDB)
- Esquema de datos acordado para comunicación entre servicios
- Healthcheck nativo para monitoreo de salud
- Límites de recursos y seguridad con contraseña
- Script de verificación automatizada
- Documentación de esquema de datos (`REDIS_SCHEMA.md`)

### Exclusión ✓
- No se realizó inyección de datos de prueba persistentes
- El script de verificación solo escribe datos temporales que elimina al finalizar

---

## 5. Criterios de Aceptación

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Motor BBDD (Redis) Dockerizado | ✅ Cumplido | Imagen `redis:7.2-alpine` en `docker-compose.yml` |
| 2 | Almacenamiento centralizado de credenciales | ✅ Cumplido | Esquema `user:*` definido en `REDIS_SCHEMA.md` |
| 3 | Almacenamiento de parámetros | ✅ Cumplido | Esquema `config:settings` definido en `REDIS_SCHEMA.md` |
| 4 | Registros de IPs | ✅ Cumplido | Esquemas `ips:banned`, `ips:history`, `failed:<IP>` definidos |
| 5 | Esquema Redis acordado | ✅ Cumplido | Documento `docs/REDIS_SCHEMA.md` completo |
| 6 | docker-compose.yml funcional | ✅ Cumplido | Contenedor levanta y responde correctamente |
| 7 | Persistencia verificada | ✅ Cumplido | Script `verify_redis.sh` comprueba AOF+RDB |

---

## 6. Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: internal_net              │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Nginx      │    │  Service 1   │    │    Redis     │  │
│  │  (Proxy)     │◄──►│  (FastAPI)   │◄──►│  (Memory DB) │  │
│  │  :80, :443   │    │              │    │  :6379       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                       ▲     │
│  ┌────────────────────────────────────────────────┐    │     │
│  │         Service 2 (Flask - Engine)             │────┘     │
│  │   network_mode: host (NET_ADMIN)               │          │
│  └────────────────────────────────────────────────┘          │
│                                                             │
│  Volumen persistente: redis_data (/data)                     │
│    ├── dump.rdb        (RDB snapshots)                       │
│    └── appendonly.aof  (AOF command log)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Estructura de Archivos

```
BanSystem/
├── docker-compose.yml          # Orquestación de servicios + Redis
├── .env.example                # Variables de entorno
├── redis/
│   └── redis.conf              # Configuración production-ready de Redis
├── scripts/
│   └── verify_redis.sh         # Verificación automatizada
└── docs/
    ├── REDIS_SCHEMA.md          # Esquema detallado de datos
    └── DOCKER_REDIS.md          # Este archivo
```

---

## 8. docker-compose.yml — Servicio Redis

### Configuración Principal

```yaml
redis:
  image: redis:7.2-alpine              # Imagen oficial ligera
  container_name: bannedbyabrejeet_redis
  restart: unless-stopped              # Reinicio automático ante fallos
```

### Puertos y Redes

```yaml
ports:
  - "127.0.0.1:6379:6379"            # Solo accesible desde localhost del host
networks:
  - internal_net                      # Red interna para comunicación entre servicios
```

### Comandos y Volúmenes

```yaml
command: >
  redis-server /usr/local/etc/redis/redis.conf
  --requirepass ${REDIS_PASSWORD:-}
volumes:
  - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro   # Configuración mounteada
  - redis_data:/data                                           # Volumen persistente nombrado
```

### Healthcheck

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-}", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 5s
```

### Límites de Recursos

```yaml
deploy:
  resources:
    limits:
      memory: 512M                  # Máximo 512MB para el contenedor
```

### Dependencias

```yaml
depends_on:
  redis:
    condition: service_healthy      # Service 1 espera healthcheck OK
```

---

## 9. redis.conf — Configuración de Persistencia

### Memoria

| Directiva | Valor | Descripción |
|-----------|-------|-------------|
| `maxmemory` | 256mb | Límite máximo de uso de memoria |
| `maxmemory-policy` | noeviction | No elimina claves existentes cuando se alcanza el límite |

### Red

| Directiva | Valor | Descripción |
|-----------|-------|-------------|
| `bind` | 0.0.0.0 | Escucha en todas las interfaces del contenedor |
| `port` | 6379 | Puerto estándar de Redis |
| `timeout` | 300 | Cierre de conexiones idle después de 5 minutos |
| `tcp-keepalive` | 60 | Detección de conexiones muertas cada 60 segundos |

### Logs

| Directiva | Valor | Descripción |
|-----------|-------|-------------|
| `loglevel` | notice | Nivel de detalle: debug, verbose, notice, warning |
| `logfile` | "" | Logs a stdout (comportamiento Docker) |

### Snapshots RDB (Persistencia Puntual)

| Directiva | Valor | Descripción |
|-----------|-------|-------------|
| `save 900 1` | Sí | Snapshot si ≥1 cambio en 900 segundos |
| `save 300 10` | Sí | Snapshot si ≥10 cambios en 300 segundos |
| `save 60 10000` | Sí | Snapshot si ≥10000 cambios en 60 segundos |
| `stop-writes-on-bgsave-error` | yes | Detiene escrituras si snapshot falla |
| `rdbcompression` | yes | Compresión LZF para RDB |
| `rdbchecksum` | yes | Suma de verificación para integridad |
| `dbfilename` | dump.rdb | Nombre del archivo RDB |
| `dir` | /data | Directorio de trabajo (volumen persistente) |

### Append Only File — AOF (Persistencia de Comandos)

| Directiva | Valor | Descripción |
|-----------|-------|-------------|
| `appendonly` | yes | AOF activado |
| `appendfilename` | appendonly.aof | Nombre del archivo AOF |
| `appendfsync` | everysec | Sincronización cada segundo (equilibrio rendimiento/pérdida) |
| `auto-aof-rewrite-percentage` | 100 | Rewriting cuando AOF crece 100% |
| `auto-aof-rewrite-min-size` | 64mb | Tamaño mínimo para triggering de rewrite |
| `aof-load-truncated` | yes | Carga AOF parcial si está truncada tras crash |
| `aof-use-rdb-preamble` | yes | Formato mixto: RDB inicial + comandos incrementales |

---

## 10. Esquema de Datos

Consultar `docs/REDIS_SCHEMA.md` para el esquema completo y detallado.

### Resumen de Claves

| Tipo de Clave | Estructura | Uso Principal | Servicios |
|---------------|------------|---------------|-----------|
| Credenciales | `user:*` | Hash — Credenciales admin | Servicio 1 |
| Parámetros | `config:*` | Hash/Set — Config firewall | Servicio 1 + 2 |
| Whitelist | `config:whitelist` | Set — IPs permitidas | Servicio 1 + 2 |
| Intentos fallidos | `failed:<IP>` | Sorted Set — Sliding window | Servicio 2 |
| IPs baneadas | `ips:banned` | Hash — Baneos activos | Servicio 1 + 2 |
| Historial | `ips:history` | List — Auditoría | Servicio 1 |
| Broker eventos | `security:events:*` | Stream — Desbaneo | Servicio 1 → 2 |

### TTLs y Políticas

| Clave | Tipo | TTL | Propietario |
|-------|------|-----|-------------|
| `user:admin` | Hash | Ninguno (persistente) | Servicio 1 |
| `config:settings` | Hash | Ninguno (persistente) | Servicio 1 |
| `config:whitelist` | Set | Ninguno (persistente) | Servicio 1 + 2 |
| `failed:<IP>` | ZSET | `findtime` segundos | Servicio 2 |
| `ips:banned` | Hash | `bantime × 60` segundos | Servicio 1 + 2 |
| `ips:history` | List | Sin límite (LTRIM 1000) | Servicio 1 |
| `security:events:unban` | Stream | MaxLen ~10000 | Servicio 1 → 2 |

---

## 11. Seguridad

### Autenticación

La contraseña se inyecta vía variable de entorno:

```bash
# En .env
REDIS_PASSWORD=tu_contraseña_segura_aqui
```

```yaml
# En docker-compose.yml
command: >
  redis-server /usr/local/etc/redis/redis.conf
  --requirepass ${REDIS_PASSWORD:-}
```

### Exposición de Puertos

El puerto 6379 solo es accesible desde `127.0.0.1` del host, no desde redes externas:

```yaml
ports:
  - "127.0.0.1:6379:6379"
```

Los microservicios se conectan por la red interna `internal_net` sin exponer puertos adicionales.

---

## 12. Conexión de Servicios

### Servicio 1 (FastAPI) — Red Interna

```python
import redis

r = redis.Redis(
    host='redis',           # Nombre del servicio en Docker
    port=6379,
    password=os.environ['REDIS_PASSWORD'],
    decode_responses=True
)
```

### Servicio 2 (Flask) — Network Mode Host

```python
import redis

r = redis.Redis(
    host='127.0.0.1',       # Acceso directo via loopback
    port=6379,
    password=os.environ['REDIS_PASSWORD'],
    decode_responses=True
)
```

---

## 13. Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```bash
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `REDIS_PASSWORD` | Contraseña de autenticación Redis | `MiContraseñaSegura123!` |
| `JWT_SECRET` | Secret para tokens JWT | `JwtSecretKeyUltraSeguro` |

---

## 14. Guía de Ejecución

### Levantar Redis

```bash
# Opción 1: Solo Redis
docker compose up -d redis

# Opción 2: Todos los servicios (recomendado)
docker compose up -d
```

### Verificar Estado

```bash
# Lista de contenedores
docker compose ps

# Logs de Redis
docker compose logs -f redis

# Verificación automatizada
./scripts/verify_redis.sh "$REDIS_PASSWORD"
```

### Verificar Conexión Manual

```bash
# Acceder al contenedor
docker exec -it bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD"

# Ping
127.0.0.1:6379> PONG

# Verificar volúmenes persistentes
docker exec bannedbyabrejeet_redis ls -lh /data/

# Ver configuración activa
docker exec -it bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" CONFIG GET appendonly
docker exec -it bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" CONFIG GET save
```

### Prueba de Persistencia

```bash
# 1. Escribir dato
docker exec -it bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" SET test_key "test_value"

# 2. Forzar BGSAVE
docker exec bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" BGSAVE

# 3. Reiniciar contenedor
docker compose restart redis

# 4. Verificar dato persistido
docker exec -it bannedbyabrejeet_redis redis-cli -a "$REDIS_PASSWORD" GET test_key
# Debe retornar: "test_value"
```

---

## 15. Troubleshooting

### Contenedor no inicia

```bash
# Ver logs
docker compose logs redis

# Verificar configuración
docker exec bannedbyabrejeet_redis redis-server --test-memory 1

# Reiniciar forzosamente
docker compose down redis && docker compose up -d redis
```

### Fallo de healthcheck

```bash
# Verificar estado del healthcheck
docker inspect bannedbyabrejeet_redis | grep -A 20 Health

# Esperar inicialización
sleep 10 && docker inspect bannedbyabrejeet_redis | grep -A 20 Health
```

### Error de persistencia

```bash
# Verificar permisos del volumen
docker volume inspect BanSystem_redis_data

# Limpiar y recrear volumen (¡PERDERÁ DATOS!)
docker compose down -v && docker compose up -d redis
```

---

## 16. Dependencias

Ninguna. Este módulo se puede ejecutar en paralelo con los Spikes del proyecto.

---

## 17. Evidencias

### docker-compose.yml funcional

El archivo `docker-compose.yml` incluye el servicio Redis completamente configurado con:
- Healthcheck nativo funcional
- Volumen persistente `redis_data`
- Configuración montada desde `redis/redis.conf`
- Dependencia saludable para Service 1
- Límites de recursos definidos

### Verificación mediante redis-cli

El script `scripts/verify_redis.sh` comprueba:
1. Estado del contenedor (running)
2. Healthcheck (healthy)
3. Persistencia AOF activada (`appendonly=yes`)
4. Configuración RDB (`appendfsync=everysec`, snapshots configurados)
5. Prueba de persistencia post-restart (dato sobrevive reinicio)
6. Memoria y políticas (`noeviction`, 256MB)
7. Broker de streams (`security:events:unban` con consumer group `ufw_workers`)

Resultado de ejecución exitosa:

```
==============================================
 Verificación completada exitosamente.
==============================================
 Resumen:
  • Contenedor:           bannedbyabrejeet_redis (running)
  • Healthcheck:          healthy
  • Persistencia:         AOF + RDB híbrida verificada
  • Memoria:              noeviction (max 268435456 bytes)
  • Stream broker:        security:events:unban (grupo: ufw_workers)
```

---

## 18. Referencias

- [Documentación oficial Redis](https://redis.io/docs/)
- [Esquema de datos completo](./REDIS_SCHEMA.md)
- [Script de verificación](../scripts/verify_redis.sh)
- [Configuración Redis](../redis/redis.conf)
- [Orquestación Docker](../docker-compose.yml)
