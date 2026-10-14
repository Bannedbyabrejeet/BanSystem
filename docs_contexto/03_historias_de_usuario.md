# Bannedbyabrejeet: Historias de Usuario y Épicas

## Resumen Ejecutivo

El proyecto organiza las historias de usuario por **épicas**, siguiendo el estándar INVEST. A continuación se presenta un resumen de las épicas y sus criterios de aceptación principales, categorizadas por áreas de funcionalidad.

---

## Épica 1: Autenticación y Gestión de Sesión

Objetivo: Garantizar que únicamente el personal autorizado configure los parámetros de baneo y acceda a la información del sistema.

### US-01: Autenticación de Administrador
- **Como** Administrador de Sistemas
- **Quiero** Iniciar sesión en la plataforma web con mis credenciales
- **Para** Garantizar que únicamente el personal autorizado configure los parámetros de baneo y acceda a la información del sistema.

**Criterios de aceptación:**
- Dado que no he iniciado sesión, al ingresar a la aplicación debo ser redirigido automáticamente a la vista de Login.
- Dado que ingresé credenciales válidas registradas en Redis, el sistema me autentica y da acceso al Dashboard principal.
- Dado que ingresé credenciales incorrectas, el sistema despliega un mensaje de error ("Credenciales inválidas") y deniega el acceso.

**Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK1-01 / FRONT-01

### US-01.2: Set de credenciales (Configuración Inicial)
- **Cómo** Administrador de sistemas
- **Quiero** Poder colocar un usuario y contraseña por primera vez
- **Para** Garantizar que un solo administrador sea el encargado de gestionar los parámetros de configuración del sistema.

**Criterios de aceptación:**
- Dado que no se ha creado un usuario de Administrador antes, no habrá ningún usuario registrado para gestionar el sistema, debo ser redirigido a una pantalla de crear cuenta única.
- Dado que cree el usuario administrador, el sistema me autentica y me redirige a la página de Log In.

**Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK1-01 / FRONT-01

### US-01.3: Restaurar contraseña
- **Cómo** Administrador de Sistemas
- **Quiero** Poder cambiar mi contraseña en caso de olvidarla
- **Para** Recuperar el acceso a la plataforma de forma autónoma y segura sin interrumpir la gestión del sistema.

**Criterios de aceptación:**
- Dado que olvidé mi contraseña, al ingresar mi correo registrado en la opción "Olvidé mi contraseña", el sistema me envía un correo electrónico con un enlace que contiene un token temporal con tiempo de expiración.
- Dado que accedí a un enlace de restauración válido, al ingresar y confirmar una nueva contraseña, el sistema actualiza la credencial en Redis y me redirige a la vista de Login con un mensaje de éxito.
- Dado que el enlace de recuperación expiró, al intentar ingresar, el sistema despliega un mensaje de error y deniega el cambio.

**Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK1-01 / FRONT-01

---

## Épica 2: Configuración de Parámetros de Seguridad

Objetivo: Permitir al administrador ajustar la rigurosidad de la protección SSH según el nivel de amenaza percibido.

### US-02: Configuración del Umbral e Intervalo de Baneo
- **Como** Administrador de Sistemas
- **Quiero** Definir el número máximo de intentos fallidos permitidos y la duración del baneo en minutos
- **Para** Ajustar la rigurosidad de la protección SSH según el nivel de amenaza percibida.

**Criterios de aceptación:**
- El Dashboard debe presentar los valores vigentes de "Intentos fallidos previos al baneo" y "Tiempo de baneo (en minutos)".
- Al actualizar los datos y presionar "Guardar", la configuración debe persistir en Redis mediante el Servicio 1.
- El sistema debe validar que los valores ingresados sean enteros positivos estrictos mayores a cero.
- El Servicio 2 debe tomar los nuevos parámetros de forma dinámica para las siguientes evaluaciones.

**Prioridad:** Alta | **Estimación:** 3 Story Points | **Asignación:** BACK1-02 / FRONT-02

### US-09: Configuración de Ventana Temporal de Baneos (Findtime)
- **Como** Administrador de Sistemas
- **Quiero** Definir una ventana de tiempo máximo (ej. 10 minutos) durante la cual se acumulan los intentos fallidos permitidos
- **Para** Evitar banear permanentemente a usuarios legítimos que puedan equivocerse con sus contraseñas de forma muy espaciada.

**Criterios de aceptación:**
- El formulario de configuración (Frontend A) debe incorporar un nuevo campo numérico: "Ventana de tolerancia (en minutos)".
- El parámetro debe almacenarse en Redis junto al resto de configuraciones a través del Servicio 1.
- El motor de evaluación (Servicio 2) deberá descartar los intentos fallidos de una IP que hayan ocurrido fuera de esta ventana de tiempo al momento del último intento.

**Prioridad:** Alta | **Estimación:** 8 Story Points | **Épica Asociada:** Épica 2

### US-08: Gestión de Lista Blanca (Whitelist) de IPs
- **Como** Administrador de Sistemas
- **Quiero** Configurar una lista de direcciones IP exentas de cualquier tipo de bloqueo (Whitelist)
- **Para** Prevenir el auto-bloqueo accidental de mi propia red de gestión o de direcciones IP críticas.

