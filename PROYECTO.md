# Proyecto: Bannedbyabrejeet

## Integrantes del equipo de desarrollo
* **Santiago Mulet**
* **Manuel Abrego**

## Introducción
Este es un sistema similar al software conocido como “Fail2Ban”. Será un software de seguridad para el protocolo SSH. Los parámetros de configuración del sistema de baneos se colocarán mediante un servicio web (el administrador deberá loguearse antes de poder configurar). El dashboard del administrador mostrará los parámetros de configuración. Además tendrá un historial de las IP’s baneadas y tendrá la posibilidad de quitar el timeout; también tendrá un apartado que mostrará los logs en un formato fácil de leer para el administrador.

### Requisitos impuestos por el profesor:
* Motor de BBDD Dockerizado (Redis)
* Backend con varios servicios (Dos frameworks distintos)
* Frontend (Dos frameworks distintos)
* El backend debe implementar Swagger

## Arquitectura del Sistema

### Frontend
*[Espacio para imagen de arquitectura Frontend]*
*[Espacio para imagen de arquitectura Frontend]*

En el frontend debe haber una ventana de login donde el administrador deberá loguearse para poder configurar previamente. Una vez logueado podrá configurar la cantidad de intentos previo al baneo y el tiempo de baneo (en minutos).
Además tendrá un historial de las IP’s que han sido baneadas anteriormente y las IP’s que están baneadas en el momento, debe existir la posibilidad de desbanear IP’s.

### Backend
*[Espacio para imagen de arquitectura Backend]*
*[Espacio para imagen de arquitectura Backend]*

El backend constará de dos servicios:
* **Servicio 1:** Este es el servicio encargado del funcionamiento del servicio web. Este servicio tendrá una BBDD Redis que manejará las credenciales del administrador, los parámetros de configuración del servicio de baneos (servicio 2), tendrá las ip’s baneadas y las ip’s registradas.
* **Servicio 2:** Este es el servicio principal. Este será el encargado de analizar los logs del protocolo SSH (Intentos fallidos y exitosos). Donde según los logs y teniendo en cuenta los parámetros de configuración determinados por el administrador en el dashboard web, realizará las acciones respectivas utilizando UFW (**Uncomplicated Firewall**), tales acciones son:
  * Luego de los intentos fallidos determinados por el admin será baneada la ip durante el tiempo configurado por el administrador.
  * Desbanear IP que el administrador elija en el dashboard.

---

## División de las Tareas

### Desarrollador 1: Infraestructura, API Web y Gestión de Configuración
**Enfoque:** Configurar la base del sistema (Redis), desarrollar el Servicio 1 (Framework Backend A) y la interfaz de autenticación/parámetros (Framework Frontend A).

#### Infraestructura y Base de Datos
* **[INFRA-01] Setup de Redis en Docker:** Configurar y levantar el contenedor Docker con Redis para servir como almacenamiento centralizado de credenciales, parámetros y registros de IPs.

#### Backend — Servicio 1 (Framework Backend A)
* **[BACK1-01] Autenticación de Administrador:** Implementar la validación del inicio de sesión del administrador, manejo de sesiones y almacenamiento seguro de credenciales en Redis.
* **[BACK1-02] API de Configuración de Baneos:** Crear los endpoints para consultar y actualizar el límite de intentos fallidos permitidos y el tiempo de baneo en minutos.
* **[BACK1-03] API de Historial y Monitoreo de IPs:** Diseñar las rutas para obtener el listado de IPs registradas, IPs baneadas actualmente e historial de baneos pasados almacenados en Redis.

#### Frontend — Módulo de Administración (Framework Frontend A)
* **[FRONT-01] Pantalla de Login:** Desarrollar la vista de inicio de sesión previa a la pantalla de configuración.
* **[FRONT-02] Formulario de Parámetros de Baneo:** Crear la interfaz del dashboard para modificar el número de intentos y el tiempo de baneo en minutos.
* **[FRONT-03] Vista de Historial y Estado de IPs:** Diseñar los componentes para visualizar las IPs actualmente sancionadas y el registro histórico.

