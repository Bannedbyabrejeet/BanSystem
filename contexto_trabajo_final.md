Contexto del Trabajo Final - Programación 3
Modalidad de Trabajo

    Individual o Equipo de 2 integrantes
    En caso de equipo de 2: los objetivos serán más complejos (mayor alcance, más funcionalidades, mayor profundidad técnica)

Stack Tecnológico Obligatorio
1. Base de Datos (Dockerizada)

    Motor de base de datos relacional (PostgreSQL, MySQL, MariaDB) o no relacional (MongoDB, Redis, Cassandra)
    Ejecución en contenedor Docker con persistencia de datos (volúmenes)

2. Backend - Mínimo 1 Servicio

    Al menos un servicio de backend funcional que exponga una API (REST, GraphQL, gRPC)
    CRUD completo sobre al menos una entidad, autenticación/autorización básica, validación de datos

3. Frontend - Mínimo 1 Aplicación

    Al menos una aplicación frontend funcional que consuma la API del backend
    Listado, creación, edición y eliminación de recursos; manejo de estado; routing; feedback visual

4. Diversidad de Frameworks (Requisito Central)

    Backend: El mismo servicio implementado con al menos 2 frameworks distintos (misma API, mismos endpoints, misma lógica)
    Frontend: La misma aplicación implementada con al menos 2 frameworks distintos (mismas vistas, mismo flujo, mismo consumo de API)

Perfil de los Alumnos

    5to año de secundaria con título técnico en informática
    Formación previa: Fundamentos de programación y Programación Orientada a Objetos
    Primeros pasos en: Programación Web y Microservicios

Proceso de Trabajo
Paso 1: Definición Inicial del Objetivo Principal

    Especificar a grandes rasgos cuál será el objetivo principal del proyecto (qué problema resuelve, qué hace la aplicación)
    Aprobación del profesor requerida antes de avanzar

Paso 2: Determinación de Límites, Alcances y Objetivos

    Una vez aprobado el objetivo principal, definir en detalle:
        Límites del sistema (qué está dentro y qué fuera)
        Alcances funcionales y no funcionales
        Objetivos específicos y medibles (funcionalidades, métricas de calidad, criterios de aceptación)
    Todo lo anterior debe quedar documentado en un archivo Markdown (PROYECTO.md o similar) dentro del repositorio de trabajo, sirviendo como contrato y guía durante todo el desarrollo.

Paso 3: Diseño de las Issues del Repositorio

    Una vez aprobado el objetivo principal y documentados los límites, alcances y objetivos, se deberán diseñar las issues que representen las tareas necesarias para construir el proyecto.
    Cada issue debe estar relacionada con uno o más objetivos del proyecto y describir, como mínimo:
        Título y descripción clara de la tarea
        Objetivo de la issue y problema que resuelve
        Alcance de los cambios incluidos y excluidos
        Criterios de aceptación verificables
        Dependencias, si requiere que otra issue se complete previamente
        Evidencias o pruebas que deberán presentarse al finalizarla
    Las issues deberán organizarse en un orden lógico de ejecución, teniendo en cuenta sus dependencias y prioridades.
    El diseño de las issues debe quedar registrado en el repositorio, utilizando la herramienta de gestión del repositorio o archivos Markdown cuando corresponda.

Paso 4: Flujo Obligatorio de Ramas, Commits y Pull Requests

    El profesor deberá ser agregado como colaborador en todos los repositorios del proyecto antes de comenzar el trabajo.
    Está prohibido realizar push directamente sobre la rama main bajo cualquier circunstancia.
    Todo trabajo deberá realizarse sobre una rama propia, creada a partir de main y asociada a la issue correspondiente.
    Todos los commits deberán seguir la especificación de Conventional Commits, utilizando el formato tipo(alcance): descripción.
    Entre los tipos de commit permitidos se encuentran feat para nuevas funcionalidades, fix para correcciones, docs para documentación, refactor para cambios internos y test para pruebas.
    Los mensajes de commit deberán ser claros, concisos y describir el cambio realizado. Por ejemplo: feat(auth): agregar autenticación con JWT.
    Una vez finalizado el trabajo de una issue, se deberá publicar la rama y crear un Pull Request (PR) hacia main.
    El PR deberá incluir la referencia a la issue, una descripción de los cambios realizados y las evidencias de cumplimiento de los criterios de aceptación.
    Cada PR deberá ser revisado y aprobado explícitamente por el profesor antes de poder incorporar sus cambios a main.
    La incorporación de cambios a main solo podrá realizarse mediante un PR aprobado por el profesor, nunca mediante un push directo.

