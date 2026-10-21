/**
 * Politica de contraseñas del Frontend A.
 *
 * Replica exactamente `password_policy_violations()` de
 * `app/core/security.py` (Servicio 1). El backend sigue siendo la autoridad:
 * estas reglas solo evitan un viaje de red con datos que ya son invalidos.
 */

import { MESSAGES } from '../constants/messages';

export const PASSWORD_MIN_LENGTH = 12;
/**
 * Argon2id no trunca como bcrypt (que limitaba la contraseña a 72 bytes),
 * pero se acota la longitud como defensa contra agotamiento de recursos
 * durante el hashing. Debe coincidir con PASSWORD_MAX_BYTES del backend.
 */
export const PASSWORD_MAX_BYTES = 1024;

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

/* ------------------------------------------------------------------ *
 * Configuracion de baneos y lista blanca (Issue #6)
 * ------------------------------------------------------------------ */

/**
 * Limites alineados con `app/schemas/config.py` del Servicio 1.
 * El backend sigue siendo la autoridad final.
 */
export const BAN_LIMITS = Object.freeze({
  maxretry: { min: 1, max: 1000 },
  bantime: { min: 1, max: 525600 },
  findtime: { min: 1, max: 10080 },
});

/**
 * Valida un entero positivo estricto (sin decimales, signos ni espacios
 * internos). Devuelve el mensaje de error o `null`.
 */
export function validatePositiveInteger(value, label, { min = 1, max } = {}) {
  const text = String(value ?? '').trim();
  if (!/^\d+$/.test(text)) {
    return `${label}: ${MESSAGES.INTEGER_REQUIRED}`;
  }

  const number = Number(text);
  if (!Number.isSafeInteger(number) || number < min) {
    return `${label}: ${MESSAGES.INTEGER_REQUIRED}`;
  }
  if (max !== undefined && number > max) {
    return `${label} no puede superar ${max}.`;
  }
  return null;
}

function isValidIPv4(value) {
  const parts = value.split('.');
  if (parts.length !== 4) return false;

  return parts.every(
    (part) =>
      /^\d{1,3}$/.test(part) &&
      Number(part) <= 255 &&
      (part === '0' || !part.startsWith('0')),
  );
}

function isHexGroup(value) {
  return /^[0-9a-fA-F]{1,4}$/.test(value);
}

function isValidIPv6(value) {
  if (!value.includes(':') || !/^[0-9a-fA-F:.]+$/.test(value)) return false;

  // Soporta IPv4 embebida (::ffff:192.168.1.1) reemplazandola por dos grupos.
  let text = value;
  if (text.includes('.')) {
    const lastColon = text.lastIndexOf(':');
    if (lastColon < 0) return false;
    const ipv4 = text.slice(lastColon + 1);
    if (!isValidIPv4(ipv4)) return false;
    text = `${text.slice(0, lastColon + 1)}0:0`;
  }

  if (text.includes('::')) {
    const sections = text.split('::');
    if (sections.length !== 2) return false;
    const left = sections[0] ? sections[0].split(':') : [];
    const right = sections[1] ? sections[1].split(':') : [];
    const groups = [...left, ...right];
    // "::" debe comprimir al menos un grupo (maximo 7 grupos explicitos).
    return groups.length <= 7 && groups.every(isHexGroup);
  }

  const groups = text.split(':');
  return groups.length === 8 && groups.every(isHexGroup);
}

/** `true` si el texto es una IP (v4/v6) o una red CIDR valida. */
export function isValidIpOrCidr(value) {
  const text = String(value ?? '').trim();
  if (!text) return false;

  const parts = text.split('/');
  if (parts.length > 2) return false;

  const address = parts[0];
  const isIpv6 = address.includes(':');
  if (isIpv6 ? !isValidIPv6(address) : !isValidIPv4(address)) {
    return false;
  }

  if (parts.length === 1) return true;

  const prefix = parts[1];
  if (!/^(0|[1-9]\d{0,2})$/.test(prefix)) return false;

  const number = Number(prefix);
  const maximum = isIpv6 ? 128 : 32;
  return number >= 0 && number <= maximum;
}

/** Valida el campo de alta de la lista blanca. */
export function validateNetworkEntry(value) {
  const text = String(value ?? '').trim();
  if (!text) return MESSAGES.REQUIRED_FIELD;
  return isValidIpOrCidr(text) ? null : MESSAGES.WHITELIST_INVALID;
}