### Desarrollador 2: Motor de Seguridad, Parser SSH e Integración UFW
**Enfoque:** Desarrollar el Servicio 2 principal de seguridad (Framework Backend B), la interacción con el sistema/firewall y el módulo de visualización de logs/desbaneo (Framework Frontend B).

#### Backend — Servicio 2 (Framework Backend B)
* **[BACK2-01] Lector y Parser de Logs SSH:** Implementar el módulo de lectura continua sobre los logs de SSH para detectar e identificar los intentos de acceso fallidos y exitosos.
* **[BACK2-02] Motor de Reglas y Evaluación:** Conectar con Redis para leer los parámetros guardados por el Servicio 1 e identificar qué IPs superan el umbral establecido.
* **[BACK2-03] Módulo de Bloqueo Automático (UFW):** Desarrollar la integración con UFW para ejecutar comandos de bloqueo sobre las IPs infractoras durante el tiempo configurado.
* **[BACK2-04] Módulo de Desbaneo Manual (UFW):** Implementar la lógica para recibir órdenes de desbloqueo, remover la IP en UFW y eliminar el timeout asociado.

#### Frontend — Módulo Operativo y Logs (Framework Frontend B)
* **[FRONT-04] Visor de Logs SSH Formateado:** Crear la interfaz responsiva para mostrar el flujo de logs SSH de manera clara y estructurada para el administrador.
* **[FRONT-05] Control de Desbaneo Manual:** Integrar la acción/botón dentro de la interfaz para solicitar el desbloqueo de una IP específica.

---

## Hitos de Coordinación Conjunta (Sync Points)
1. **Definición de Esquema en Redis:** Acordar juntos la estructura de claves y datos en Redis para la comunicación transparente entre ambos servicios.
2. **Definición de Contrato de API:** Establecer el formato de las peticiones para el desbaneo manual entre el Servicio 1 y el Servicio 2.
3. **Integración Frontend:** Acordar la estrategia para unificar las vistas desarrolladas en frameworks distintos.

---

## 1. Evaluación y Diagnóstico Técnico Preliminar
El proyecto "Bannedbyabrejeet" plantea el desarrollo de una solución de seguridad perimetral para el protocolo SSH inspirada en *Fail2Ban*. La arquitectura técnica combina:
1. **Infraestructura dockerizada:** Almacenamiento distribuido con Redis.
2. **Servicios Backend desacoplados:** Un servicio web/gestión de configuración y un motor principal de seguridad/parser de SSH.
3. **Múltiples Frameworks:** Restricción/requisito de utilizar dos frameworks distintos en el backend y dos en el frontend.
4. **Integración con Firewall Operativo:** Automatización de reglas mediante ufw (Uncomplicated Firewall).

### Actores Identificados
* **Administrador de Sistemas / Operador de Seguridad:** Usuario autenticado que ajusta parámetros, audita logs, monitorea IPs y ejecuta desbaneos manuales.
* **Servicio SSH / Sistema Operativo (Actor pasivo):** Fuente emisora de eventos de acceso (exitosos y fallidos).
* **Firewall UFW (Actor del sistema):** Componente ejecutor de las acciones de bloqueo y desbloqueo.

---

## 2. Historias de Usuario (User Stories - Backlog del Producto)
Siguiendo el estándar **INVEST** y la convención *Como / Quiero / Para*, se estructuran las historias de usuario organizadas por épicas.

### Épica 1: Autenticación y Gestión de Sesión
#### US-01: Autenticación de Administrador
* **Como:** Administrador de Sistemas,
* **Quiero:** Iniciar sesión en la plataforma web con mis credenciales,
* **Para:** Garantizar que únicamente el personal autorizado configure los parámetros de baneo y acceda a la información del sistema.
* **Criterios de Aceptación:**
  * Dado que no he iniciado sesión, al ingresar a la aplicación debo ser redirigido automáticamente a la vista de Login.
  * Dado que ingresé credenciales válidas registradas en Redis, el sistema me autentica y da acceso al Dashboard principal.
  * Dado que ingresé credenciales incorrectas, el sistema despliega un mensaje de error ("Credenciales inválidas") y deniega el acceso.
