# Bannedbyabrejeet: Estado Actual y Tareas Pendientes

## Análisis Basado en las 10 Issues

Este documento detalla el estado actual del proyecto basándose en las 10 Issues definidas, identificando spikes arquitectónicos, tareas críticas y la división de trabajo entre los desarrolladores.

---

## Spikes Arquitectónicos (Arquitectural Spikes)

### Issue #1: Estrategia de Integración de Frontends (Spike Arquitectónico)
- **Estado:** Pendiente de resolución (primera tarea del Sprint)
- **Objetivo:** Definir la estrategia técnica para unificar vistas en dos frameworks distintos.
- **Decisión pendiente:** Arquitectura de Microfrontends (Module Federation o Single-SPA) vs. Proxy inverso (Nginx) con enrutamiento por rutas (/admin para Frontend A, /logs para Frontend B).
- **Resultado esperado:** Documento de diseño arquitectónico cargado en wiki/docs del repositorio.

### Issue #2: Definición de Comunicación Inter-Servicios (Spike Arquitectónico)
- **Estado:** Pendiente de resolución
- **Objetivo:** Establecer el canal de transferencia de datos para desbaneo manual entre Servicio 1 y Servicio 2.
- **Opciones en análisis:** 
  - Pub/Sub (Mensajería) de Redis
  - Llamadas HTTP REST directas entre servicios
- **Resultado esperado:** Diagrama de secuencia UML y documento YAML/JSON con el contrato provisional.

### Issue #3: Privilegios de Docker y Ruta de Logs SSH (Spike Técnico)
- **Estado:** Pendiente de resolución
- **Objetivo:** Garantizar acceso del sistema a recursos críticos del host operativo.
- **Preguntas clave:**
  - ¿Servicio 2 correrá en el Host o dentro de un contenedor Docker?
  - Si Docker: manejo de permisos CAP_NET_ADMIN y acceso al socket del host para UFW.
  - Ruta exacta de logs SSH (/var/log/auth.log, /var/log/secure, o journalctl).
- **Resultado esperado:** Script de Docker Compose draft validando montaje y permisos.

### Issue #4: Setup Inicial de Infraestructura y Base de Datos
- **Estado:** Tarea crítica / Pendiente de inicio
- **Objetivo:** Desplegar Redis dockerizado como almacenamiento centralizado.
- **Alcance incluye:** Ficheros Dockerfile y docker-compose.yml para Redis, configuración de persistencia (AOF/RDB).
- **Criterios de aceptación:**
  - Motor de BBDD (Redis) obligatoriamente Dockerizado.
  - Almacenamiento centralizado de credenciales, parámetros y registros de IPs.
  - Esquema en Redis acordado en conjunto para comunicación entre servicios.
- **Evidencia esperada:** Archivo docker-compose.yml funcional y captura de conexión mediante redis-cli.

---

## Tareas Críticas y División de Desarrollo

### Desarrollador 1: Infraestructura, API Web y Gestión de Configuración
**Enfoque:** Configurar la base del sistema (Redis), desarrollar el Servicio 1 (FastAPI) y la interfaz de autenticación/parámetros (Frontend A).

| ID | Tarea | Descripción | Dependencias |
|----|-------|-------------|--------------|
| **INFRA-01** | Setup de Redis en Docker | Configurar y levantar contenedor Docker con Redis | Issue #4 (Configuración inicial) |
| **BACK1-01** | Autenticación de Administrador | Validación inicio sesión, manejo de sesiones, almacenamiento seguro en Redis | Issue #4 |
| **BACK1-02** | API de Configuración de Baneos | Endpoints para consultar/actualizar intentos y tiempo de baneo | Issue #5 (Autenticación) |
| **BACK1-03** | API de Historial y Monitoreo de IPs | Rutas para obtener IPs registradas, baneadas e historial | Issue #5 |
| **FRONT-01** | Pantalla de Login | Vista de inicio de sesión previa a configuración | BACK1-01 |
| **FRONT-02** | Formulario de Parámetros de Baneo | Dashboard para modificar intentos y tiempo de baneo | BACK1-02 |
| **FRONT-03** | Vista de Historial y Estado de IPs | Componentes para visualizar IPs sancionadas y registro histórico | BACK1-03 |

