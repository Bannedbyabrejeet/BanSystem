"""Mensajes de error y de éxito compartidos con el Frontend A.

El texto es parte del contrato de la API (US-01, US-01.3, US-10): el
frontend muestra literalmente estas cadenas, por lo que deben coincidir
carácter a carácter con ``frontend-admin/src/constants/messages.js``.
"""

from __future__ import annotations

# --- US-01: control de credenciales -----------------------------------------
INVALID_CREDENTIALS = "Credenciales inválidas"
MISSING_TOKEN = "Falta el token de autenticación"
SESSION_EXPIRED = "Tu sesión expiró. Volvé a iniciar sesión."
SESSION_REVOKED = "La sesión ya no es válida. Volvé a iniciar sesión."

# --- CU-01.2: setup único ---------------------------------------------------
ALREADY_INITIALIZED = "La cuenta de administrador ya fue creada. Iniciá sesión."

# --- US-01.3 / US-10: recuperación de contraseña ------------------------------
RESET_TOKEN_INVALID = "El enlace de recuperación ha caducado o no es válido"
PASSWORD_UPDATED = "Contraseña actualizada correctamente"
#: Respuesta genérica de ``forgot-password``: no revela si el correo existe
#: para evitar enumeración de cuentas.
RESET_REQUEST_ACCEPTED = (
    "Si el correo está registrado, te enviamos un enlace de recuperación "
    "válido por 15 minutos."
)

# --- US-02 / US-09: parámetros de baneo --------------------------------------
SETTINGS_UPDATED = "Parámetros de baneo actualizados con éxito"
#: Se devuelve en el PUT porque GET y PUT comparten la misma representación
#: de los parámetros, sin envolverlos en un objeto adicional.

# --- US-08: lista blanca -----------------------------------------------------
WHITELIST_ENTRY_ADDED = "Dirección agregada a la lista blanca"
WHITELIST_ENTRY_EXISTS = "La dirección ya está en la lista blanca"
WHITELIST_ENTRY_REMOVED = "Dirección eliminada de la lista blanca"
WHITELIST_ENTRY_NOT_FOUND = "La dirección no está en la lista blanca"
PROTECTED_WHITELIST_ENTRY = "La IP local no puede eliminarse de la lista blanca"
INVALID_NETWORK_ENTRY = (
    "Ingresá una dirección IP o subred válida "
    "(por ejemplo 192.168.1.10 o 10.0.0.0/8)"
)

# --- Infraestructura ---------------------------------------------------------
AUTH_SERVICE_UNAVAILABLE = "Servicio de autenticación no disponible"