* **Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK1-01 / FRONT-01.

#### US-01.2: Set de credenciales
* **Cómo:** Administrador de sistemas,
* **Quiero:** Poder colocar un usuario y contraseña por primera vez,
* **Para:** Garantizar que un solo administrador sea el encargado de gestionar los parámetros de configuración del sistema.
* **Criterios de aceptación:**
  * Dado que no se a creado un usuario de Administrador antes, no habrá ningún usuario registrado para gestionar el sistema, debo ser redirigido a una pantalla de crear cuenta única.
  * Dado que cree el usuario administrador, el sistema me autentica y me redirige a la pagina de Log In.
* **Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK1-01 / FRONT-01.

#### US-01.3: Restaurar contraseña
* **Cómo:** Administrador de Sistemas,
* **Quiero:** Poder cambiar mi contraseña en caso de olvidarla,
* **Para:** Recuperar el acceso a la plataforma de forma autónoma y segura sin interrumpir la gestión del sistema ni depender de intervenciones manuales en la base de datos.
* **Criterios de aceptación:**
  * Dado que olvidé mi contraseña, al ingresar mi correo registrado en la opción "Olvidé mi contraseña", el sistema me envía un correo electrónico con un enlace que contiene un token temporal con tiempo de expiración.
  * Dado que accedí a un enlace de restauración válido, al ingresar y confirmar una nueva contraseña, el sistema actualiza la credencial en Redis y me redirige a la vista de Login con un mensaje de éxito ("Contraseña actualizada correctamente").
  * Dado que el enlace de restauración expiró, al intentar ingresar, el sistema despliega un mensaje de error ("El enlace de recuperación ha caducado o no es válido") y deniega el cambio.
* **Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK1-01 / FRONT-01.

### Épica 2: Configuración de Parámetros de Seguridad
#### US-02: Configuración del Umbral e Intervalo de Baneo
* **Como:** Administrador de Sistemas,
* **Quiero:** Definir el número máximo de intentos fallidos permitidos y la duración del baneo en minutos,
* **Para:** Ajustar la rigurosidad de la protección SSH según el nivel de amenaza percibido.
* **Criterios de Aceptación:**
  * El Dashboard debe presentar los valores vigentes de "Intentos fallidos previos al baneo" y "Tiempo de baneo (en minutos)".
  * Al actualizar los datos y presionar "Guardar", la configuración debe persistir en Redis mediante el Servicio 1.
  * El sistema debe validar que los valores ingresados sean enteros positivos estrictos mayores a cero.
  * El Servicio 2 debe tomar los nuevos parámetros de forma dinámica para las siguientes evaluaciones.
* **Prioridad:** Alta | **Estimación:** 3 Story Points | **Asignación:** BACK1-02 / FRONT-02.

### Épica 3: Monitoreo y Análisis de Logs SSH
#### US-03: Visualización Formateada de Logs SSH
* **Como:** Administrador de Sistemas,
* **Quiero:** Visualizar el flujo de logs del protocolo SSH en un formato estructurado y legible,
* **Para:** Auditar rápidamente los intentos de acceso exitosos y fallidos a los servidores.
* **Criterios de Aceptación:**
  * La vista debe mostrar los eventos de acceso SSH parseados por el Servicio 2.
  * Cada registro debe especificar: Fecha/Hora, IP de origen, usuario involucrado y resultado (Éxito / Fallo).
  * Debe existir diferenciación visual clara entre un intento exitoso y uno fallido.
* **Prioridad:** Media | **Estimación:** 8 Story Points | **Asignación:** BACK2-01 / FRONT-04.

