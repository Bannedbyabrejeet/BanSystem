import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

/**
 * Frontend B (Vue 3) — consola operativa.
 *
 * En producción se publica bajo `/logs/` detrás del mismo origen que el
 * Frontend A (ADR 001). En desarrollo se puede abrir directo en el puerto
 * 3001 o, preferentemente, a través del proxy del Frontend A:
 * `http://localhost:3000/logs/`. Así el token de `sessionStorage` se comparte.
 */
export default defineConfig({
  plugins: [vue()],
  base: '/logs/',
  server: {
    port: 3001,
    strictPort: true,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/telemetry': {
        target: process.env.VITE_TELEMETRY_PROXY_TARGET || 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 3001,
    strictPort: true,
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
});
