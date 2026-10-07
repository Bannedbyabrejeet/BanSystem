/**
 * US-01.3 + US-10 — Restablecer la contraseña desde el enlace.
 *
 * Al abrir `/reset-password?token=...`:
 *  1. Lee el token de la query string.
 *  2. Consulta `GET /auth/verify-reset-token/{token}`.
 *     - 200  → muestra el formulario y la cuenta regresiva restante.
 *     - 404  → muestra "El enlace de recuperación ha caducado o no es válido"
 *              y no permite escribir nada.
 *  3. Al confirmar, rota la contraseña y vuelve al login con el mensaje
 *     "Contraseña actualizada correctamente".
 */

import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import { Alert, AuthLayout, Button, FullScreenLoader, PasswordField } from '../components/ui';
import { MESSAGES } from '../constants/messages';
import { useAuth } from '../context/AuthContext';
import { formatRemaining } from '../utils/formatRemaining';
import { validatePasswordField } from '../utils/validation';

const TOKEN_PATTERN = /^[A-Za-z0-9_-]{20,256}$/;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { checkResetToken, resetPassword } = useAuth();

  const token = useMemo(() => searchParams.get('token') ?? '', [searchParams]);

  // --- Verificación del token (US-10) ---
  const [verifying, setVerifying] = useState(true);
  const [tokenError, setTokenError] = useState('');
  const [expiresAt, setExpiresAt] = useState(null);
  const [remaining, setRemaining] = useState(0);

  // --- Formulario ---
  const [form, setForm] = useState({ newPassword: '', confirmPassword: '' });
  const [fieldError, setFieldError] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    if (!TOKEN_PATTERN.test(token)) {
      setTokenError(MESSAGES.RESET_TOKEN_MISSING);
      setVerifying(false);
      return undefined;
    }

    async function verify() {
      setVerifying(true);
      try {
        const data = await checkResetToken(token);
        if (cancelled) return;
        setExpiresAt(data.expires_at ? new Date(data.expires_at) : null);
        setRemaining(data.expires_in ?? 0);
        setTokenError('');
      } catch (error) {
        if (cancelled) return;
        setTokenError(
          error instanceof ApiError && error.isNetworkError
            ? MESSAGES.NETWORK_ERROR
            : MESSAGES.RESET_TOKEN_INVALID,
        );
      } finally {
        if (!cancelled) setVerifying(false);
      }
    }

    verify();
    return () => {
      cancelled = true;
    };
  }, [token, checkResetToken]);

  // Cuenta regresiva basada en la expiración informada por el servidor.
  useEffect(() => {
    if (!expiresAt || tokenError) return undefined;
    const tick = () => setRemaining(Math.max(0, Math.round((expiresAt.getTime() - Date.now()) / 1000)));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [expiresAt, tokenError]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError('');
    setFieldError('');

    const validationError = validatePasswordField(form.newPassword, form.confirmPassword);
    if (validationError) {
      setFieldError(validationError);
      return;
    }

    setLoading(true);
    try {
      const response = await resetPassword({
        token,
        newPassword: form.newPassword,
        confirmPassword: form.confirmPassword,
      });
      navigate('/login', {
        replace: true,
        state: { message: response?.message || MESSAGES.PASSWORD_UPDATED },
      });
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setTokenError(MESSAGES.RESET_TOKEN_INVALID);
        } else {
          setSubmitError(error.message);
        }
      } else {
        setSubmitError(MESSAGES.GENERIC_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }

  if (verifying) {
    return <FullScreenLoader message="Validando enlace de recuperación…" />;
  }

  if (tokenError) {
    return (
      <AuthLayout title="Enlace no válido" subtitle={tokenError}>
        <Alert message={tokenError} type="error" />
        <Link className="btn btn--primary" to="/forgot-password">
          Solicitar un nuevo enlace
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Establecer nueva contraseña"
      subtitle={MESSAGES.RESET_LINK_VALID}
      footer={
        <p>
          <Link to="/login">Volver al inicio de sesión</Link>
        </p>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert message={submitError} type="error" />
        <p className="form__note">
          El enlace vence en <strong>{formatRemaining(remaining)}</strong>. Al cambiar la
          contraseña se cierran todas las sesiones abiertas.
        </p>

        <PasswordField
          label="Nueva contraseña"
          name="newPassword"
          value={form.newPassword}
          onChange={handleChange}
          error={fieldError}
          autoComplete="new-password"
          showRules
          disabled={loading}
        />

        <PasswordField
          label="Confirmar contraseña"
          name="confirmPassword"
          value={form.confirmPassword}
          onChange={handleChange}
          error={fieldError && form.newPassword ? MESSAGES.PASSWORD_MATCH : undefined}
          autoComplete="new-password"
          disabled={loading}
        />

        <Button type="submit" loading={loading}>
          Guardar nueva contraseña
        </Button>
      </form>
    </AuthLayout>
  );
}