### Épica 4: Baneo Automático y Gestión de Firewall
#### US-04: Bloqueo Automático de IP por Intentos Fallidos
* **Como:** Engine de Seguridad SSH,
* **Quiero:** Detectar automáticamente las IPs que superen el límite de intentos fallidos,
* **Para:** Ejecutar la regla de bloqueo en UFW y registrar la sanción en Redis.
* **Criterios de Aceptación:**
  * Cuando una IP acumule una cantidad de intentos fallidos de login SSH igual al parámetro configurado, el Servicio 2 ejecutará el comando de bloqueo en UFW.
  * La IP sancionada debe registrarse en Redis en la lista de IPs baneadas activas junto con la estampa de tiempo y duración.
* **Prioridad:** Alta | **Estimación:** 8 Story Points | **Asignación:** BACK2-02 / BACK2-03.

#### US-05: Expiración Automática del Baneo (Timeout)
* **Como:** Engine de Seguridad SSH,
* **Quiero:** Retirar la restricción en UFW una vez transcurrido el tiempo de baneo,
* **Para:** Restaurar el acceso normal a las direcciones IP cuya penalización haya caducado.
* **Criterios de Aceptación:**
  * Transcurrido el tiempo en minutos definido en la configuración, el Servicio 2 debe eliminar la regla correspondiente en UFW.
  * El estado de la IP en Redis debe actualizarse de "Baneada" a "Historial".
* **Prioridad:** Media | **Estimación:** 5 Story Points | **Asignación:** BACK2-03.

### Épica 5: Gestión de IPs y Desbaneo Manual
#### US-06: Consulta de Historial y Estado Actual de IPs
* **Como:** Administrador de Sistemas,
* **Quiero:** Consultar un listado con las IPs actualmente bloqueadas y el registro histórico,
* **Para:** Mantener trazabilidad de las direcciones IP sancionadas en el sistema.
* **Criterios de Aceptación:**
  * La vista debe clasificar las IPs en dos listas o estados: "Baneadas en el momento" e "Historial de baneadas anteriormente".
  * Se debe disponibilizar el origen de la IP, momento de bloqueo y tiempo asignado.
* **Prioridad:** Media | **Estimación:** 3 Story Points | **Asignación:** BACK1-03 / FRONT-03.

#### US-07: Desbaneo Manual de IP desde el Dashboard
* **Como:** Administrador de Sistemas,
* **Quiero:** Seleccionar una IP baneada desde la interfaz web y remover su bloqueo manualmente,
* **Para:** Eliminar el timeout y desbloquear de inmediato una IP bloqueada por error legítimo.
* **Criterios de Aceptación:**
  * Cada IP en la lista de baneos activos debe contar con la opción/botón "Desbanear".
  * Al ejecutar la acción, la orden se transfiere al Servicio 2 para remover la regla en UFW.
  * Se quita el timeout de la IP en Redis y su estado pasa a "Desbaneada manualmente".
* **Prioridad:** Alta | **Estimación:** 5 Story Points | **Asignación:** BACK2-04 / FRONT-05.

#### US-08: Gestión de Lista Blanca (Whitelist) de IPs
* **Como:** Administrador de Sistemas,
* **Quiero:** Configurar una lista de direcciones IP exentas de cualquier tipo de bloqueo (Whitelist),
* **Para:** Prevenir el auto-bloqueo accidental de mi propia red de gestión o de direcciones IP críticas para la operación del servidor.
* **Criterios de Aceptación:**
  * El Dashboard web (Frontend A) debe incluir un apartado para agregar y eliminar direcciones IP o subredes de una lista blanca.
  * Por defecto, la IP local (127.0.0.1) debe estar siempre incluida y no debe poder eliminarse de la lista blanca.
  * El motor de seguridad (Servicio 2) debe contrastar la IP de todo log fallido contra esta lista alojada en Redis; si hay coincidencia, ignorará el evento.
* **Prioridad:** Crítica | **Estimación:** 5 Story Points | **Épica Asociada:** Épica 2 (Configuración)

