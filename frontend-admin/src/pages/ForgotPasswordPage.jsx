/**
 * US-01.3 — "Olvidé mi contraseña".
 *
 * El Servicio 1 genera un token con TTL nativo en Redis (SETEX, 900 s) y
 * envía el correo con el enlace `/reset-password?token=...`.
 *
 * La interfaz muestra siempre el mismo mensaje, exista o no el correo
 * registrado, para no permitir enumerar cuentas.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';

import { ApiError } from '../api/client';
import { Alert, AuthLayout, Button, Field } from '../components/ui';
import { MESSAGES } from '../constants/messages';
import { useAuth } from '../context/AuthContext';
import { isEmailValid } from '../utils/validation';

export default function ForgotPasswordPage() {
  const { forgotPassword } = useAuth();

  const [email, setEmail] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [serverError, setServerError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setServerError('');
    setInfo('');

    if (!email.trim()) {
      setFieldError(MESSAGES.REQUIRED_FIELD);
      return;
    }
    if (!isEmailValid(email)) {
      setFieldError(MESSAGES.INVALID_EMAIL);
      return;
    }

    setFieldError('');
    setLoading(true);
    try {
      const response = await forgotPassword(email);
      setInfo(response?.message || MESSAGES.FORGOT_SENT);
      setSent(true);
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setServerError(
          requestError.status === 502 ? MESSAGES.FORGOT_NO_TOKEN : requestError.message,
        );
      } else {
        setServerError(MESSAGES.GENERIC_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Recuperar contraseña"
      subtitle="Te enviamos un enlace temporal para establecer una nueva contraseña."
      footer={
        <p>
          <Link to="/login">Volver al inicio de sesión</Link>
        </p>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert message={serverError} type="error" />
        <Alert message={info} type="info" />

        <Field
          label="Correo electrónico"
          name="email"
          type="email"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
            setFieldError('');
            setServerError('');
            setInfo('');
            setSent(false);
          }}
          error={fieldError}
          autoComplete="email"
          placeholder="admin@ejemplo.com"
          disabled={loading}
          required
        />

        <Button type="submit" loading={loading} disabled={sent}>
          {sent ? 'Enlace solicitado' : 'Enviar enlace de recuperación'}
        </Button>

        {sent && (
          <p className="form__note">
            Con <code>MAIL_MODE=log</code> el enlace completo se imprime en los logs del
            contenedor del Servicio 1.
          </p>
        )}
      </form>
    </AuthLayout>
  );
}
