/**
 * Destino tras un login exitoso (US-01: "da acceso al Dashboard principal").
 *
 * Alcance de la Issue #5: muestra la sesión activa y permite cerrarla.
 * Los paneles de parámetros de baneo, IPs baneadas e historial (issues #6,
 * #7 y #8) se incorporan en este mismo layout más adelante.
 */

import { Link, useNavigate } from 'react-router-dom';

import { AuthLayout, Button } from '../components/ui';
import { useAuth } from '../context/AuthContext';

const PENDIENTES = [
  {
    issue: '#6',
    titulo: 'Parámetros de baneo',
    detalle: 'Intentos fallidos previos al baneo y tiempo de baneo en minutos.',
  },
  {
    issue: '#7',
    titulo: 'IPs baneadas e historial',
    detalle: 'Listado de sanciones activas, historial y desbaneo manual.',
  },
  {
    issue: '#8',
    titulo: 'Visor de logs SSH',
    detalle: 'Eventos de acceso exitosos y fallidos en formato legible.',
  },
];

export default function DashboardPage() {
  const { admin, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true, state: { message: 'Sesión cerrada correctamente.' } });
  }

  return (
    <AuthLayout
      title="Panel de administración"
      subtitle={`Sesión activa como ${admin?.username ?? 'administrador'}`}
      footer={
        <p>
          ¿Necesitás cambiar la contraseña?{' '}
          <Link to="/forgot-password">Solicitar enlace de recuperación</Link>
        </p>
      }
    >
      <section className="dashboard">
        <div className="dashboard__session">
          <h2 className="dashboard__subtitle">Sesión actual</h2>
          <dl className="dashboard__data">
            <div>
              <dt>Administrador</dt>
              <dd>{admin?.username}</dd>
            </div>
            <div>
              <dt>Correo</dt>
              <dd>{admin?.email}</dd>
            </div>
            <div>
              <dt>Cuenta creada</dt>
              <dd>{admin ? new Date(admin.created_at).toLocaleString('es-AR') : '—'}</dd>
            </div>
          </dl>
          <Button type="button" variant="secondary" onClick={handleLogout}>
            Cerrar sesión
          </Button>
        </div>

        <div className="dashboard__pending">
          <h2 className="dashboard__subtitle">Próximas secciones</h2>
          <ul className="dashboard__list">
            {PENDIENTES.map((item) => (
              <li key={item.issue}>
                <span className="dashboard__tag">{item.issue}</span>
                <div>
                  <strong>{item.titulo}</strong>
                  <p>{item.detalle}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </AuthLayout>
  );
}
