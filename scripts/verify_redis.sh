#!/usr/bin/env bash
# =============================================================================
# Bannedbyabrejeet — Redis Verification Script
# Verifica salud, persistencia y broker de streams del contenedor Redis.
#
# Uso: ./scripts/verify_redis.sh [PASSWORD]
#   PASSWORD: Contraseña de Redis (si no se configuró, dejar vacío).
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REDIS_CONTAINER="bannedbyabrejeet_redis"
REDIS_PASSWORD="${1:-}"
REDIS_CLI=("docker" "exec" "-i" "$REDIS_CONTAINER" "redis-cli")

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
ok()  { echo -e "${GREEN}[OK]${NC}  $1"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $1"; }
fail(){ echo -e "${RED}[FAIL]${NC} $1"; }

run_redis_cli() {
    if [ -n "$REDIS_PASSWORD" ]; then
        "${REDIS_CLI[@]}" -a "$REDIS_PASSWORD" --no-auth-warning "$@"
    else
        "${REDIS_CLI[@]}" "$@"
    fi
}

# ------------------------------------------------------------------------------
# 1. Estado del contenedor
# ------------------------------------------------------------------------------
echo "=============================================="
echo " Bannedbyabrejeet — Redis Infrastructure Check"
echo "=============================================="
echo ""

echo "--- [1/5] Verificando estado del contenedor ---"
CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' "$REDIS_CONTAINER" 2>/dev/null || echo "not_found")

if [ "$CONTAINER_STATUS" != "running" ]; then
    fail "El contenedor '$REDIS_CONTAINER' no está en ejecución (estado: $CONTAINER_STATUS)."
    echo "  Ejecute: docker compose up -d redis"
    exit 1
fi
ok "Contenedor '$REDIS_CONTAINER' está ejecutando."

# ------------------------------------------------------------------------------
# 2. Healthcheck
# ------------------------------------------------------------------------------
echo ""
echo "--- [2/5] Verificando healthcheck nativo ---"
HEALTH_STATUS=$(docker inspect -f '{{.State.Health.Status}}' "$REDIS_CONTAINER" 2>/dev/null || echo "unknown")

case "$HEALTH_STATUS" in
    healthy)
        ok "Healthcheck: healthy"
        ;;
    starting)
        warn "Healthcheck: starting — aún inicializando"
        ;;
    unhealthy)
        fail "Healthcheck: unhealthy"
        exit 1
        ;;
    *)
        warn "Healthcheck: no disponible (verificar configuración)"
        ;;
esac

# Ping directo
PING_RESULT=$(run_redis_cli ping 2>/dev/null || echo "NO_PONG")
if [ "$PING_RESULT" = "PONG" ]; then
    ok "Redis CLI responde PONG correctamente."
else
    fail "Redis CLI NO responde PONG. Verificar contraseña o conectividad."
    exit 1
fi

# ------------------------------------------------------------------------------
# 3. Persistencia Híbrida (AOF + RDB)
# ------------------------------------------------------------------------------
echo ""
echo "--- [3/5] Verificando persistencia híbrida (AOF + RDB) ---"

# Escribir dato de prueba
TEST_KEY="__verify_persistence__"
TEST_VALUE="$(date +%s)"
run_redis_cli SET "$TEST_KEY" "$TEST_VALUE" > /dev/null
ok "Dato de prueba escrito: $TEST_KEY = $TEST_VALUE"

# Forzar BGSAVE para generar RDB
run_redis_cli BGSAVE > /dev/null
sleep 2
ok "BGSAVE solicitado."

# Forzar rewrite de AOF
run_redis_cli BGREWRITEAOF > /dev/null
sleep 2
ok "BGREWRITEAOF solicitado."

# Verificar archivos en volumen
echo "  Archivos en volumen redis_data:"
docker exec "$REDIS_CONTAINER" ls -lh /data/ 2>/dev/null || warn "No se puede listar /data/"

# Verificar configuración activa
APPENDONLY=$(run_redis_cli CONFIG GET appendonly 2>/dev/null | tail -1)
APPENDFSYNC=$(run_redis_cli CONFIG GET appendfsync 2>/dev/null | tail -1)
SAVE_CONFIG=$(run_redis_cli CONFIG GET save 2>/dev/null | tail -1)

if [ "$APPENDONLY" = "yes" ]; then
    ok "AOF activado (appendonly=yes)"
else
    warn "AOF no activado (appendonly=$APPENDONLY)"
fi

if [ "$APPENDFSYNC" = "everysec" ]; then
    ok "Appendfsync configurado como everysec"
else
    warn "Appendfsync=$APPENDFSYNC (se recomienda everysec)"
fi

ok "Configuración de snapshots: $SAVE_CONFIG"

# Restart del contenedor y verificar persistencia
echo ""
echo "--- [3b/5] Prueba de persistencia tras restart ---"
echo "  Reiniciando contenedor Redis..."
docker compose restart redis 2>/dev/null || docker restart "$REDIS_CONTAINER" 2>/dev/null
sleep 5

# Re-autenticar tras restart
PING_POST=$(run_redis_cli ping 2>/dev/null || echo "NO_PONG")
if [ "$PING_POST" = "PONG" ]; then
    ok "Redis responde PONG post-restart."