Paso 5: Presentación, Aprobación y Ejecución de las Issues

    Antes de comenzar la implementación, cada issue deberá ser presentada al profesor.
    Durante la presentación, el alumno o equipo deberá demostrar que comprende:
        El problema que la issue resuelve
        La estrategia de implementación propuesta
        Los cambios que deberán realizarse en el sistema
        La forma en que se comprobará el cumplimiento de los criterios de aceptación
    Una issue solo podrá pasar a la etapa de ejecución después de que su diseño sea aprobado.
    Al finalizar la implementación, se deberá presentar la resolución de la issue junto con las evidencias correspondientes y demostrar que se cumplen sus criterios de aceptación.
    La siguiente issue solo podrá comenzar a ejecutarse una vez que la resolución de la issue anterior haya sido presentada y aprobada, su PR haya sido aprobado por el profesor y sus cambios hayan sido integrados en main, respetando el orden de trabajo definido.
    Si el diseño o la resolución de una issue no es aprobado, deberá corregirse y volver a presentarse antes de avanzar con la siguiente.

Aclaraciones y Ejemplos
Límites del Sistema

Definen qué pertenece al proyecto y qué no. Ayudan a evitar el "scope creep" (crecimiento descontrolado del alcance).

    Ejemplo:

        ✅ Dentro: Gestión de tareas, usuarios, autenticación, API REST, frontend web
        ❌ Fuera: App móvil nativa, notificaciones push, chat en tiempo real, integración con calendarios externos, panel de analytics avanzado

Alcances Funcionales

Qué hace el sistema — funcionalidades, casos de uso, reglas de negocio. Responden a "¿qué debe poder hacer el usuario?".

    Ejemplos:

        CRUD de tareas (crear, listar, editar, eliminar, marcar completada)
        Registro e inicio de sesión con JWT
        Filtros por estado, prioridad, fecha
        Asignación de tareas a usuarios
        Validación: título obligatorio, fecha futura, prioridad en {baja, media, alta}

Alcances No Funcionales

Cómo se comporta el sistema — calidad, restricciones técnicas, atributos de arquitectura. Responden a "¿cómo debe ser el sistema?".

    Ejemplos:

        Performance: API responde < 200ms (P95) bajo carga normal
        Disponibilidad: 99.9% uptime (excluyendo mantenimiento programado)
        Seguridad: Contraseñas hasheadas (bcrypt), HTTPS obligatorio, rate limiting en auth
        Escalabilidad: Stateless services, BD con connection pooling, horizontal scaling ready
        Mantenibilidad: Cobertura tests ≥ 80%, ESLint/Prettier, documentación OpenAPI actualizada
        Usabilidad: Responsive (mobile-first), WCAG AA básico, feedback visual < 100ms
        Desplegabilidad: docker-compose up levanta todo en < 2 min, health checks en todos los servicios

Objetivos Específicos y Medibles

Metas concretas que permiten saber si el proyecto se completó con éxito. Deben ser SMART (Específicos, Medibles, Alcanzables, Relevantes, Temporales).

    Ejemplos:

        Implementar 2 backends (Express + FastAPI) con paridad 100% de endpoints
        Implementar 2 frontends (React + Vue) con mismas 5 vistas y mismo flujo
        Alcanzar ≥ 85% cobertura de tests en ambos backends y frontends
        Documentar API con OpenAPI 3.0 y generar cliente TypeScript automático
        Desplegar en staging con GitHub Actions después de cada PR aprobado e integrado en main
        Presentar comparativa de métricas (latencia, bundle size, DX) en informe final

