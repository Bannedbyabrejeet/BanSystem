/**
 * US-01.2 / CU-01.2 — Crear la cuenta unica de administrador.
 *
 * Solo es accesible mientras Redis no tenga un administrador. Tras crearlo,
 * el backend responde 409 y esta ruta queda cerrada de forma permanente.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ApiError } from '../api/client';
import { Alert, AuthLayout, Button, Field, PasswordField } from '../components/ui';
import { MESSAGES } from '../constants/messages';
import { useAuth } from '../context/AuthContext';
import { isEmailValid, validatePasswordField } from '../utils/validation';

const EMPTY_FORM = { username: '', email: '', password: '', passwordConfirm: '' };

export default function SetupPage() {
  const { setupAdmin, isInitialized } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined, submit: undefined }));
  }

  /** Validacion en cliente; el backend vuelve a validar todo. */
  function validate() {
    const nextErrors = {};

    if (!form.username.trim()) {
      nextErrors.username = MESSAGES.REQUIRED_FIELD;
    } else if (form.username.trim().length < 3) {
      nextErrors.username = 'El usuario debe tener al menos 3 caracteres.';
    }

    if (!form.email.trim()) {
      nextErrors.email = MESSAGES.REQUIRED_FIELD;
    } else if (!isEmailValid(form.email)) {
      nextErrors.email = MESSAGES.INVALID_EMAIL;
    }

    const passwordError = validatePasswordField(form.password, form.passwordConfirm);
    if (passwordError) {
      nextErrors.password = passwordError;
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError('');

    if (!validate()) {
      return;
    }

    setLoading(true);
    try {
      await setupAdmin(form);
      navigate('/login', { replace: true, state: { message: MESSAGES.SETUP_SUCCESS } });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        // Otra petición creó la cuenta primero: se va al login.
        navigate('/login', { replace: true, state: { message: MESSAGES.SETUP_SUCCESS } });
        return;
      }
      setSubmitError(error instanceof ApiError ? error.message : MESSAGES.GENERIC_ERROR);
    } finally {
      setLoading(false);
    }
  }

  if (isInitialized) {
    return (
      <AuthLayout title="Cuenta ya creada" subtitle={MESSAGES.ALREADY_INITIALIZED}>
        <Link className="btn btn--primary" to="/login">
          Ir al inicio de sesión
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Crear cuenta de administrador"
      subtitle={MESSAGES.SETUP_INTRO}
      footer={
        <p>
          ¿Ya tenés una cuenta? <Link to="/login">Iniciá sesión</Link>
        </p>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert message={submitError} type="error" />

        <Field
          label="Usuario"
          name="username"
          value={form.username}
          onChange={handleChange}
          error={errors.username}
          autoComplete="username"
          placeholder="admin"
          disabled={loading}
        />

        <Field
          label="Correo electrónico"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          error={errors.email}
          autoComplete="email"
          placeholder="admin@ejemplo.com"
          hint="Aquí se enviarán los enlaces de recuperación de contraseña."
          disabled={loading}
        />

        <PasswordField
          label="Contraseña"
          name="password"
          value={form.password}
          onChange={handleChange}
          error={errors.password}
          autoComplete="new-password"
          showRules
          disabled={loading}
        />

        <PasswordField
          label="Confirmar contraseña"
          name="passwordConfirm"
          value={form.passwordConfirm}
          onChange={handleChange}
          error={errors.passwordConfirm}
          autoComplete="new-password"
          disabled={loading}
        />

        <Button type="submit" loading={loading}>
          Crear cuenta
        </Button>
      </form>
    </AuthLayout>
  );
}
