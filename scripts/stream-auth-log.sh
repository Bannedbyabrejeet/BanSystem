#!/usr/bin/env bash
# =============================================================================
# Bannedbyabrejeet — Puente de lectura de auth.log
#
# El Servicio 2 necesita leer /var/log/auth.log, pero en Debian/Ubuntu ese
# archivo pertenece a syslog:adm y un usuario normal no puede abrirlo.
#
# Este script usa Docker (el usuario del proyecto suele estar en el grupo
# `docker`) para transmitir el auth.log del host a un archivo legible por el
# usuario, sin modificar propietarios ni permisos del sistema.
#
# Uso:
#   ./scripts/stream-auth-log.sh
#
# Imprime en stdout la ruta del archivo espejo. Luego arranque el motor con:
#   SSH_LOG_PATH=<ruta> LOG_READ_FROM_START=true python -m app
#
# Para detenerlo:
#   docker rm -f bannedbyabrejeet_authlog_bridge
# =============================================================================

set -euo pipefail

CONTAINER="bannedbyabrejeet_authlog_bridge"
OUT_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/bansystem"
OUT_FILE="$OUT_DIR/auth.log"

mkdir -p "$OUT_DIR"

# Se recrea para evitar quedar con una configuración vieja o un contenedor
# detenido de una ejecución anterior.
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

# Se monta el directorio /var/log (no solo el archivo) para que `tail -F`
# siga funcionando después de una rotación de logrotate.
docker run -d \
    --name "$CONTAINER" \
    --restart unless-stopped \
    -v /var/log:/hostlog:ro \
    -v "$OUT_DIR:/out" \
    alpine:latest \
    sh -c 'exec tail -n 0 -F /hostlog/auth.log > /out/auth.log' >/dev/null

# Espera breve a que el contenedor cree el archivo espejo.
for _ in $(seq 1 20); do
    [ -s "$OUT_FILE" ] && break
    sleep 0.2
done

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
    echo "Error: el contenedor '$CONTAINER' no quedó en ejecución." >&2
    docker logs "$CONTAINER" >&2 || true
    exit 1
fi

echo "$OUT_FILE"
