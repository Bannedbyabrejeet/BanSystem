/**
 * US-02 / US-09 — Formulario de parámetros de baneo.
 *
 * Presenta los valores vigentes y valida en cliente antes de enviarlos al
 * Servicio 1. El backend vuelve a validar y es la fuente de verdad.
 */

import { useEffect, useState } from 'react';

import { MESSAGES } from '../../constants/messages';
import { BAN_LIMITS, validatePositiveInteger } from '../../utils/validation';
import { Button, Field } from '../ui';

const FIELDS = [
  {
    name: 'maxretry',
    label: 'Cantidad de intentos previos al baneo',
    hint: 'Intentos fallidos permitidos dentro de la ventana de tolerancia.',
  },
  {
    name: 'bantime',
    label: 'Tiempo de baneo (minutos)',
    hint: 'Duración del bloqueo aplicado por el firewall.',
  },
  {
    name: 'findtime',
    label: 'Ventana de tolerancia (minutos)',
    hint: 'Los intentos más antiguos que esta ventana se descartan.',
  },
];

function toForm(settings) {
  return {
    maxretry: String(settings.maxretry),
    bantime: String(settings.bantime),
    findtime: String(settings.findtime),
  };
}

export default function BanSettingsForm({ settings, onSave }) {
  const [form, setForm] = useState(() => toForm(settings));
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [saving, setSaving] = useState(false);

  // Si otro guardado o una recarga cambia los valores, el formulario se
  // sincroniza con lo que Redis devolvió.
  useEffect(() => {
    setForm(toForm(settings));
    setErrors({});
  }, [settings]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
    setSubmitError('');
  }

  function validate() {
    const nextErrors = {};

    for (const field of FIELDS) {
      const error = validatePositiveInteger(
        form[field.name],
        field.label,
        BAN_LIMITS[field.name],
      );
      if (error) nextErrors[field.name] = error;
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError('');

    if (!validate()) return;

    setSaving(true);
    try {
      await onSave({
        maxretry: Number(form.maxretry),
        bantime: Number(form.bantime),
        findtime: Number(form.findtime),
      });
    } catch (error) {
      setSubmitError(error?.message || MESSAGES.GENERIC_ERROR);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="config-form" onSubmit={handleSubmit} noValidate>
      <div className="config-form__grid">
        {FIELDS.map((field) => (
          <Field
            key={field.name}
            label={field.label}
            name={field.name}
            type="number"
            inputMode="numeric"
            min={BAN_LIMITS[field.name].min}
            max={BAN_LIMITS[field.name].max}
            step="1"
            value={form[field.name]}
            onChange={handleChange}
            error={errors[field.name]}
            hint={field.hint}
            disabled={saving}
          />
        ))}
      </div>

      {submitError && (
        <p className="field__error" role="alert">
          {submitError}
        </p>
      )}

      <div className="config-form__actions">
        <Button type="submit" loading={saving}>
          Guardar configuración
        </Button>
        <p className="config-form__note">
          El Servicio 2 toma los nuevos valores en la siguiente evaluación.
        </p>
      </div>
    </form>
  );
}
