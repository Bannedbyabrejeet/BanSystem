/**
 * Mensajes de la interfaz.
 *
 * Los textos marcados como "contrato con el backend" deben coincidir
 * caracter a caracter con app/core/constants.py del Servicio 1, porque son
 * criterios de aceptacion de las historias US-01, US-01.3 y US-10.
 */

export const MESSAGES = {
  // --- Contrato con el backend ---
  INVALID_CREDENTIALS: 'Credenciales inválidas',
  PASSWORD_UPDATED: 'Contraseña actualizada correctamente',
  RESET_TOKEN_INVALID: 'El enlace de recuperación ha caducado o no es válido',
  AUTH_SERVICE_UNAVAILABLE: 'Servicio de autenticación no disponible',
  ALREADY_INITIALIZED: 'La cuenta de administrador ya fue creada. Iniciá sesión.',

  // --- Flujo de setup (US-01.2) ---
  SETUP_SUCCESS: 'Cuenta de administrador creada. Iniciá sesión con tus credenciales.',
  SETUP_INTRO:
    'Todavía no hay ningún administrador registrado. Creá la cuenta única que ' +
    'protegerá el panel de configuración.',

  // --- Recuperación (US-01.3) ---
  FORGOT_SENT:
    'Si el correo está registrado, te enviamos un enlace de recuperación válido por 15 minutos.',
  FORGOT_NO_TOKEN:
    'No pudimos enviar el correo. Revisá que el servidor SMTP esté configurado e intentá nuevamente.',
  RESET_LINK_VALID: 'El enlace es válido. Elegí tu nueva contraseña.',
  RESET_TOKEN_MISSING: 'El enlace no incluye un token de recuperación válido.',

  // --- Sesión ---
  SESSION_EXPIRED: 'Tu sesión expiró. Volvé a iniciar sesión.',
  SESSION_REVOKED: 'La sesión ya no es válida. Volvé a iniciar sesión.',
  LOGOUT_SUCCESS: 'Sesión cerrada correctamente.',

  // --- Errores de red / validacion ---
  NETWORK_ERROR: 'No pudimos conectar con el Servicio 1. Verificá que esté ejecutándose.',
  GENERIC_ERROR: 'Ocurrió un error inesperado. Intentá nuevamente.',
  REQUIRED_FIELD: 'Este campo es obligatorio.',
  INVALID_EMAIL: 'Ingresá un correo electrónico válido.',
  FIELDS_REQUIRED: 'Completá todos los campos para continuar.',

  // --- Política de contraseñas (debe replicar app/core/security.py) ---
  PASSWORD_MIN_LENGTH: 'Al menos 12 caracteres.',
  PASSWORD_UPPERCASE: 'Al menos una letra mayúscula.',
  PASSWORD_LOWERCASE: 'Al menos una letra minúscula.',
  PASSWORD_DIGIT: 'Al menos un número.',
  PASSWORD_BYTES: 'Máximo 72 bytes (límite de bcrypt).',
  PASSWORD_MATCH: 'Las contraseñas no coinciden.',
};

/** Etiquetas de los requisitos de contraseña, para mostrar la lista viva. */
export const PASSWORD_REQUIREMENTS = [
  { id: 'length', label: '12 caracteres o más' },
  { id: 'uppercase', label: 'Una mayúscula' },
  { id: 'lowercase', label: 'Una minúscula' },
  { id: 'digit', label: 'Un número' },
];
