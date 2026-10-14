# Bannedbyabrejeet: Visión y Requisitos

## Introducción

**Bannedbyabrejeet** es un sistema de seguridad para el protocolo SSH inspirado en Fail2Ban. Su propósito es monitorear los logs de SSH en tiempo real, detectar intentos de acceso no autorizados (ataques de fuerza bruta) y aplicar bloqueos automáticos mediante el firewall UFW (Uncomplicated Firewall). El sistema permite a un administrador configurar los parámetros de seguridad a través de una interfaz web, visualizar el historial de IPs baneadas y gestionar excepciones (lista blanca).

## Objetivo General

Proporcionar una solución de seguridad perimetral para servidores SSH que automatice el bloqueo de IPs tras intentos fallidos de autenticación, ofreciendo al mismo tiempo una interfaz de gestión centralizada para configurar umbrales de baneo, tiempos de expiración y listas blancas, garantizando que solo personal autorizado pueda modificar estos parámetros.

## Requisitos Técnicos

### Infraestructura y Almacenamiento

- **Docker**: El proyecto debe estar totalmente dockerizado. El almacén de datos centralizado es **Redis**, que funcionará como base de datos en memoria para credenciales, parámetros de configuración y estado de IPs.

- **Redis**: Debe estar dockerizado obligatoriamente. Soporta estructuras de datos avanzadas como **Redis Streams** y permite configuración de **TTL** (Time-To-Live) en tokens de recuperación. El esquema en Redis debe estar acordado en conjunto entre ambos servicios para garantizar comunicación transparente.

### Backend (Dos Frameworks Distintos)

El backend se divide en dos servicios independientes:

1. **Servicio 1 - FastAPI**: Encargado del funcionamiento del servicio web, autenticación de administrador, gestión de configuración y almacenamiento en Redis. Este servicio expone la API REST y gestiona los endpoints para la interfaz administrativa.

2. **Servicio 2 - Flask**: Es el motor de seguridad principal. Su función es leer los logs de SSH, parsearlos, evaluar los parámetros de configuración y ejecutar acciones mediante UFW (bloqueo/desbloqueo de IPs).

- **Swagger**: El backend debe implementar **Swagger** (OpenAPI) para documentar exhaustivamente los endpoints desarrollados en ambos servicios (Servicio 1 y Servicio 2), sirviendo como fuente única de verdad para la comunicación entre equipos.

### Frontend (Dos Frameworks Distintos)

El frontend también está dividido en dos módulos que utilizan frameworks distintos:

1. **Frontend A**: Módulo de administración enfocado en autenticación, configuración de parámetros, historial de IPs y gestión de whitelist. Incluye la pantalla de login, formulario de parámetros de baneo y dashboard de control.

2. **Frontend B**: Módulo operativo enfocado en la visualización de logs SSH formateados y control de desbaneo. Incluye el visor de logs con diferenciación visual entre intentos exitosos y fallidos, y botones de desbaneo manual.

### Configuración de Parámetros (Definidos por el Administrador)

A través del dashboard web, el administrador podrá definir:

- **Cantidad de intentos fallidos previos al baneo**: Umbral máximo de fallos consecutivos antes de bloquear una IP.
- **Tiempo de baneo (en minutos)**: Duración de la restricción en UFW antes de la expiración automática.
- **Ventana de tolerancia / Findtime**: Ventana de tiempo durante la cual se acumulan los intentos fallidos permitidos (para evitar banear a usuarios legítimos con fallos espaciados).

## Actores del Sistema

- **Administrador de Sistemas / Operador de Seguridad**: Usuario autenticado que ajusta parámetros, audita logs, monitorea IPs y ejecuta desbaneos manuales.
- **Servicio SSH**: Actor pasivo que emite eventos de acceso (exitosos y fallidos).
- **Firewall UFW**: Ejecuta las acciones de bloqueo y desbloqueo definidas por el motor de seguridad.