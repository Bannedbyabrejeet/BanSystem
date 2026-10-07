/**
 * Guarda de ruta protegida (US-01): sin sesion valida no se entra.
 *
 * - Mientras se verifica el token: pantalla de carga (evita parpadeos).
 * - Si el sistema aun no fue inicializado: va a crear la cuenta unica.
 * - Si no hay sesion: va al login, remembering la ruta de origen.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { FullScreenLoader } from '../components/ui';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute() {
  const { isReady, isAuthenticated, isInitialized } = useAuth();
  const location = useLocation();

  if (!isReady) {
    return <FullScreenLoader message="Verificando sesión…" />;
  }

  if (!isInitialized) {
    return <Navigate to="/setup" replace />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
