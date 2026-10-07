/**
 * Guarda de ruta publica: solo para visitantes sin sesion.
 * Si ya hay sesion activa, redirige al dashboard.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { FullScreenLoader } from '../components/ui';
import { useAuth } from '../context/AuthContext';

export default function PublicOnlyRoute() {
  const { isReady, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isReady) {
    return <FullScreenLoader message="Verificando sesión…" />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // `state.from` permite volver a la pagina solicitada tras el login.
  return <Outlet state={{ from: location }} />;
}
