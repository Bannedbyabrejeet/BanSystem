# Documentación técnica — Bannedbyabrejeet

> **Última actualización:** 2026-10-21

Índice de la documentación técnica del repositorio. Para el **estado de avance por issue** (qué está cerrado y qué falta) ver [`../docs_contexto/04_estado_actual_y_tareas.md`](../docs_contexto/04_estado_actual_y_tareas.md).

---

## 1. Contenido de `docs/`

| Documento | Qué es | Última revisión |
|---|---|---|
| [`REDIS_SCHEMA.md`](REDIS_SCHEMA.md) | Esquema completo de claves Redis (hash, set, zset, streams) y **contrato de datos** entre el Servicio 1 y el Servicio 2 | 2026-10-21 |
| [`DOCKER_REDIS.md`](DOCKER_REDIS.md) | Guía operativa de la infraestructura: compose, `redis.conf`, persistencia, variables de entorno y troubleshooting | 2026-10-21 |
| [`ADR001-UnificacionMultifrontend.md`](ADR001-UnificacionMultifrontend.md) | Decisión de arquitectura: estrategia multi-framework (React + Vue) con tokens de diseño compartidos | 2026-09-02 |
| [`contrato-desbaneo.yaml`](contrato-desbaneo.yaml) | Contrato del broker de desbaneo manual: stream `security:events:unban` y grupo de consumidores `ufw_workers` | 2026-09-04 |
| [`sequencia-inter_servicios.mmd`](sequencia-inter_servicios.mmd) · [`.png`](sequencia-inter_servicios.png) | Diagrama de secuencia del flujo de desbaneo manual (Admin → Frontend → Servicio 1 → Redis → Servicio 2 → UFW) | 2026-09-04 |
| [`EVALUACION.md`](EVALUACION.md) | Informe de calidad y autoría generado por la cátedra. **No editar a mano**: se regenera en cada evaluación | 2026-10-17 |
| [`evidencias/issue-06.md`](evidencias/issue-06.md) | Capturas del dashboard, persistencia en Redis y resultados de las pruebas de la Issue #6 | 2026-10-21 |
| [`evidencias/issue-07-backend-b.md`](evidencias/issue-07-backend-b.md) | Pruebas del lector SSH/motor, contador, whitelist y reset por `findtime` | 2026-10-28 |
| [`historico/`](historico/) | Borradores descartados, conservados solo como registro del diseño original | — |

---

## 2. Documentación de contexto

En [`../docs_contexto/`](../docs_contexto/), pensada para que un agente o una persona nueva entienda el proyecto sin leer todo el código:

| Documento | Qué es | Última revisión |
|---|---|---|
| [`01_vision_y_requisitos.md`](../docs_contexto/01_vision_y_requisitos.md) | Visión del producto, roles, requisitos funcionales y no funcionales | 2026-10-07 |
| [`02_arquitectura_del_sistema.md`](../docs_contexto/02_arquitectura_del_sistema.md) | Arquitectura de los servicios, la base de datos y los frontends | 2026-10-07 |
| [`03_historias_de_usuario.md`](../docs_contexto/03_historias_de_usuario.md) | Historias de usuario (US) y sus criterios de aceptación | 2026-10-07 |
| [`04_estado_actual_y_tareas.md`](../docs_contexto/04_estado_actual_y_tareas.md) | **Estado real del repositorio**: issues cerradas, pendientes, evidencia y plan por tarea | 2026-10-21 |

En la raíz del repositorio, [`../PROYECTO.md`](../PROYECTO.md) (enunciado del proyecto con un apéndice de estado) y [`../contexto_trabajo_final.md`](../contexto_trabajo_final.md) (contexto del trabajo final de la cátedra) completan el panorama.

---

## 3. Contratos vigentes

Los dos acuerdos entre servicios que **no deben cambiar** sin actualizar esta documentación y avisar al equipo:

1. **Esquema de claves Redis** → [`REDIS_SCHEMA.md`](REDIS_SCHEMA.md)
   Claves de administración (`admin:credentials`, `admin:initialized`, `reset_token:*`), de configuración (`config:settings`, `config:whitelist`), de conteo (`failed:<IP>`), de baneo (`ips:banned`, `ips:history`) y el stream de desbaneo.
2. **Desbaneo manual** → [`contrato-desbaneo.yaml`](contrato-desbaneo.yaml)
   Eventos `UNBAN` publicados por el Servicio 1 en `security:events:unban` y consumidos por el Servicio 2.

---

## 4. Convenciones

- **Mensajes de la API son contrato.** `backend-service1/app/core/constants.py` y `frontend-admin/src/constants/messages.js` deben coincidir **carácter a carácter**: el frontend muestra esas cadenas literalmente.
- **Nombres de claves Redis** se declaran en `backend-service1/app/core/keys.py` y se documentan en [`REDIS_SCHEMA.md`](REDIS_SCHEMA.md).
- **Secretos** (`REDIS_PASSWORD`, `JWT_SECRET`, credenciales SMTP) viven **solo** en `.env`, que está ignorado por git. `.env.example` es la plantilla y no lleva valores reales.
- **Documentos generados automáticamente** (como `EVALUACION.md`) no se editan a mano: se regeneran.
