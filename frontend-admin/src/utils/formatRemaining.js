/**
 * Formatea segundos restantes como "mm:ss" (cuenta regresiva del enlace).
 *
 * @param {number} totalSeconds
 * @returns {string}
 */
export function formatRemaining(totalSeconds) {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const minutes = String(Math.floor(safe / 60)).padStart(2, '0');
  const seconds = String(safe % 60).padStart(2, '0');
  return `${minutes}:${seconds}`;
}