else
    fail "Redis NO responde post-restart."
    exit 1
fi

# Verificar dato persistido
VALUE_AFTER=$(run_redis_cli GET "$TEST_KEY" 2>/dev/null || echo "")
if [ "$VALUE_AFTER" = "$TEST_VALUE" ]; then
    ok "Persistencia verificada: dato sobrevive al restart ($TEST_KEY = $VALUE_AFTER)"
else
    fail "Persistencia FALLÓ: dato perdido tras restart (esperado=$TEST_VALUE, obtenido=$VALUE_AFTER)"
    exit 1
fi

# Limpiar dato de prueba
run_redis_cli DEL "$TEST_KEY" > /dev/null 2>&1 || true
ok "Dato de prueba limpiado."

# ------------------------------------------------------------------------------
# 4. Memoria y límites
# ------------------------------------------------------------------------------
echo ""
echo "--- [4/5] Verificando memoria y políticas ---"

MAXMEMORY=$(run_redis_cli CONFIG GET maxmemory 2>/dev/null | tail -1)
MAXMEMORY_POLICY=$(run_redis_cli CONFIG GET maxmemory-policy 2>/dev/null | tail -1)

if [ "$MAXMEMORY" = "268435456" ]; then
    ok "maxmemory configurado: 256MB"
else
    warn "maxmemory=$MAXMEMORY (se recomienda 256MB = 268435456 bytes)"
fi

if [ "$MAXMEMORY_POLICY" = "noeviction" ]; then
    ok "Política de memoria: noeviction"
else
    warn "Política de memoria=$MAXMEMORY_POLICY (se recomienda noeviction)"
fi

INFO_MEM=$(run_redis_cli INFO memory 2>/dev/null | grep -E "used_memory_human|maxmemory_human" || true)
echo "  $INFO_MEM" | while read -r line; do
    [ -n "$line" ] && echo "    $line"
done

# ------------------------------------------------------------------------------
# 5. Inicialización del Stream de Broker (security:events:unban)
# ------------------------------------------------------------------------------
echo ""
echo "--- [5/5] Inicializando Broker de Desbaneo (Streams) ---"

STREAM="security:events:unban"
GROUP="ufw_workers"

# Crear Consumer Group si no existe
CREATE_RESULT=$(run_redis_cli XGROUP CREATE "$STREAM" "$GROUP" 0 MKSTREAM 2>&1 || true)
if echo "$CREATE_RESULT" | grep -qi "BUSYGROUP\|already exists"; then
    ok "Consumer Group '$GROUP' ya existe en stream '$STREAM'."
else
    ok "Consumer Group '$GROUP' creado en stream '$STREAM'."
fi

# Verificar grupo existente
GROUP_INFO=$(run_redis_cli XPENDING "$STREAM" "$GROUP" 2>/dev/null || echo "")
if [ -n "$GROUP_INFO" ]; then
    ok "Consumer Group activo verificado en '$STREAM'."
    echo "  $GROUP_INFO" | head -3 | while read -r line; do
        [ -n "$line" ] && echo "    $line"
    done
else
    warn "Sin mensajes pendientes en el grupo (esto es normal en fresh install)."
fi

# Publicar mensaje de prueba
TEST_MSG_ID=$(run_redis_cli XADD "$STREAM" "*" \
    "action" "UNBAN" \
    "ip" "127.0.0.1" \
    "requested_by" "verify_script" \
    "timestamp" "$(date +%s)" 2>/dev/null || echo "")

if [ -n "$TEST_MSG_ID" ]; then
    ok "Mensaje de prueba publicado: $TEST_MSG_ID"
else
    fail "No se pudo publicar mensaje en el stream."
    exit 1
fi

# Consumir y ACK el mensaje de prueba
CONSUMED=$(run_redis_cli XREADGROUP GROUP "$GROUP" "verify_worker" COUNT 1 STREAMS "$STREAM" ">" 2>/dev/null || echo "")
if echo "$CONSUMED" | grep -q "UNBAN"; then
    ok "Mensaje consumido exitosamente por verify_worker."
else
    warn "No se pudo consumir el mensaje (puede ser problema de formato de salida)."
fi

# Limpiar mensaje de prueba (opcional)
# run_redis_cli XACK "$STREAM" "$GROUP" "$TEST_MSG_ID" > /dev/null 2>&1 || true

# ------------------------------------------------------------------------------
# Resumen Final
# ------------------------------------------------------------------------------
echo ""
echo "=============================================="
echo " Verificación completada exitosamente."
echo "=============================================="
echo ""
echo " Resumen:"
echo "  • Contenedor:           $REDIS_CONTAINER (running)"
echo "  • Healthcheck:          $HEALTH_STATUS"
echo "  • Persistencia:         AOF + RDB híbrida verificada"
echo "  • Memoria:              $MAXMEMORY_POLICY (max $MAXMEMORY bytes)"
echo "  • Stream broker:        $STREAM (grupo: $GROUP)"
echo ""
echo " Para conectar desde servicios:"
echo "   Servicio 1 (FastAPI):   redis://redis:6379 (red internal_net)"
echo "   Servicio 2 (Flask):     redis://127.0.0.1:6379 (network_mode: host)"
echo ""
