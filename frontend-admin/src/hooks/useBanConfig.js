/**
 * Estado y operaciones de la configuración de baneos (Issue #6).
 *
 * Concentra el acceso a la API para que el dashboard solo se ocupe de la
 * presentación. Toda escritura devuelve el estado completo desde el Servicio 1
 * y se refleja en la interfaz sin volver a pedirlo.
 */

import { useEffect, useState } from 'react';

import {
  ApiError,
  addWhitelistEntry,
  fetchBanSettings,
  fetchWhitelist,
  removeWhitelistEntry,
  updateBanSettings,
} from '../api/client';
import { MESSAGES } from '../constants/messages';

const EMPTY_WHITELIST = { entries: [], protected_entries: [] };

export default function useBanConfig() {
  const [settings, setSettings] = useState(null);
  const [whitelist, setWhitelist] = useState(EMPTY_WHITELIST);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [success, setSuccess] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadConfig() {
      setLoading(true);
      setLoadError('');
      try {
        const [banSettings, whitelistState] = await Promise.all([
          fetchBanSettings(),
          fetchWhitelist(),
        ]);
        if (cancelled) return;
        setSettings(banSettings);
        setWhitelist(whitelistState);
      } catch (error) {
        if (cancelled) return;
        setLoadError(
          error instanceof ApiError ? error.message : MESSAGES.CONFIG_LOAD_ERROR,
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadConfig();
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  function applyWhitelist(response) {
    setWhitelist({
      entries: response.entries,
      protected_entries: response.protected_entries,
    });
  }

  async function saveSettings(values) {
    setSuccess('');
    const saved = await updateBanSettings(values);
    setSettings(saved);
    setSuccess(MESSAGES.BAN_SETTINGS_UPDATED);
  }

  async function addEntry(entry) {
    setSuccess('');
    const response = await addWhitelistEntry(entry);
    applyWhitelist(response);
    setSuccess(response.message || MESSAGES.WHITELIST_ADDED);
  }

  async function removeEntry(entry) {
    setSuccess('');
    const response = await removeWhitelistEntry(entry);
    applyWhitelist(response);
    setSuccess(response.message || MESSAGES.WHITELIST_REMOVED);
  }

  return {
    settings,
    whitelist,
    loading,
    loadError,
    success,
    retry: () => setReloadKey((current) => current + 1),
    saveSettings,
    addEntry,
    removeEntry,
  };
}
