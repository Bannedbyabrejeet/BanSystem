/**
 * Politica de contraseñas del Frontend A.
 *
 * Replica exactamente `password_policy_violations()` de
 * `app/core/security.py` (Servicio 1). El backend sigue siendo la autoridad:
 * estas reglas solo evitan un viaje de red con datos que ya son invalidos.
 */

import { MESSAGES } from '../constants/messages';

export const PASSWORD_MIN_LENGTH = 12;
export const PASSWORD_MAX_BYTES = 72;

/** Misma lista de contraseñas triviales que bloquea el backend. */
const WEAK_PASSWORDS = new Set([
  'administrador',
  'bannedbyabrejeet',
  'changeme12345',
  'contrasena1234',
  'password1234',
  'password12345',
  'qwertyuiop123',
  'administrador1',
  'adminadmin1234',
  '1234567890123',
]);

/** Cuántos bytes ocupa la contraseña cuando se guarda en UTF-8. */
export function passwordByteLength(password) {
  return new TextEncoder().encode(password).length;
}

/** Evalúa cada regla y devuelve un objeto `{ regla: booleano }`. */
export function checkPasswordRules(password) {
  const value = password ?? '';
  return {
    length: value.length >= PASSWORD_MIN_LENGTH,
    uppercase: /[A-ZÁ-Ü]/.test(value),
    lowercase: /[a-zá-ü]/.test(value),
    digit: /\d/.test(value),
    bytes: passwordByteLength(value) <= PASSWORD_MAX_BYTES,
  };
}

/** Lista de reglas incumplidas (vacía si la contraseña es aceptable). */
export function getPasswordViolations(password) {
  const rules = checkPasswordRules(password);
  const violations = [];

  if (!rules.length) {
    violations.push(
      MESSAGES.PASSWORD_MIN_LENGTH.replace('12', String(PASSWORD_MIN_LENGTH)),
    );
  }
  if (!rules.uppercase) violations.push(MESSAGES.PASSWORD_UPPERCASE);
  if (!rules.lowercase) violations.push(MESSAGES.PASSWORD_LOWERCASE);
  if (!rules.digit) violations.push(MESSAGES.PASSWORD_DIGIT);
  if (!rules.bytes) violations.push(MESSAGES.PASSWORD_BYTES);
  if (WEAK_PASSWORDS.has((password ?? '').trim().toLowerCase())) {
    violations.push('La contraseña es demasiado común. Elegí una más difícil de adivinar.');
  }
  return violations;
}

/** `true` si la contraseña cumple la política. */
export function isPasswordValid(password) {
  return getPasswordViolations(password).length === 0;
}

/** Validación de correo equivalente a la del backend. */
export function isEmailValid(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test((email ?? '').trim());
}

/**
 * Valida el campo de contraseña de un formulario (setup o reset).
 * @returns {string|null} mensaje de error, o `null` si es válida.
 */
export function validatePasswordField(password, confirmation) {
  if (!password) return MESSAGES.REQUIRED_FIELD;
  if (confirmation !== undefined && password !== confirmation) {
    return MESSAGES.PASSWORD_MATCH;
  }
  const violations = getPasswordViolations(password);
  return violations.length > 0 ? violations[0] : null;
}
