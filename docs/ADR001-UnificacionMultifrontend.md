# ADR 001: Estrategia de Unificación Multi-Framework para Frontend

- **Estado:** Aprobado
- **Fecha:** 2026-09-02
- **Autores:** Santiago Mulet & Manuel Abrego

## Contexto y Restricción
El proyecto exige el desarrollo de la interfaz de usuario dividida en dos frameworks 
modernos diferentes (React y Vue.js). Se debe garantizar una navegación unificada,
sin recargas bruscas ni discrepancias de estilo o autenticación.

## Decisión
Se implementa una arquitectura basada en **Proxy Inverso con Nginx (Path-based Routing)** 
bajo un mismo origen HTTP (`http://localhost`), combinada con un **Shared Design System 
Tokens (Tailwind CSS)**.

## Ventajas Clave
1. **Aislamiento Total de Tecnologías:** Ni React ni Vue conocen las dependencias internas del otro.
2. **Sin Colisiones de Estado:** No hay riesgo de interferencia entre la reactividad de Vue 3 (Proxies) y React 18 (VDOM/Hooks).
3. **Seguridad Same-Origin:** El token JWT emitido por FastAPI en `/api/v1/auth/login` se comparte sin problemas de CORS entre ambas vistas.
4. **Resiliencia:** Si el microfrontend de logs requiere reiniciar su servidor de desarrollo o desplegarse por separado, el panel de administración sigue 100% operativo.