**Criterios de aceptación:**
- El Dashboard web (Frontend A) debe incluir un apartado para agregar y eliminar direcciones IP o subredes de una lista blanca.
- Por defecto, la IP local (127.0.0.1) debe estar siempre incluida y no debe poder eliminarse de la lista blanca.
- El motor de seguridad (Servicio 2) debe contrastar la IP de todo log fallido contra esta lista alojada en Redis; si hay coincidencia, ignorará el evento.

**Prioridad:** Crítica | **Estimación:** 5 Story Points | **Épica Asociada:** Épica 2 (Configuración)

---

## Épica 3: Monitoreo y Análisis de Logs SSH

Objetivo: Proporcionar al administrador visibilidad completa sobre la actividad SSH del servidor.

### US-03: Visualización Formateada de Logs SSH
- **Como** Administrador de Sistemas
- **Quiero** Visualizar el flujo de logs del protocolo SSH en un formato estructurado y legible
- **Para** Auditar rápidamente los intentos de acceso exitosos y fallidos a los servidores.

**Criterios de aceptación:**
- La vista debe mostrar los eventos de acceso SSH parseados por el Servicio 2.
- Cada registro debe especificar: Fecha/Hora, IP de origen, usuario involucrado y resultado (Éxito / Fallo).
- Debe existir diferenciación visual clara entre un intento exitoso y uno fallido.

**Prioridad:** Media | **Estimación:** 8 Story Points | **Asignación:** BACK2-01 / FRONT-04

---

## Épica 4: Baneo Automático y Gestión de Firewall

Objetivo: Detectar y bloquear automáticamente IPs que ataquen el servicio SSH.

### US-04: Bloqueo Automático de IP por Intentos Fallidos
- **Como** Engine de Seguridad SSH
- **Quiero** Detectar automáticamente las IPs que superen el límite de intentos fallidos
- **Para** Ejecutar la regla de bloqueo en UFW y registrar la sanción en Redis.

**Criterios de aceptación:**
- Cuando una IP acumule una cantidad de intentos fallidos de login SSH igual al parámetro configurado, el Servicio 2 ejecutará el comando de bloqueo en UFW.
- La IP sancionada debe registrarse en Redis en la lista de IPs baneadas activas junto con la estampa de tiempo y duración.

**Prioridad:** Alta | **Estimación:** 8 Story Points | **Asignación:** BACK2-02 / BACK2-03

### US-05: Expiración Automática del Baneo (Timeout)
- **Como** Engine de Seguridad SSH
- **Quiero** Retirar la restricción en UFW una vez transcurrido el tiempo de baneo
- **Para** Restaurar el acceso normal a las direcciones IP cuya penalización haya caducado.

**Criterios de aceptación:**
- Transcurrido el tiempo en minutos definido en la configuración, el Servicio 2 debe eliminar la regla correspondiente en UFW.
- El estado de la IP en Redis debe actualizarse de "Baneada" a "Historial".

**Prioridad:** Media | **Estimación:** 5 Story Points | **Asignación:** BACK2-03

---

## Épica 5: Gestión de IPs y Desbaneo Manual

Objetivo: Permitir al administrador gestionar manually los bloqueos cuando sea necesario.

### US-06: Consulta de Historial y Estado Actual de IPs
- **Como** Administrador de Sistemas
- **Quiero** Consultar un listado con las IPs actualmente bloqueadas y el registro histórico
- **Para** Mantener trazabilidad de las direcciones IP sancionadas en el sistema.

**Criterios de aceptación:**
- La vista debe clasificar las IPs en dos listas o estados: "Baneadas en el momento" e "Historial de baneadas anteriormente".
- Se debe disponibilizar el origen de la IP, momento de bloqueo y tiempo asignado.

**Prioridad:** Media | **Estimación:** 3 Story Points | **Asignación:** BACK1-03 / FRONT-03

### US-07: Desbaneo Manual de IP desde el Dashboard
- **Como** Administrador de Sistemas
- **Quiero** Seleccionar una IP baneada desde la interfaz web y remover su bloqueo manualmente
- **Para** Eliminar el timeout y desbloquear de inmediato una IP bloqueada por error legítimo.

**Criterios de aceptación:**
- Cada IP en la lista de baneos activos debe contar con la opción/botón "Desbanear".
- Al ejecutar la acción, la orden se transfiere al Servicio 2 para remover la regla en UFW.
- Se quita el timeout de la IP en Redis y su estado pasa a "Desbaneada manualmente".
- La interfaz actualiza el listado, moviendo la IP del grupo de activas al historial pasado.

**Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK2-04 / FRONT-05

---

## Épica 2 (adicional): US-10 - Expiración Estricta de Tokens de Recuperación (TTL)

- **Como** Sistema de Autenticación (Servicio 1)
- **Quiero** Asignar un Time-To-Live (TTL) restrictivo a nivel de base de datos para los tokens de restauración de contraseña
- **Para** Garantizar su autodestrucción inmediata al cumplirse el plazo y prevenir ventanas de oportunidad para ataques.

**Criterios de aceptación:**
- Al generar un enlace de recuperación, el Servicio 1 debe persistir el token en Redis utilizando el comando nativo EXPIRE.
- Cualquier intento de validar un token desde el Frontend A posterior al vencimiento del TTL debe recibir un código 404 del Servicio 1 por ausencia nativa de la llave.

**Prioridad:** Alta | **Estimación:** 3 Story Points | **Épica Asociada:** Épica 1 (Autenticación)