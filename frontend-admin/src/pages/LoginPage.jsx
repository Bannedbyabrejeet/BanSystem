/**
 * US-01 / CU-01 — Inicio de sesion del administrador.
 *
 * Con credenciales incorrectas el Servicio 1 responde 401 y la interfaz
 * muestra exactamente "Credenciales inválidas".
 */

import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { ApiError } from '../api/client';
import { Alert, AuthLayout, Button, Field, PasswordField } from '../components/ui';
import { MESSAGES } from '../constants/messages';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login, isInitialized } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({ identifier: '', password: '' });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [successMessage, setSuccessMessage] = useState(location.state?.message ?? '');
  const [loading, setLoading] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function validate() {
    const nextErrors = {};
    if (!form.identifier.trim()) {
      nextErrors.identifier = MESSAGES.REQUIRED_FIELD;
    }
    if (!form.password) {
      nextErrors.password = MESSAGES.REQUIRED_FIELD;
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError('');
    setSuccessMessage('');

    if (!validate()) {
      return;
    }

    setLoading(true);
    try {
      await login(form);
      // Vuelve a la ruta que el guardia protegido memorizó, o al dashboard.
      const destination = location.state?.from?.pathname ?? '/dashboard';
      navigate(destination, { replace: true });
    } catch (error) {
      if (error instanceof ApiError) {
        // El backend ya devuelve el texto contractual; se respeta tal cual.
        setSubmitError(error.isUnauthorized ? MESSAGES.INVALID_CREDENTIALS : error.message);
      } else {
        setSubmitError(MESSAGES.GENERIC_ERROR);
      }
      setForm((current) => ({ ...current, password: '' }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Iniciar sesión"
      subtitle="Acceso exclusivo del administrador de Bannedbyabrejeet."
      footer={
        <p>
          <Link to="/forgot-password">Olvidé mi contraseña</Link>
          {isInitialized ? ' · ' : ' · '}
          <Link to="/setup">Crear cuenta</Link>
        </p>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert message={successMessage} type="success" />
        <Alert message={submitError} type="error" />

        <Field
          label="Usuario o correo"
          name="identifier"
          value={form.identifier}
          onChange={handleChange}
          error={errors.identifier}
          autoComplete="username"
          placeholder="admin"
          disabled={loading}
        />

        <PasswordField
          label="Contraseña"
          name="password"
          value={form.password}
          onChange={handleChange}
          error={errors.password}
          disabled={loading}
        />

        <Button type="submit" loading={loading}>
          Iniciar sesión
        </Button>
      </form>
    </AuthLayout>
  );
}
