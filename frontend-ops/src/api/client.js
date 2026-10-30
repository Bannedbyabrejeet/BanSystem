import axios from 'axios';

import { MESSAGES } from '../constants/messages';

/** Misma clave que usa el Frontend A: el token se comparte en el mismo origen. */
export const TOKEN_KEY = 'bba.admin.token';

export function readToken() {
  try {
    return window.sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function clearToken() {
  try {
    window.sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* sin almacenamiento disponible */
  }
}

export class ApiError extends Error {
  constructor(message, { status = 0, details = [] } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }

  get isUnauthorized() {
    return this.status === 401;
  }

  get isNetworkError() {
    return this.status === 0;
  }
}

const http = axios.create({
  baseURL: '',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
});

http.interceptors.request.use((config) => {
  const token = readToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function toApiError(error) {
  if (error instanceof ApiError) return error;
  if (!error.response) {
    return new ApiError(MESSAGES.NETWORK_ERROR, { status: 0 });
  }
  const { status, data } = error.response;
  const detail = data && data.detail;
  if (Array.isArray(detail)) {
    return new ApiError(detail.join(' '), { status, details: detail });
  }
  if (typeof detail === 'string' && detail.trim()) {
    return new ApiError(detail, { status, details: [detail] });
  }
  return new ApiError(MESSAGES.GENERIC_ERROR, { status });
}

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.dispatchEvent(new Event('bba:unauthorized'));
    }
    return Promise.reject(toApiError(error));
  },
);

async function request(config) {
  const response = await http.request(config);
  return response.data;
}

/** Valida la sesión reutilizando el endpoint del Servicio 1. */
export function fetchSession() {
  return request({ method: 'GET', url: '/api/v1/auth/me' });
}

/** Eventos SSH parseados por el Servicio 2. */
export function fetchLogs({ limit = 25, offset = 0, outcome = '', ip = '', username = '' } = {}) {
  const params = { limit, offset };
  if (outcome) params.outcome = outcome;
  if (ip.trim()) params.ip = ip.trim();
  if (username.trim()) params.username = username.trim();
  return request({ method: 'GET', url: '/telemetry/logs', params });
}

/** IPs baneadas en este momento. */
export function fetchBans() {
  return request({ method: 'GET', url: '/telemetry/bans' });
}

/** Historial de baneos y desbaneos. */
export function fetchHistory({ limit = 50, offset = 0 } = {}) {
  return request({
    method: 'GET',
    url: '/telemetry/history',
    params: { limit, offset },
  });
}

/** Encola el desbaneo manual de una IP. */
export function requestUnban(ip) {
  return request({
    method: 'DELETE',
    url: `/telemetry/bans/${encodeURIComponent(ip)}`,
  });
}