#### US-09: Configuración de Ventana Temporal de Baneos (Findtime)
* **Como:** Administrador de Sistemas,
* **Quiero:** Definir una ventana de tiempo máximo (ej. 10 minutos) durante la cual se acumulan los intentos fallidos permitidos,
* **Para:** Evitar banear permanentemente a usuarios legítimos que puedan equivocarse con sus contraseñas de forma muy espaciada (ej. 1 fallo por semana).
* **Criterios de Aceptación:**
  * El formulario de configuración (Frontend A) debe incorporar un nuevo campo numérico: "Ventana de tolerancia (en minutos)".
  * El parámetro debe almacenarse en Redis junto al resto de configuraciones a través del Servicio 1.
  * El motor de evaluación (Servicio 2) deberá descartar los intentos fallidos de una IP que hayan ocurrido fuera de esta ventana de tiempo al momento del último intento.
* **Prioridad:** Alta | **Estimación:** 8 Story Points | **Épica Asociada:** Épica 2 (Configuración)

#### US-10: Expiración Estricta de Tokens de Recuperación (TTL)
* **Como:** Sistema de Autenticación (Servicio 1),
* **Quiero:** Asignar un Time-To-Live (TTL) restrictivo a nivel de base de datos para los tokens de restauración de contraseña,
* **Para:** Garantizar su autodestrucción inmediata al cumplirse el plazo (ej. 15 minutos) y prevenir ventanas de oportunidad para ataques de secuestro de cuentas.
* **Criterios de Aceptación:**
  * Al generar un enlace de recuperación, el Servicio 1 debe persistir el token en Redis utilizando el comando nativo EXPIRE.
  * Cualquier intento de validar un token desde el Frontend A posterior al vencimiento del TTL debe recibir un código 404 del Servicio 1 por ausencia nativa de la llave.
* **Prioridad:** Alta | **Estimación:** 3 Story Points | **Épica Asociada:** Épica 1 (Autenticación)

---

## 3. Casos de Uso (Use Cases - Especificación Detallada)

### CU-01: Autenticación de Administrador
* **ID:** CU-01
* **Nombre:** Autenticación de Administrador
* **Actor Principal:** Administrador de Sistemas
* **Precondiciones:** El contenedor Docker de Redis está iniciado y accesible. El Servicio 1 está operativo.
* **Flujo Principal:**
  1. El Administrador accede a la URL del sistema web.
  2. La aplicación (Frontend A) detecta falta de sesión y muestra el formulario de Login.
  3. El Administrador ingresa usuario y contraseña y presiona "Iniciar Sesión".
  4. El Frontend A envía las credenciales vía POST al Servicio 1.
  5. El Servicio 1 valida las credenciales contra la base de datos Redis.
  6. El Servicio 1 confirma la autenticación y devuelve una cookie/token de sesión.
  7. El Frontend A redirige al Administrador al Dashboard de administración.
* **Flujos Alternativos / Excepciones:**
  * **5a. Credenciales inválidas:** El Servicio 1 responde código HTTP 401. El Frontend A muestra el mensaje "Usuario o contraseña incorrectos". El flujo retorna al paso 3.
  * **5b. Error de conexión a Redis:** El Servicio 1 responde código HTTP 500. El Frontend A informa "Servicio de autenticación no disponible".
* **Postcondiciones:** El Administrador obtiene una sesión activa para operar el sistema.

### CU-01.2: Set de Credenciales (Configuración Inicial del Administrador)
* **ID:** CU-01.2
* **Nombre:** Set de credenciales iniciales
* **Actor Principal:** Administrador de Sistemas
* **Precondiciones:** El contenedor Docker con Redis está disponible. Servicio 1 activo. No existe ningún usuario Administrador registrado.
* **Flujo Principal:**
  1. El Administrador accede a la URL de la aplicación web a través del Frontend A.
  2. El Frontend A verifica el estado de inicialización consultando al Servicio 1.
  3. El Servicio 1 verifica en Redis que no existen credenciales de administrador previas.
  4. Al confirmar, el sistema redirige automáticamente a la pantalla de creación de cuenta única.
  5. El Administrador coloca por primera vez su nombre de usuario y contraseña y presiona "Crear Cuenta".
  6. El Frontend A envía la solicitud de registro inicial al Servicio 1.
  7. El Servicio 1 (BACK1-01) almacena de forma segura las credenciales en Redis.
  8. El sistema autentica al usuario y lo redirige a la página de Log In.
