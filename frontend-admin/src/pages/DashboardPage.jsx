/**
 * Dashboard del administrador (US-01) con la configuración de la Issue #6.
 *
 * Incluye:
 * - Sesión activa y cierre de sesión.
 * - US-02 / US-09: umbral de intentos, tiempo de baneo y ventana de tolerancia.
 * - US-08: alta y baja de IPs/subredes de la lista blanca.
 *
 * Las secciones de IPs baneadas y logs SSH (issues #7 y #8) siguen pendientes.
 */

import { Link, useNavigate } from 'react-router-dom';

import BanSettingsForm from '../components/config/BanSettingsForm';
import WhitelistPanel from '../components/config/WhitelistPanel';
import { Alert, AuthLayout, Button } from '../components/ui';
import { MESSAGES } from '../constants/messages';
import { useAuth } from '../context/AuthContext';
import useBanConfig from '../hooks/useBanConfig';

const PENDIENTES = [
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
  const {
    settings,
    whitelist,
    loading,
    loadError,
    success,
    retry,
    saveSettings,
    addEntry,
    removeEntry,
  } = useBanConfig();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true, state: { message: MESSAGES.LOGOUT_SUCCESS } });
  }

  return (
    <AuthLayout
      wide
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
        <div className="dashboard__panel dashboard__session">
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

        <Alert message={success} type="success" />

        {loadError && (
          <div className="dashboard__panel">
            <Alert message={loadError} type="error" />
            <Button
              type="button"
              variant="secondary"
              onClick={retry}
            >
              Reintentar
            </Button>
          </div>
        )}

        {loading && !loadError && (
          <p className="dashboard__loading" role="status">
            Cargando configuración…
          </p>
        )}

        {!loading && !loadError && settings && (
          <div className="dashboard__panel">
            <header className="dashboard__section-header">
              <div>
                <h2 className="dashboard__subtitle">Parámetros de baneo</h2>
                <p className="dashboard__description">
                  Ajustá la rigurosidad de la protección SSH. Los tres valores se
                  guardan juntos en Redis.
                </p>
              </div>
              <span className="dashboard__tag">US-02 · US-09</span>
            </header>
            <BanSettingsForm settings={settings} onSave={saveSettings} />
          </div>
        )}

        {!loading && !loadError && (
          <div className="dashboard__panel">
            <header className="dashboard__section-header">
              <div>
                <h2 className="dashboard__subtitle">Lista blanca</h2>
                <p className="dashboard__description">
                  Las direcciones y subredes listadas quedan exentas de bloqueos.
                  Las IPs locales siempre están protegidas.
                </p>
              </div>
              <span className="dashboard__tag">US-08</span>
            </header>
            <WhitelistPanel
              entries={whitelist.entries}
              protectedEntries={whitelist.protected_entries}
              onAdd={addEntry}
              onRemove={removeEntry}
            />
          </div>
        )}

        <div className="dashboard__panel dashboard__pending">
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
