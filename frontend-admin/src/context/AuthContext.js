/**
 * Contexto de autenticación: definición, hook de acceso y estados posibles.
 *
 * Vive en un módulo aparte de <AuthProvider> para que el archivo del
 * componente exporte solo componentes (regla react-refresh, HMR estable).
 */

import { createContext, useContext } from 'react';

/** Estados posibles de la inicialización de la sesión. */
export const AUTH_STATUS = {
  LOADING: 'loading',
  READY: 'ready',
};

/** Contexto de autenticación: `null` hasta que monta <AuthProvider>. */
export const AuthContext = createContext(null);

/** Lee el estado del contexto. Lanza error si se usa fuera del provider. */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de <AuthProvider>');
  }
  return context;
}