* **Flujos Alternativos / Excepciones:**
  * **3a. Ya existe un usuario Administrador registrado:** El Servicio 1 deniega la creación inicial y redirige a la pantalla de Login estándar (CU-01).
  * **7a. Fallo en el almacenamiento en Redis:** Error HTTP 500 y el Frontend A despliega mensaje de error.
* **Postcondiciones:** Queda registrado un único Administrador en Redis.

### CU-01.3: Restaurar Contraseña
* **ID:** CU-01.3
* **Nombre:** Restaurar contraseña
* **Actor Principal:** Administrador de Sistemas
* **Precondiciones:** Contenedor de Redis accesible. Servicio 1 activo con servicio de correo. Existe un usuario registrado con correo.
* **Flujo Principal:**
  1. El Administrador accede a la vista de Login en el Frontend A y selecciona "Olvidé mi contraseña".
  2. El Frontend A solicita el correo electrónico registrado.
  3. El Administrador ingresa su correo y presiona "Enviar enlace de recuperación".
  4. El Frontend A envía la solicitud al Servicio 1.
  5. El Servicio 1 consulta en Redis la existencia del correo proporcionado.
  6. El Servicio 1 genera un token temporal con tiempo de expiración y envía un correo con el enlace.
  7. El Administrador hace clic en el enlace seguro recibido.
  8. El Frontend A valida con el Servicio 1 la vigencia y autenticidad del token.
  9. Al verificar que es válido, despliega el formulario para restablecer la contraseña.
  10. El Administrador ingresa y confirma su nueva contraseña.
  11. El Servicio 1 actualiza la credencial en Redis e invalida el token consumido.
  12. El sistema redirige a la vista de Login mostrando el mensaje de éxito.
* **Flujos Alternativos / Excepciones:**
  * **5a. Correo no registrado:** El Servicio 1 no genera ningún token ni envía correo.
  * **8a. Enlace caducado o inválido:** El Servicio 1 deniega el cambio y despliega el mensaje de error "El enlace de recuperación ha caducado...".
* **Postcondiciones:** La nueva contraseña se actualiza y el token temporal queda inhabilitado.

### CU-02: Configuración de Parámetros de Baneo
* **ID:** CU-02
* **Nombre:** Configuración de Parámetros de Baneo
* **Actor Principal:** Administrador de Sistemas
* **Precondiciones:** El Administrador cuenta con sesión válida abierta.
* **Flujo Principal:**
  1. El Administrador navega a la sección de configuración del Dashboard.
  2. El Frontend A solicita los parámetros actuales mediante GET al Servicio 1.
  3. El Servicio 1 lee las claves de configuración de Redis y responde los valores.
  4. El Administrador modifica la "Cantidad de intentos fallidos" y/o el "Tiempo de baneo (minutos)".
  5. El Administrador presiona el botón "Guardar Configuración".
  6. El Frontend A envía los nuevos valores al Servicio 1.
  7. El Servicio 1 sobrescribe los valores en Redis.
  8. El Frontend A notifica "Parámetros actualizados con éxito".
* **Flujos Alternativos:**
  * **6a. Entrada inválida:** Si se ingresan valores no numéricos o <= 0, el Frontend A bloquea la solicitud.
* **Postcondiciones:** Los nuevos parámetros quedan registrados en Redis.

### CU-03: Bloqueo Automático de IP mediante UFW
* **ID:** CU-03
* **Nombre:** Bloqueo Automático de IP mediante UFW
* **Actor Principal:** Servicio 2 (Motor de Seguridad / Parser SSH)
* **Precondiciones:** Servicio 2 en ejecución continua con privilegios UFW.
* **Flujo Principal:**
  1. El Servicio 2 lee un evento de intento fallido SSH en los logs.
  2. El Servicio 2 consulta en Redis los parámetros vigentes.
  3. El Servicio 2 incrementa el registro de intentos fallidos acumulados para la IP origen.
  4. El Servicio 2 verifica que los intentos superaron el parámetro permitido.
  5. El Servicio 2 ejecuta el comando UFW (ufw deny from <IP> to any port 22).
  6. El Servicio 2 registra la IP en Redis con estado "Baneada", timestamp de inicio y tiempo de expiración.
