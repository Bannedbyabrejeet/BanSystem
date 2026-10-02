/**
 * Cliente HTTP del Frontend A hacia el Servicio 1 (FastAPI).
 *
 * Decisiones:
 * - **Misma origen por defecto**: si `VITE_API_BASE_URL` esta vacio se usan
 *   rutas relativas (`/api/v1`), que el proxy de Vite reenvia al backend.
 *   Asi el token viaja sin depender de CORS (ADR 001).
 * - **Token en sessionStorage**: se pierde al cerrar la pestana, a diferencia
 *   de localStorage, y se adjunta automaticamente en cada peticion.
 * - **Errores normalizados**: el backend responde `{ "detail": ... }`, que
 *   puede ser un string o una lista (validacion de Pydantic). `ApiError`
 *   expone siempre un `message` utilizable por la interfaz.
 */

import axios from 'axios';
import { MESSAGES } from '../constants/messages';

const TOKEN_STORAGE_KEY = 'bba.admin.token';

const baseURL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');

/** Clave de almacenamiento del token (expuesta para los tests). */
export const TOKEN_KEY = TOKEN_STORAGE_KEY;

/** Lee el token de sesión, tolerando el modo privado del navegador. */
export function readToken() {
  try {
    return window.sessionStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    // El navegador bloquea el almacenamiento (modo privado, cookies de terceros
    // deshabilitadas). La sesión durará lo que dure la pestaña en memoria.
    return null;
  }
}

/** Guarda el token de sesión. */
export function writeToken(token) {
  try {
    window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    /* sin almacenamiento disponible: se sigue trabajando en memoria */
  }
}

/** Elimina el token de sesión. */
export function clearToken() {
  try {
    window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    /* sin almacenamiento disponible */
  }
}

export const http = axios.create({
  baseURL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
});

// Adjunta el token Bearer a cada petición.
http.interceptors.request.use((config) => {
  const token = readToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Error de API con estado HTTP y mensaje listo para mostrar.
 */
export class ApiError extends Error {
  constructor(message, { status = 0, details = [] } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }

  /** `true` cuando el servidor no respondió (no es un error HTTP). */
  get isNetworkError() {
    return this.status === 0;
  }

  /** `true` cuando la sesión dejó de ser válida. */
  get isUnauthorized() {
    return this.status === 401;
  }
}

/** Normaliza cualquier error de axios a un `ApiError`. */
function toApiError(error) {
  if (error instanceof ApiError) {
    return error;
  }

  if (!error.response) {
    return new ApiError(MESSAGES.NETWORK_ERROR, { status: 0 });
  }

  const { status, data } = error.response;
  const detail = data && data.detail;

  if (Array.isArray(detail)) {
    // Validación de Pydantic: lista de mensajes legibles.
    return new ApiError(detail.join(' '), { status, details: detail });
  }
  if (typeof detail === 'string' && detail.trim() !== '') {
    return new ApiError(detail, { status, details: [detail] });
  }
  return new ApiError(MESSAGES.GENERIC_ERROR, { status });
}

http.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(toApiError(error)),
);

/**
 * Envuelve una llamada y devuelve solo `response.data`, o lanza `ApiError`.
 * @template T
 * @param {import('axios').AxiosRequestConfig} config
 * @returns {Promise<T>}
 */
async function request(config) {
  const response = await http.request(config);
  return response.data;
}

/* ------------------------------------------------------------------ *
 * Endpoints de autenticacion (documentados en /docs del Servicio 1)
 * ------------------------------------------------------------------ */

/** `GET /auth/status` → `{ initialized: boolean }` */
export function fetchAuthStatus() {
  return request({ method: 'GET', url: '/auth/status' });
}

/** `POST /auth/setup` — crea la cuenta unica de administrador. */
export function setupAdmin({ username, email, password, passwordConfirm }) {
  return request({
    method: 'POST',
    url: '/auth/setup',
    data: {
      username: username.trim(),
      email: email.trim(),
      password,
      password_confirm: passwordConfirm,
    },
  });
}

/** `POST /auth/login` → `{ access_token, expires_in, admin }` */
export function login({ identifier, password }) {
  return request({
    method: 'POST',
    url: '/auth/login',
    data: { identifier: identifier.trim(), password },
  });
}

/** `POST /auth/forgot-password` — genera el token con TTL en Redis. */
export function requestPasswordReset(email) {
  return request({
    method: 'POST',
    url: '/auth/forgot-password',
    data: { email: email.trim() },
  });
}

/** `GET /auth/verify-reset-token/{token}` → `{ valid, expires_in }` */
export function verifyResetToken(token) {
  return request({ method: 'GET', url: `/auth/verify-reset-token/${encodeURIComponent(token)}` });
}

/** `POST /auth/reset-password` — consume el token y rota la contraseña. */
export function resetPassword({ token, newPassword, confirmPassword }) {
  return request({
    method: 'POST',
    url: '/auth/reset-password',
    data: {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    },
  });
}

/** `GET /auth/me` — valida el JWT contra Redis. */
export function fetchCurrentSession() {
  return request({ method: 'GET', url: '/auth/me' });
}
