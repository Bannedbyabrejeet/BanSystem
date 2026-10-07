import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Frontend A (React) de Bannedbyabrejeet.
 *
 * El frontend se sirve en http://localhost:3000 y consume el Servicio 1
 * (FastAPI) desde la MISMA ORIGEN a traves del proxy de Vite: las peticiones
 * a /api/* se reenvian a http://127.0.0.1:8000. Asi el navegador nunca hace
 * una peticion cross-origin y los tokens no dependen de CORS (ADR 001).
 *
 * Para hablar con un backend en otro origen: VITE_API_BASE_URL.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    host: true,
    proxy: {
      // Destino del Servicio 1 en desarrollo. Ajustable con
      // VITE_API_PROXY_TARGET si el backend no escucha en el 8000.
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 3000,
    strictPort: true,
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
});
