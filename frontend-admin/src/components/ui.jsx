/**
 * Componentes de interfaz reutilizables del modulo de autenticacion.
 * Presentacionales: no conocen la API ni el estado de sesion.
 */

import { useId, useState } from 'react';

import { PASSWORD_REQUIREMENTS } from '../constants/messages';
import { checkPasswordRules } from '../utils/validation';

/* ------------------------------------------------------------------ *
 * Boton
 * ------------------------------------------------------------------ */
export function Button({ children, type = 'submit', variant = 'primary', loading = false, disabled = false, ...props }) {
  return (
    <button
      type={type}
      className={`btn btn--${variant}`}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading && <span className="btn__spinner" aria-hidden="true" /> }
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ *
 * Campo de formulario
 * ------------------------------------------------------------------ */
export function Field({ label, name, type = 'text', error, hint, required = true, autoComplete, value, onChange, disabled = false, ...props }) {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  return (
    <div className={`field${error ? ' field--error' : ''}`}>
      <label className="field__label" htmlFor={id}>
        {label}
        {required && <span className="field__required" aria-hidden="true"> *</span>}
      </label>

      <input
        id={id}
        name={name}
        type={type}
        className="field__input"
        value={value}
        onChange={onChange}
        disabled={disabled}
        autoComplete={autoComplete}
        required={required}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={[hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ') || undefined}
        {...props}
      />

      {hint && !error && (
        <p className="field__hint" id={hintId}>
          {hint}
        </p>
      )}
      {error && (
        <p className="field__error" id={errorId} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Campo de contraseña con reglas de seguridad visibles
 * ------------------------------------------------------------------ */
export function PasswordField({ label, name, value, onChange, error, autoComplete = 'current-password', disabled = false, showRules = false, required = true, ...props }) {
  const [visible, setVisible] = useState(false);
  const rules = checkPasswordRules(value ?? '');

  return (
    <div className={`field${error ? ' field--error' : ''}`}>
      <Field
        label={label}
        name={name}
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        error={error}
        autoComplete={autoComplete}
        disabled={disabled}
        required={required}
        {...props}
      />

      <button
        type="button"
        className="field__toggle"
        onClick={() => setVisible((current) => !current)}
        disabled={disabled}
        aria-pressed={visible}
      >
        {visible ? 'Ocultar' : 'Ver'}
      </button>

      {showRules && (
        <ul className="password-rules" aria-label="Requisitos de la contraseña">
          {PASSWORD_REQUIREMENTS.map((requirement) => (
            <li
              key={requirement.id}
              className={`password-rule${rules[requirement.id] ? ' password-rule--ok' : ''}`}
            >
              <span aria-hidden="true">{rules[requirement.id] ? '✓' : '•'}</span>
              {requirement.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Mensaje de estado
 * ------------------------------------------------------------------ */
export function Alert({ message, type = 'info' }) {
  if (!message) return null;
  return (
    <div className={`alert alert--${type}`} role={type === 'error' ? 'alert' : 'status'}>
      {message}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Pantalla de carga
 * ------------------------------------------------------------------ */
export function FullScreenLoader({ message = 'Cargando…' }) {
  return (
    <div className="loader-page" role="status" aria-live="polite">
      <span className="loader-page__spinner" aria-hidden="true" />
      <p>{message}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Contenedor de las pantallas de autenticacion
 * ------------------------------------------------------------------ */
export function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <main className="auth">
      <section className="auth__card">
        <header className="auth__header">
          <div className="brand" aria-hidden="true">
            <span className="brand__shield" />
          </div>
          <h1 className="auth__title">{title}</h1>
          {subtitle && <p className="auth__subtitle">{subtitle}</p>}
        </header>

        {children}

        {footer && <footer className="auth__footer">{footer}</footer>}
      </section>
    </main>
  );
}
