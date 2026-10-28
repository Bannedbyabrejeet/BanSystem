/**
 * US-08 — Gestión de la lista blanca de IPs y subredes.
 *
 * Las entradas locales protegidas (127.0.0.1 y ::1) se muestran con un
 * candado y no pueden eliminarse desde la interfaz. El backend también
 * rechaza el intento con 409.
 */

import { useState } from 'react';

import { MESSAGES } from '../../constants/messages';
import { validateNetworkEntry } from '../../utils/validation';
import { Alert, Button, Field } from '../ui';

export default function WhitelistPanel({
  entries,
  protectedEntries,
  onAdd,
  onRemove,
}) {
  const [entry, setEntry] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [actionError, setActionError] = useState('');
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState(null);

  const protectedSet = new Set(protectedEntries);

  function handleChange(event) {
    setEntry(event.target.value);
    setFieldError('');
    setActionError('');
  }

  async function handleAdd(event) {
    event.preventDefault();
    setActionError('');

    const validationError = validateNetworkEntry(entry);
    if (validationError) {
      setFieldError(validationError);
      return;
    }

    setAdding(true);
    try {
      await onAdd(entry.trim());
      setEntry('');
    } catch (error) {
      setFieldError(error?.message || MESSAGES.GENERIC_ERROR);
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(target) {
    setActionError('');
    setRemoving(target);
    try {
      await onRemove(target);
    } catch (error) {
      setActionError(error?.message || MESSAGES.GENERIC_ERROR);
    } finally {
      setRemoving(null);
    }
  }

  return (
    <div className="whitelist">
      <form className="whitelist__form" onSubmit={handleAdd} noValidate>
        <div className="whitelist__input">
          <Field
            label="Agregar IP o subred"
            name="entry"
            value={entry}
            onChange={handleChange}
            error={fieldError}
            placeholder="192.168.1.10 o 10.0.0.0/8"
            hint="Acepta IPv4, IPv6 y notación CIDR. Las IPs locales están protegidas."
            disabled={adding}
          />
        </div>
        <Button type="submit" loading={adding}>
          Agregar
        </Button>
      </form>

      <Alert message={actionError} type="error" />

      <ul className="whitelist__list">
        {entries.map((item) => {
          const isProtected = protectedSet.has(item);
          return (
            <li key={item} className="whitelist__item">
              <div className="whitelist__entry">
                <code>{item}</code>
                {isProtected && (
                  <span className="badge badge--protected" title="No puede eliminarse">
                    Protegida
                  </span>
                )}
              </div>

              <Button
                type="button"
                variant="danger"
                loading={removing === item}
                disabled={isProtected || removing !== null}
                title={
                  isProtected
                    ? MESSAGES.WHITELIST_PROTECTED
                    : `Eliminar ${item} de la lista blanca`
                }
                onClick={() => handleRemove(item)}
              >
                Eliminar
              </Button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