### Desarrollador 2: Motor de Seguridad, Parser SSH e Integración UFW
**Enfoque:** Desarrollar el Servicio 2 principal (Flask), interacción con firewall y módulo de visualización (Frontend B).

| ID | Tarea | Descripción | Dependencias |
|----|-------|-------------|--------------|
| **BACK2-01** | Lector y Parser de Logs SSH | Módulo de lectura continua sobre logs SSH para detectar intentos fallidos/éxitos | Issue #3 (Rutas y permisos) |
| **BACK2-02** | Motor de Reglas y Evaluación | Conectar con Redis para leer parámetros y detectar IPs que superan umbrales | Issue #5 (Parámetros en Redis), Issue #2 (Contrato inter-servicios) |
| **BACK2-03** | Módulo de Bloqueo Automático (UFW) | Integración con UFW para ejecutar comandos de bloqueo sobre IPs infractoras | Issue #3 (Permisos Docker), Issue #8 (Motor detectando ataques) |
| **BACK2-04** | Módulo de Desbaneo Manual (UFW) | Lógica para recibir órdenes de desbloqueo, remover IP en UFW y eliminar timeout | Issue #2 (Contrato API), Issue #8 (Endpoints ready) |
| **FRONT-04** | Visor de Logs SSH Formateado | Interfaz para mostrar flujo de logs SSH de manera clara y estructurada | BACK2-01 (Parser operativo) |
| **FRONT-05** | Control de Desbaneo Manual | Botón/acción dentro de la interfaz para solicitar desbloqueo de IP específica | BACK2-04 (Desbaneo implementado) |

---

## Hitos de Coordinación Conjunta (Sync Points)

Estos son los puntos de sincronización críticos entre ambos desarrolladores:

1. **Definición de Esquema en Redis:** Acordar la estructura de claves y datos en Redis para comunicación transparente entre Servicio 1 y Servicio 2. (Dependencia cruzada entre Desarrollador 1 y 2)

2. **Definición de Contrato de API:** Establecer el formato de las peticiones para el desbaneo manual entre el Servicio 1 y el Servicio 2. Requiere definiciones de Issue #2.

3. **Integración Frontend:** Acordar la estrategia para unificar las vistas desarrolladas en frameworks distintos. Requiere resolución de Issue #1.

---

## Resumen del Estado del Proyecto

### Progreso Estimado
- **Infraestructura base:** Pendiente de setup (Issue #4). Es la tarea inicial que debe completarse antes de desarrollar cualquier otro componente.
- **Spikes arquitectónicos:** Issues #1, #2 y #3 deben resolverse al comienzo del proyecto para definir las bases técnicas.
- **Desarrollo backend:** Dividido entre Servicio 1 (autenticación y configuración) y Servicio 2 (motor de seguridad), con avances paralelos una vez resueltos los spikes.
- **Desarrollo frontend:** Dos módulos independientes (Administración y Operativo) que dependen del correcto funcionamiento de sus respectivos backends.

### Rutas Críticas
1. **Issue #4 → Issue #5 → Issue #6:** La infraestructura Redis debe levantarse antes de poder implementar autenticación y configuración.
2. **Issue #3:** Definir permisos Docker y rutas de logs es esencial antes del parser SSH (BACK2-01).
3. **Issue #1 y #2:** Los spikes arquitectónicos deben resolverse temprano para evitar reworks en la integración de frontends y comunicación inter-servicios.

### Recomendaciones para Siguientes Sprintes
1. Priorizar el levantamiento de la infraestructura Docker/Redis (Issue #4).
2. Resolver los spikes arquitectónicos (#1, #2, #3) en paralelo al setup inicial.
3. Establecer el esquema de Redis acordado antes de implementar BACK1-01 y BACK2-02.
4. Definir la estrategia de enrutamiento de frontends antes de comenzar el desarrollo UI significativo.