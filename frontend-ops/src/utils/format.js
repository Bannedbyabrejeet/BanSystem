/** Utilidades de formato para la consola operativa. */

export function formatDateTime(timestamp) {
  if (!timestamp) return '—';
  return new Date(Number(timestamp) * 1000).toLocaleString('es-AR', {
    dateStyle: 'short',
    timeStyle: 'medium',
  });
}

export function formatDuration(minutes) {
  const value = Number(minutes) || 0;
  if (value < 60) return `${value} min`;
  const hours = Math.floor(value / 60);
  const rest = value % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

export function formatRemaining(expiresAt) {
  const remaining = Number(expiresAt) - Math.floor(Date.now() / 1000);
  if (remaining <= 0) return 'Vencida';
  const minutes = Math.ceil(remaining / 60);
  return formatDuration(minutes);
}

export function outcomeLabel(outcome) {
  return outcome === 'success' ? 'Éxito' : 'Fallo';
}

export function actionLabel(action) {
  if (action === 'banned') return 'Baneada';
  if (action === 'unbanned') return 'Desbaneada';
  return action || '—';
}

export function unbanReasonLabel(reason) {
  if (reason === 'manual') return 'Manual';
  if (reason === 'timeout') return 'Timeout';
  return reason || '—';
}
