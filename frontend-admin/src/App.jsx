/**
 * Raíz de la aplicación: punto de entrada de la Issue #5.
 * Solo vistas de autenticación y el esqueleto del dashboard.
 */

import { Navigate, Route, Routes } from 'react-router-dom';

import { FullScreenLoader } from './components/ui';
import { useAuth } from './context/AuthContext';
import DashboardPage from './pages/DashboardPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import LoginPage from './pages/LoginPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import SetupPage from './pages/SetupPage';
import ProtectedRoute from './routes/ProtectedRoute';
import PublicOnlyRoute from './routes/PublicOnlyRoute';

/** Decide la primera pantalla según el estado de inicialización. */
function RootRedirect() {
  const { isReady, isInitialized, isAuthenticated, serviceAvailable } = useAuth();

  if (!isReady) {
    return <FullScreenLoader />;
  }
  if (!serviceAvailable) {
    return <Navigate to="/login" replace />;
  }
  if (!isInitialized) {
    return <Navigate to="/setup" replace />;
  }
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Visitantes sin sesión: setup, login y recuperación. */}
      <Route element={<PublicOnlyRoute />}>
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        {/* El enlace llega con el token en la query: accesible por URL directa. */}
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>

      {/* Sesión válida obligatoria. */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>

      <Route path="/" element={<RootRedirect />} />
      <Route path="*" element={<RootRedirect />} />
    </Routes>
  );
}