* **Flujos Alternativos:**
  * **4a. Intentos por debajo del umbral:** La IP no se bloquea; se actualiza el contador.
  * **5a. Error en comando UFW:** El Servicio 2 emite alerta crítica.
* **Postcondiciones:** La IP infractora queda bloqueada en UFW y persistida en Redis.

### CU-04: Desbaneo Manual de IP
* **ID:** CU-04
* **Nombre:** Desbaneo Manual de IP
* **Actor Principal:** Administrador de Sistemas
* **Precondiciones:** Administrador con sesión. IP bloqueada en UFW y Redis.
* **Flujo Principal:**
  1. El Administrador ingresa a la vista de historial/estado de IPs.
  2. El Administrador ubica la IP y presiona "Desbanear".
  3. El Frontend realiza la petición.
  4. El Servicio 1/2 recibe la instrucción y ejecuta remoción en UFW (ufw delete deny from <IP>).
  5. El Servicio 2 remueve el timeout activo en Redis y actualiza el estado a "Desbaneada manualmente".
  6. La interfaz actualiza el listado.
* **Postcondiciones:** La IP recupera acceso SSH.

### CU-05: Visualización de Logs SSH Formateados
* **ID:** CU-05
* **Nombre:** Visualización de Logs SSH Formateados
* **Actor Principal:** Administrador de Sistemas
* **Precondiciones:** Administrador autenticado.
* **Flujo Principal:**
  1. El Administrador selecciona "Logs SSH".
  2. El Frontend B consulta los logs procesados al Servicio 2.
  3. El Servicio 2 extrae las entradas del parser y las retorna estructuradas.
  4. El Frontend B presenta los datos formateados en una tabla interactiva.
* **Postcondiciones:** Visualización de actividad SSH estructurada.

### CU-06: Agregar y Eliminar IP en Lista Blanca
* **ID:** CU-06
* **Nombre:** Agregar y Eliminar IP en Lista Blanca
* **Actor Principal:** Administrador de Sistemas
* **Precondiciones:** Sesión iniciada. Servicio 1 y Redis operativos.
* **Flujo Principal:**
  1. El Administrador ingresa al módulo de "Whitelist".
  2. El sistema muestra el listado actual desde Redis.
  3. El Administrador ingresa una IP y presiona "Proteger IP".
  4. El Frontend A valida el formato y envía al Servicio 1.
  5. El Servicio 1 anexa la IP a la Whitelist en Redis.
  6. La interfaz confirma la adición exitosa.
* **Excepciones:**
  * **3a. Formato inválido:** Frontend rechaza.
  * **5a. Borrar IP crítica:** Backend rechaza eliminar 127.0.0.1 (HTTP 403).
* **Postcondiciones:** IP exenta de evaluaciones de bloqueo.

### CU-07: Evaluación Dinámica con Ventana Temporal (Findtime)
* **ID:** CU-07
* **Nombre:** Evaluación Dinámica con Ventana Temporal (Findtime)
* **Actor Principal:** Servicio 2
* **Precondiciones:** Servicio 2 en ejecución. Parámetro de ventana de tolerancia definido en Redis.
* **Flujo Principal:**
  1. El Servicio 2 intercepta un fallo de login SSH para la IP [X].
  2. Consulta el contador de errores de la IP [X] y la marca de tiempo del primer fallo.
  3. Calcula la diferencia de tiempo entre el fallo actual y el primer fallo.
  4. Si la diferencia es menor a la "Ventana de tolerancia", incrementa el contador.
  5. Si el contador alcanza el límite configurado, ejecuta el CU-03.
* **Excepciones:**
  * **4a. Tiempo expirado:** Si la diferencia es mayor a la ventana, reinicia el registro dejando el contador en 1 y actualizando la marca de tiempo.
* **Postcondiciones:** Monitoreo coherente enfocado en ataques de fuerza bruta rápidos.

