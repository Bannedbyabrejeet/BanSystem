# Bannedbyabrejeet: Arquitectura del Sistema

## Visión General de la Arquitectura

La arquitectura de **Bannedbyabrejeet** se basa en una separación clara de responsabilidades entre dos microservicios desacoplados, comunicándose a través de una base de datos centralizada en Redis. El sistema combina una infraestructura dockerizada con una división funcional bien definida que permite desarrollar y escalar cada componente de forma independiente.

## División de Servicios

### Servicio 1: API Web y Gestión de Configuración (FastAPI)

Este servicio actúa como la interfaz administrativa y punto de entrada para la configuración del sistema. Sus responsabilidades principales son:

- **Autenticación y autorización** del administrador mediante credenciales almacenadas en Redis.
- **Gestión de parámetros de configuración**: Almacenar y servir los valores umbrales (intentos fallidos, tiempo de baneo, ventana de tolerancia/findtime) y la lista blanca de IPs.
- **Historial y estado de IPs**: Mantener el registro de IPs baneadas activamente y el historial de baneos pasados.
- **API de documentación Swagger**: Exponer la documentación interactiva de la API para ambos servicios.

**Endpoints y datos gestionados:**
- Autenticación de administrador (login, sesión, recuperación de contraseña)
- Configuración de parámetros de baneo (GET/PARÁMETROS)
- Historial de IPs registradas y baneadas
- Operaciones de whitelist (agregar/eliminar IPs, con excepción de 127.0.0.1)

### Servicio 2: Motor de Seguridad, Parser SSH e Integración UFW (Flask)

Este servicio es el núcleo algorítmico del sistema. Se ejecuta de forma continua monitoreando los logs del sistema y tomando decisiones automáticas basadas en la configuración del Servicio 1. Sus responsabilidades son:

- **Lector y parser de logs SSH**: Consumo continuo de los logs del sistema operativo (rutas como `/var/log/auth.log` o `/var/log/secure`) para detectar eventos de inicio de sesión.
- **Motor de reglas y evaluación**: Leer los parámetros de Redis y evaluar si una IP supera los umbrales configurados.
- **Integración con UFW**: Ejecutar comandos de firewall para bloquear/desbloquear IPs (`ufw deny from <IP>` y `ufw delete deny from <IP>`).
- **Gestión de timeouts**: Programar la expiración automática de baneos y actualizar el estado en Redis.

**Acciones ejecutadas:**
- Bloqueo automático de IP cuando se supera el límite de intentos en la ventana de tiempo configurada.
- Expiración automática de banes tras el tiempo configurado (timeout).
- Desbaneo manual solicitado desde el dashboard.
- Contrastación de IPs contra la lista blanca antes de aplicar bloqueos.

## Integración de los Dos Frontends

El sistema presenta dos interfaces de usuario distintas que consumen los servicios backend:

### Frontend A (Framework A - Módulo de Administración)
- Pantalla de login y registro inicial de administrador.
- Dashboard de configuración de parámetros de seguridad.
- Visualización de historial y estado actual de IPs.
- Gestión de lista blanca (whitelist) de IPs.
- Formulario de configuración de umbrales y timeouts.

### Frontend B (Framework B - Módulo Operativo)
- Visor de logs SSH formateados con diferenciación visual.
- Lista de IPs baneadas activas con opción de desbaneo manual.
- Consumo de endpoints de telemetría del Servicio 2 para datos en tiempo real.

### Estrategia de Integración

Dado que ambos frontends utilizan frameworks distintos, la integración se logra a través de:

1. **API Gateway / Proxy Inverso**: Enrutamiento de rutas por prefijo (ej. `/admin/*` para Frontend A y `/logs/*` para Frontend B) mediante Nginx o solución similar.
2. **Comunicación unificada con Backends**: Ambos frontends consumen sus respectivos servicios (Servicio 1 y Servicio 2) a través de sus endpoints REST, manteniendo una apariencia coherente para el usuario final a través de un diseño visual consistente.
3. **Estado compartido en Redis**: Ambos servicios leen y escriben en la misma instancia de Redis, garantizando que la configuración y el estado de IPs sean consistentes independientemente de qué frontend esté activo.

## Flujo de Datos Principal

1. El servicio SSH del sistema operativo genera logs de intentos de acceso (éxito y fallo).
2. El Servicio 2 (Flask) lee estos logs continuamente y los parsea.
3. El Servicio 2 consulta Redis para obtener los parámetros de configuración vigentes.
4. Si una IP supera el umbral, el Servicio 2 ejecuta comandos UFW para bloquearla.
5. El estado resultante (IP bloqueada, tiempo de expiración) se persiste en Redis.
6. Ambos frontends consultan Redis para visualizar el estado actual y la historia de eventos.