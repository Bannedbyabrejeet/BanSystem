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

# --- Infraestructura ---------------------------------------------------------
AUTH_SERVICE_UNAVAILABLE = "Servicio de autenticación no disponible"
