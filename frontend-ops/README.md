# Frontend B — Consola operativa (Vue 3)

Interfaz operativa de **Bannedbyabrejeet** para la Issue #9:

- **US-03 / FRONT-04:** visor de logs SSH con fecha/hora, IP, usuario y
  resultado, con diferenciación visual entre éxitos y fallos.
- **US-06:** dos estados de IPs: “Baneadas en el momento” e “Historial de
  baneadas anteriormente”.
- **US-07 / FRONT-05:** botón **Desbanear** en cada sanción activa, que envía
  la orden al Servicio 2 y elimina la regla de UFW + el timeout en Redis.

La autenticación se reutiliza del Frontend A: este módulo no implementa login
ni configuración de umbrales.

## Arquitectura de integración

Según el [ADR 001](../docs/ADR001-UnificacionMultifrontend.md), ambos
frontends viven bajo el mismo origen. En desarrollo se recomienda abrir la
consola a través del proxy del Frontend A:

```text
http://localhost:3000/logs/
```

Así el token JWT guardado por el Frontend A en `sessionStorage` se comparte
sin CORS ni duplicar el login.

Rutas:

| Ruta | Contenido |
|---|---|
| `/logs/` | Visor de logs SSH |
| `/logs/bans` | IPs baneadas e historial |

El frontend consume:

| Endpoint | Servicio |
|---|---|
| `GET /api/v1/auth/me` | Servicio 1 (validar sesión) |
| `GET /telemetry/logs` | Servicio 2 (eventos SSH) |
| `GET /telemetry/bans` | Servicio 2 (sanciones activas) |
| `GET /telemetry/history` | Servicio 2 (historial) |
| `DELETE /telemetry/bans/<ip>` | Servicio 2 (encolar desbaneo) |

## Ejecutar en desarrollo

Requisitos: Node.js 18.18+, Servicio 1 en `8000`, Servicio 2 Flask en `5000`
y el motor `python -m app` para que el worker procese los desbaneos.

```bash
cd frontend-ops
npm ci
npm run dev
```

La consola queda en `http://localhost:3001/logs/` si se abre directo. Para
compartir la sesión con el panel de administración, abrir:

```text
http://localhost:3000/logs/
```

El `vite.config.js` del Frontend A ya redirige `/logs` a `3001` y
`/telemetry` a `5000`.

## Variables

| Variable | Por defecto | Descripción |
|---|---|---|
| `VITE_ADMIN_LOGIN_URL` | `/login` | Login del Frontend A. |
| `VITE_ADMIN_DASHBOARD_URL` | `/dashboard` | Dashboard del Frontend A. |
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:8000` | Servicio 1 en desarrollo. |
| `VITE_TELEMETRY_PROXY_TARGET` | `http://127.0.0.1:5000` | Servicio 2 Flask en desarrollo. |

## Build

```bash
npm run build
```

El bundle queda en `build/`. En producción el proxy inverso debe servir
`/logs/*` con fallback de History API hacia `/logs/index.html` y enrutar
`/telemetry/*` al Servicio 2.
