/**
 * Proveedor del contexto de autenticación del Frontend A.
 *
 * Concentra el estado de sesión que consumen las rutas protegidas y las
 * pantallas. Se apoya en el Servicio 1 como única fuente de verdad:
 * el token JWT se valida en cada arranque llamando a `GET /auth/me`.
 *
 * La definición del contexto, los estados posibles y el hook `useAuth`
 * viven en `AuthContext.js` para que este archivo exporte únicamente
 * componentes (regla react-refresh: HMR estable durante el desarrollo).
 */

import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  ApiError,
  clearToken,
  fetchAuthStatus,
  fetchCurrentSession,
  login as loginRequest,
  readToken,
  requestPasswordReset,
  resetPassword as resetPasswordRequest,
  setupAdmin as setupAdminRequest,
  verifyResetToken,
  writeToken,
} from '../api/client';
import { AUTH_STATUS, AuthContext } from './AuthContext';

export function AuthProvider({ children }) {
  const [status, setStatus] = useState(AUTH_STATUS.LOADING);
  const [isInitialized, setIsInitialized] = useState(false);
  const [admin, setAdmin] = useState(null);
  const [serviceAvailable, setServiceAvailable] = useState(true);

  /** Cierra la sesión local y limpia el token. */
  const logout = useCallback(() => {
    clearToken();
    setAdmin(null);
  }, []);

  /**
   * Restaura la sesión al cargar la aplicación.
   * Sin token, solo consulta si el administrador ya fue creado.
   */
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const token = readToken();

        if (!token) {
          const authStatus = await fetchAuthStatus();
          if (cancelled) return;
          setIsInitialized(authStatus.initialized);
          setServiceAvailable(true);
          return;
        }

        // Hay token: el backend decide si sigue siendo válido.
        try {
          const session = await fetchCurrentSession();
          if (cancelled) return;
          setAdmin(session.admin);
          setIsInitialized(true);
          setServiceAvailable(true);
        } catch (error) {
          if (error instanceof ApiError && error.isUnauthorized) {
            // Token expirado o revocado: se descarta sin molestar al usuario.
            clearToken();
            const authStatus = await fetchAuthStatus();
            if (cancelled) return;
            setIsInitialized(authStatus.initialized);
          } else {
            if (!cancelled) setServiceAvailable(false);
            throw error;
          }
        }
      } catch {
        if (!cancelled) setServiceAvailable(false);
      } finally {
        if (!cancelled) setStatus(AUTH_STATUS.READY);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  /** US-01.2: crea la cuenta única de administrador. */
  const setupAdmin = useCallback(async (payload) => {
    const created = await setupAdminRequest(payload);
    setIsInitialized(true);
    return created;
  }, []);

  /** US-01: autentica y guarda el token para las siguientes peticiones. */
  const login = useCallback(async ({ identifier, password }) => {
    const data = await loginRequest({ identifier, password });
    writeToken(data.access_token);
    setAdmin(data.admin);
    setIsInitialized(true);
    return data;
  }, []);

  /** US-01.3: pide el enlace de recuperación. */
  const forgotPassword = useCallback(async (email) => {
    const response = await requestPasswordReset(email);
    return response;
  }, []);

  /** US-10: valida el token contra Redis antes de mostrar el formulario. */
  const checkResetToken = useCallback(async (token) => {
    return verifyResetToken(token);
  }, []);

  /** US-01.3: rota la contraseña y consume el token. */
  const resetPassword = useCallback(async (payload) => {
    const response = await resetPasswordRequest(payload);
    return response;
  }, []);

  const value = useMemo(
    () => ({
      status,
      isReady: status === AUTH_STATUS.READY,
      isInitialized,
      isAuthenticated: Boolean(admin),
      admin,
      serviceAvailable,
      setupAdmin,
      login,
      logout,
      forgotPassword,
      checkResetToken,
      resetPassword,
    }),
    [
      status,
      isInitialized,
      admin,
      serviceAvailable,
      setupAdmin,
      login,
      logout,
      forgotPassword,
      checkResetToken,
      resetPassword,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}