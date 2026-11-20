<!-- evaluacion:inicio -->
# Evaluación — Bannedbyabrejeet/BanSystem

> Documento **generado automáticamente** por la cátedra de Programación III (RepoSense + análisis de calidad + constancia). **No editar a mano**: se regenera en cada evaluación.
> Rama evaluada: `main`. Análisis **heurístico** (regex + métricas): es una criba para orientar la revisión, **no una nota**.
> Generado: 2026-11-20.

## 1. Veredicto

| Aspecto | Resultado |
|---|---|
| Tipo de proyecto | app |
| Índice de calidad de servicios | **27/100** (mínimo 50) |
| Criterios cumplidos | **10/16** |
| Aprobado (semáforo) | **NO** |
| Código (LOC) | 7,633 |
| Archivos de código | 84 |
| Tests (archivos) | 18 |
| Cobertura de líneas | 72.2% (mínimo 80%) |
| Capas detectadas | presentacion, logica, datos, vistas, servicios, estado |
| Pushes directos a `main` (sin PR) | 1 |

> **Pushes directos:** se detectaron **1** commit(s) a `main` que no pasaron por un Pull Request. El flujo esperado es **rama → PR → revisión → merge**; el PR se aprueba con el mensaje `Aprobado`. Evitá pushear directo a `main`: la ruleset lo bloquea y el commit directo queda auditado.

> **Aprobado** exige las compuertas críticas (**SEC**, **SQL**, **capas**, **índice ≥ 50** y **cobertura ≥ 80 %** cuando aplica) y tolera hasta **3 criterios en rojo** (12/15). No es una nota: sirve para ordenar y priorizar la revisión.

## 2. Autoría (RepoSense)

| Autor | Commits | Código (LOC) | Tests (LOC) | Docs (LOC) | Días activos | % del código |
|---|---:|---:|---:|---:|---:|---:|
| SantiMulet | 23 | 10,401 | 2,880 | 4,067 | 14 | 100% |
| manu_abrego_1913 | 5 | 0 | 0 | 253 | 5 | 0% |

> _El LOC de autoría lo calcula RepoSense sobre el historial y puede diferir del LOC de código del análisis de calidad (que mira solo el estado de `main`)._

> **Reparto del trabajo:** SantiMulet concentra el 100% de las líneas de código. Un reparto muy desigual suele indicar que la integración no fue realmente en equipo; vale la pena reconstruir cómo se coordinó.

## 3. Constancia (IC) — todas las ramas

> El IC mide **cuándo** se trabajó (sesiones por semana, pausas y recencia), no cuánto ni con qué calidad. Se calcula sobre **todas las ramas** de todos los repositorios del alumno, no sólo `main`.

| Alumno | Sesiones | Cumplimiento | Pausa | Recencia | IC | Nivel | Para subir de nivel |
|---|--:|--:|--:|--:|--:|--|--|
| SantiMulet | 11 | 39% | 23 d | 36% | **30** | No aprueba | Cumplimiento 39% (mín. 50%); Recencia 36% (mín. 50%) |
| manu_abrego_1913 | 6 | 21% | 61 d | 36% | **19** | No aprueba | Cumplimiento 21% (mín. 50%); Recencia 36% (mín. 50%) |

> Para aprobar el IC: **2 sesiones por semana** sostenidas, sin pausas mayores a **10 días** y con actividad en las **últimas 2 semanas**. Se excluyen merges, bots y al docente. Zona horaria UTC-3.

## 4. Aspectos evaluados

Cada aspecto indica **qué mide**, **por qué importa** y **tu resultado**. Cuando el resultado está en rojo, se agregan preguntas para **investigar la causa** (no hay recetas: entender el porqué es parte de la evaluación).

### 1. Índice de calidad de servicios (indice) — A REVISAR

- **Qué mide:** Un resumen numérico (0-100) que combina todas las señales y métricas del análisis, con topes duros por duplicación.
- **Por qué importa:** Ordena y prioriza la revisión: un índice bajo indica varias señales que conviene mirar juntas.
- **Tu resultado:** índice **27/100** _(mínimo 50)_
- **Para investigar la causa:**
    - ¿En qué momento del proyecto se concentraron los problemas (arranque, integración de partes, cierre)?
    - ¿El índice bajó por muchas señales chicas o por una o dos graves?
    - ¿Se revisó el código integrado después de unir el trabajo de cada integrante?

### 2. Duplicación (DRY) (duplicacion) — OK

- **Qué mide:** Porcentaje de bloques de código repetidos (similitud) en el repositorio.
- **Por qué importa:** Cada copia se mantiene por separado: un arreglo hay que repetirlo y los defectos se multiplican.
- **Tu resultado:** **4.9%** de duplicación _(máximo 15%)_

### 3. Secretos hardcodeados (SEC) — OK

- **Qué mide:** Credenciales, tokens o claves escritos directamente en el código en vez de leerse de variables de entorno.
- **Por qué importa:** Un secreto en el repositorio queda expuesto en el historial aunque luego se borre, y compromete al servicio y a sus usuarios.
- **Tu resultado:** **0** secreto(s) hardcodeado(s) _(máximo 0)_

### 4. Consultas SQL por concatenación (SQL) — OK

- **Qué mide:** Consultas SQL armadas concatenando o interpolando valores en vez de usar parámetros.
- **Por qué importa:** Es la puerta clásica a inyección: un valor que llega de afuera puede cambiar la consulta.
- **Tu resultado:** **0** consulta(s) SQL por concatenación _(máximo 0)_

### 5. Separación en capas (capas) — OK

- **Qué mide:** Si el código está separado en capas reconocibles (backend: presentación / lógica / datos; frontend: vistas / servicios / estado).
- **Por qué importa:** Sin separación, cada archivo hace de todo y cualquier cambio toca varios lugares a la vez.
- **Tu resultado:** **6** capa(s) detectada(s): presentacion, logica, datos, vistas, servicios, estado _(mínimo 2 capas (a partir de 150 LOC))_

### 6. Acceso a datos dentro del componente (HTTP) — OK

- **Qué mide:** Llamadas `fetch`/`axios` dentro de componentes de UI en vez de una capa de servicios/API.
- **Por qué importa:** Duplica la lógica de acceso a datos y acopla la vista al backend: un cambio de API toca muchos componentes.
- **Tu resultado:** **0** llamada(s) a la API dentro de componente(s) _(máximo 0)_

### 7. Depuración olvidada (DBG) — OK

- **Qué mide:** Mensajes de depuración olvidados (`console.log`, `print`, `debugger`).
- **Por qué importa:** Generan ruido en los registros, pueden filtrar datos y dan sensación de código sin terminar.
- **Tu resultado:** **0** mensaje(s) de depuración olvidado(s) _(máximo 0)_

### 8. Uso del tipo `any` (Any) — OK

- **Qué mide:** Uso de `any` en TypeScript, que desactiva la verificación de tipos.
- **Por qué importa:** Se pierde la ayuda del compilador justo donde los datos vienen de afuera (API, formularios).
- **Tu resultado:** **0** uso(s) de `any` _(máximo 2)_

### 9. Componente demasiado grande (BigC) — A REVISAR

- **Qué mide:** Componentes de UI muy extensos, que suelen mezclar render, estado y lógica.
- **Por qué importa:** Son difíciles de leer, probar y reutilizar, y sus cambios tienen efectos inesperados.
- **Tu resultado:** **5** componente(s) demasiado grande(s) _(máximo 1)_
- **Para investigar la causa:**
    - ¿El componente creció a medida que se agregaban requisitos, sin volver a dividirlo?
    - ¿Mezcla responsabilidades distintas (mostrar, calcular, pedir datos)?
    - ¿Se dividió por pantalla o por unidad de responsabilidad?

### 10. Baja cohesión (Coh) — A REVISAR

- **Qué mide:** Una clase o unidad cuyos métodos y campos no están relacionados entre sí.
- **Por qué importa:** Una unidad que cambia por motivos distintos es frágil y cuesta entenderla.
- **Tu resultado:** **4** unidad(es) con baja cohesión _(máximo 0)_
- **Para investigar la causa:**
    - ¿La unidad agrupa cosas que en realidad pertenecen a lugares distintos?
    - ¿Cambia por motivos diferentes según la tarea?
    - ¿Se pensó su responsabilidad antes de escribirla, o se fue agregando?

### 11. Complejidad alta (Compl) — A REVISAR

- **Qué mide:** Complejidad ciclomática: cantidad de caminos posibles dentro de una función (condicionales, bucles, casos).
- **Por qué importa:** Muchos caminos = difícil de seguir y de probar; suelen esconderse casos sin cubrir.
- **Tu resultado:** **41** bloque(s) de complejidad alta _(máximo 5 por 1000 LOC (tenés 7633 LOC))_
- **Para investigar la causa:**
    - ¿Se agregaron condiciones a medida que aparecían casos nuevos?
    - ¿Se probaron todos los caminos o solo el caso principal?
    - ¿Hay reglas de negocio mezcladas con detalles técnicos?

### 12. Funciones/métodos largos o con muchos parámetros (Tam) — OK

- **Qué mide:** Tamaño de las funciones/métodos y cantidad de parámetros.
- **Por qué importa:** Una función que hace varias cosas cuesta leerla, nombrarla y reutilizarla.
- **Tu resultado:** **54** función/método(s) largos o con muchos parámetros _(máximo 10 por 1000 LOC)_

### 13. Acoplamiento alto (Acop) — A REVISAR

- **Qué mide:** Cuánto depende una unidad de las partes internas de otra.
- **Por qué importa:** Piezas muy enlazadas hacen que un cambio se propague y que sea difícil reemplazar partes.
- **Tu resultado:** **20** unidad(es) con acoplamiento alto _(máximo 2 por 1000 LOC)_
- **Para investigar la causa:**
    - ¿Las piezas se conocen en detalle entre sí (acceden a campos o estructuras internas)?
    - ¿El acceso a datos ocurre desde lugares que no son los responsables?
    - ¿Se puede cambiar una parte sin tocar las demás?

### 14. Cobertura de tests (Cob) — A REVISAR

- **Qué mide:** Porcentaje de líneas de código ejecutadas por la suite de tests (cobertura real, no cantidad de archivos de test).
- **Por qué importa:** Un test que existe pero no ejecuta el código no protege de nada: la cobertura muestra qué partes quedan sin verificar.
- **Tu resultado:** **72.2%** de líneas cubiertas · fuente: ejecución: pytest (backend-service1 60.2%, backend-service2 83.6%) _(mínimo 80% de líneas)_
- **Para investigar la causa:**
    - ¿Qué módulos o ramas del sistema nunca se ejecutan en los tests?
    - ¿Los tests prueban el camino principal y los errores, o solo el caso feliz?
    - ¿La suite se puede correr en CI sin base de datos ni servicios externos?

### 15. Endpoints del backend (EP) — OK

- **Qué mide:** Cantidad de endpoints (rutas HTTP) expuestos por el backend.
- **Por qué importa:** El backend se mide por lo que expone: pocos endpoints sugiere poca funcionalidad de servicio.
- **Tu resultado:** **41** endpoint(s) _(mínimo 5)_

### 16. Vistas del frontend (Vistas) — OK

- **Qué mide:** Cantidad de vistas/componentes de pantalla del frontend.
- **Por qué importa:** El frontend se mide por pantallas: pocas vistas sugiere poca cobertura de la interfaz pedida.
- **Tu resultado:** **20** vista(s)/componente(s) _(mínimo 6)_

## 5. Observaciones y qué falta

Criterios que hoy están en rojo y, para cada uno, una explicación breve de **cómo corregirlo** hasta alcanzar el nivel de aprobación (perfil `exigente`):

| Criterio | Resultado actual | Meta | Brecha | Cómo alcanzarlo |
|---|---|---|---|---|
| Índice de calidad de servicios (indice) | índice **27/100** | mínimo 50 | faltan 23 pts | El índice sólo penaliza lo que **excede** los umbrales de cada criterio: si tenés todo en verde, el índice es 100. Si está en rojo, mirá la columna **Brecha** y los criterios en rojo; corregí primero duplicación, SEC, SQL y capas. Meta del perfil exigente: ≥50. |
| Componente demasiado grande (BigC) | **5** componente(s) demasiado grande(s) | máximo 1 | 4 componente(s) de más | Dividí el componente por responsabilidad en subcomponentes (render, estado, acceso a datos) y dejá el original sólo como orquestador. Meta: ≤1 componente grande. |
| Baja cohesión (Coh) | **4** unidad(es) con baja cohesión | máximo 0 | 4 clase(s) a separar | Separá la clase en unidades con una sola responsabilidad: si los métodos cambian por motivos distintos, son clases distintas. Meta: 0 clases con baja cohesión. |
| Complejidad alta (Compl) | **41** bloque(s) de complejidad alta | máximo 5 por 1000 LOC (tenés 7633 LOC) | 41 hallazgo(s); el máximo para 7,633 LOC es 38.2 | Extraé condiciones y ramas a funciones con nombre propio, usá retornos tempranos y evitá anidar `if`/`switch`. Meta: ≤5 bloques por 1000 LOC. |
| Acoplamiento alto (Acop) | **20** unidad(es) con acoplamiento alto | máximo 2 por 1000 LOC | 20 hallazgo(s); el máximo para 7,633 LOC es 15.3 | Hacé que cada unidad dependa de una interfaz o de un módulo de servicio, no de los detalles internos de otra; evitá acceder a campos ajenos. Meta: ≤2 por 1000 LOC. |
| Cobertura de tests (Cob) | **72.2%** de líneas cubiertas · fuente: ejecución: pytest (backend-service1 60.2%, backend-service2 83.6%) | mínimo 80% de líneas | faltan 7.8 pts | Agregá o ampliá tests que ejecuten los módulos sin cubrir (camino principal y errores) y publicá el artefacto (`coverage/lcov.info`, `coverage-summary.json`, `coverage.xml` o `coverage.json`) o corré la suite con coverage. Meta: ≥80% de líneas. |

> Empezá por las señales de seguridad (**SEC**, **SQL**) y por la **duplicación**: son las que más pesan en el índice y las más rápidas de verificar a ojo. Después de corregir, volvé a correr la medición: el semáforo se recalcula sobre `main`.

## 6. Actividad en clase y fuera de clase

> Se consideran las **29 clases** del período (miércoles y viernes, según `config/constancia.json`; feriados y semanas sin clase descontados). Para cada alumno se muestra la actividad **en cada clase** y también la actividad **fuera de los días de clase** (fines de semana u otros días). `Commits` = commits de trabajo (no-merge); `Merges` = merges de PR (también son push). Los días sin actividad dicen **sin actividad**.

### manu_abrego_1913

**11/29 clases con actividad** · total del período: 12 commits · 10 merges

| Fecha | Actividad | Repositorios | Commits / merges |
|---|:--:|---|--:|
| 2026-08-14 | **Sí** | BanSystem | 1 / 0 |
| 2026-08-19 | No | sin actividad | 0 / 0 |
| 2026-08-21 | No | sin actividad | 0 / 0 |
| 2026-08-26 | No | sin actividad | 0 / 0 |
| 2026-08-28 | **Sí** | BanSystem, beta | 2 / 1 |
| 2026-09-02 | **Sí** | BanSystem | 1 / 1 |
| 2026-09-04 | **Sí** | BanSystem | 2 / 1 |
| 2026-09-09 | **Sí** | BanSystem | 0 / 1 |
| 2026-09-11 | No | sin actividad | 0 / 0 |
| 2026-09-16 | No | sin actividad | 0 / 0 |
| 2026-09-18 | No | sin actividad | 0 / 0 |
| 2026-09-23 | No | sin actividad | 0 / 0 |
| 2026-09-25 | No | sin actividad | 0 / 0 |
| 2026-09-30 | No | sin actividad | 0 / 0 |
| 2026-10-02 | No | sin actividad | 0 / 0 |
| 2026-10-07 | No | sin actividad | 0 / 0 |
| 2026-10-09 | No | sin actividad | 0 / 0 |
| 2026-10-14 | **Sí** | beta | 1 / 0 |
| 2026-10-16 | **Sí** | beta | 0 / 1 |
| 2026-10-21 | **Sí** | beta | 1 / 1 |
| 2026-10-23 | No | sin actividad | 0 / 0 |
| 2026-10-28 | **Sí** | beta | 2 / 1 |
| 2026-10-30 | **Sí** | beta | 1 / 2 |
| 2026-11-04 | No | sin actividad | 0 / 0 |
| 2026-11-06 | No | sin actividad | 0 / 0 |
| 2026-11-11 | **Sí** | beta | 1 / 1 |
| 2026-11-13 | No | sin actividad | 0 / 0 |
| 2026-11-18 | No | sin actividad | 0 / 0 |
| 2026-11-20 | No | sin actividad | 0 / 0 |

**Fuera de clase:** sin actividad registrada.

### SantiMulet

**14/29 clases con actividad** · total del período: 23 commits · 10 merges

| Fecha | Actividad | Repositorios | Commits / merges |
|---|:--:|---|--:|
| 2026-08-14 | **Sí** | BanSystem | 1 / 0 |
| 2026-08-19 | No | sin actividad | 0 / 0 |
| 2026-08-21 | No | sin actividad | 0 / 0 |
| 2026-08-26 | **Sí** | BanSystem | 2 / 1 |
| 2026-08-28 | No | sin actividad | 0 / 0 |
| 2026-09-02 | **Sí** | BanSystem | 1 / 1 |
| 2026-09-04 | **Sí** | BanSystem | 2 / 0 |
| 2026-09-09 | **Sí** | BanSystem | 1 / 1 |
| 2026-09-11 | No | sin actividad | 0 / 0 |
| 2026-09-16 | No | sin actividad | 0 / 0 |
| 2026-09-18 | No | sin actividad | 0 / 0 |
| 2026-09-23 | No | sin actividad | 0 / 0 |
| 2026-09-25 | No | sin actividad | 0 / 0 |
| 2026-09-30 | No | sin actividad | 0 / 0 |
| 2026-10-02 | **Sí** | BanSystem | 1 / 0 |
| 2026-10-07 | **Sí** | BanSystem | 1 / 1 |
| 2026-10-09 | No | sin actividad | 0 / 0 |
| 2026-10-14 | **Sí** | BanSystem | 0 / 1 |
| 2026-10-16 | **Sí** | BanSystem | 4 / 0 |
| 2026-10-21 | **Sí** | BanSystem | 4 / 1 |
| 2026-10-23 | No | sin actividad | 0 / 0 |
| 2026-10-28 | **Sí** | BanSystem | 3 / 2 |
| 2026-10-30 | **Sí** | BanSystem | 2 / 1 |
| 2026-11-04 | No | sin actividad | 0 / 0 |
| 2026-11-06 | No | sin actividad | 0 / 0 |
| 2026-11-11 | **Sí** | BanSystem | 1 / 0 |
| 2026-11-13 | **Sí** | BanSystem | 0 / 1 |
| 2026-11-18 | No | sin actividad | 0 / 0 |
| 2026-11-20 | No | sin actividad | 0 / 0 |

**Fuera de clase:** sin actividad registrada.

## 7. Anexo: archivos donde se originan los problemas

Se listan **todos** los archivos y líneas que el análisis marca para cada criterio en rojo. Para **duplicación** se muestran los archivos con líneas repetidas; para **cobertura**, las unidades por debajo del umbral.

**Resumen por archivo** — archivos con más hallazgos:

| Archivo | Hallazgos | Peso total | Señales |
|---|---:|---:|---|
| `frontend-admin/src/pages/ResetPasswordPage.jsx` | 8 | 38 | big_component, high_complexity, long_function |
| `backend-service2/app/bans.py` | 7 | 37 | high_complexity, high_coupling, long_method, long_params |
| `backend-service2/app/monitor.py` | 6 | 35 | high_complexity, high_coupling, long_method, long_params, low_cohesion |
| `backend-service1/app/api/v1/endpoints/banned_ips.py` | 5 | 22 | high_complexity, long_function |
| `backend-service1/app/core/security.py` | 5 | 21 | high_complexity, long_function |
| `backend-service2/app/ufw.py` | 5 | 30 | high_complexity, high_coupling, long_method, long_params, low_cohesion |
| `frontend-admin/src/components/ui.jsx` | 5 | 22 | big_component, long_params |
| `backend-service1/app/schemas/config.py` | 4 | 32 | high_coupling |
| `backend-service1/app/services/auth_service.py` | 4 | 26 | high_complexity, high_coupling, long_method |
| `backend-service1/app/services/mail_service.py` | 4 | 22 | high_complexity, high_coupling, long_method, long_params |
| `backend-service2/app/unban_worker.py` | 4 | 22 | high_complexity, high_coupling, long_method, long_params |
| `frontend-admin/src/context/AuthProvider.jsx` | 4 | 18 | high_complexity, long_function |
| `frontend-admin/src/hooks/useBanConfig.js` | 4 | 19 | high_complexity, long_function |
| `frontend-admin/src/pages/ForgotPasswordPage.jsx` | 4 | 18 | high_complexity, long_function |
| `frontend-admin/src/pages/LoginPage.jsx` | 4 | 18 | high_complexity, long_function |
| `backend-service1/app/core/config.py` | 3 | 21 | high_complexity, high_coupling, low_cohesion |
| `backend-service2/app/api.py` | 3 | 13 | high_complexity, long_function |
| `backend-service2/app/engine.py` | 3 | 18 | high_complexity, high_coupling, long_method |
| `backend-service2/app/tailer.py` | 3 | 18 | high_complexity, high_coupling |
| `backend-service2/app/telemetry.py` | 3 | 17 | high_complexity, high_coupling, long_params |
| `backend-service2/scripts/demo_ufw.py` | 3 | 13 | high_complexity, long_function |
| `frontend-admin/src/pages/SetupPage.jsx` | 3 | 14 | high_complexity, long_function |
| `frontend-admin/src/utils/validation.js` | 3 | 15 | high_complexity |
| `backend-service1/app/main.py` | 2 | 8 | long_function |
| `backend-service1/app/schemas/auth.py` | 2 | 16 | high_coupling, low_cohesion |
| … | … | … | y 17 archivo(s) más |

**Índice (indice)** — todos los hallazgos que lo afectan:

| Archivo:línea | Señal | Peso | Detalle |
|---|---|---:|---|
| `backend-service1/app/core/config.py:32` | low_cohesion | 8 | clase 'Settings' con baja cohesión (2%) |
| `backend-service1/app/core/config.py:32` | high_coupling | 8 | clase 'Settings' muy acoplada (CBO=59) |
| `backend-service1/app/schemas/auth.py:35` | low_cohesion | 8 | clase 'AdminRecord' con baja cohesión (0%) |
| `backend-service1/app/schemas/auth.py:92` | high_coupling | 8 | clase 'SetupRequest' muy acoplada (CBO=9) |
| `backend-service1/app/schemas/config.py:21` | high_coupling | 8 | clase 'BanSettings' muy acoplada (CBO=9) |
| `backend-service1/app/schemas/config.py:49` | high_coupling | 8 | clase 'WhitelistEntryRequest' muy acoplada (CBO=11) |
| `backend-service1/app/schemas/config.py:91` | high_coupling | 8 | clase 'BanRecord' muy acoplada (CBO=9) |
| `backend-service1/app/schemas/config.py:118` | high_coupling | 8 | clase 'HistoryEntry' muy acoplada (CBO=9) |
| `backend-service1/app/services/auth_service.py:50` | high_coupling | 8 | clase 'ResetOutcome' muy acoplada (CBO=8) |
| `backend-service1/app/services/auth_service.py:137` | high_coupling | 8 | clase 'AuthService' muy acoplada (CBO=48) |
| `backend-service1/app/services/config_service.py:64` | high_coupling | 8 | clase 'ConfigService' muy acoplada (CBO=30) |
| `backend-service1/app/services/mail_service.py:51` | high_coupling | 8 | clase 'MailService' muy acoplada (CBO=30) |
| `backend-service2/app/bans.py:87` | high_coupling | 8 | clase 'BanService' muy acoplada (CBO=37) |
| `backend-service2/app/config.py:17` | high_coupling | 8 | clase 'Settings' muy acoplada (CBO=38) |
| `backend-service2/app/engine.py:28` | high_coupling | 8 | clase 'SecurityEngine' muy acoplada (CBO=25) |
| `backend-service2/app/models.py:17` | high_coupling | 8 | clase 'SSHEvent' muy acoplada (CBO=12) |
| `backend-service2/app/monitor.py:20` | low_cohesion | 8 | clase 'LogMonitor' con baja cohesión (32%) |
| `backend-service2/app/monitor.py:20` | high_coupling | 8 | clase 'LogMonitor' muy acoplada (CBO=44) |
| `backend-service2/app/redis_config.py:61` | high_coupling | 8 | clase 'RedisConfigReader' muy acoplada (CBO=18) |
| `backend-service2/app/tailer.py:19` | high_coupling | 8 | clase 'LogTailer' muy acoplada (CBO=10) |
| `backend-service2/app/telemetry.py:53` | high_coupling | 8 | clase 'TelemetryStore' muy acoplada (CBO=21) |
| `backend-service2/app/ufw.py:69` | low_cohesion | 8 | clase 'UfwExecutor' con baja cohesión (29%) |
| `backend-service2/app/ufw.py:69` | high_coupling | 8 | clase 'UfwExecutor' muy acoplada (CBO=19) |
| `backend-service2/app/unban_worker.py:48` | high_coupling | 8 | clase 'UnbanWorker' muy acoplada (CBO=28) |
| `frontend-admin/src/components/ui.jsx:1` | big_component | 6 | componente grande (151 líneas) |
| `frontend-admin/src/pages/DashboardPage.jsx:1` | big_component | 6 | componente grande (159 líneas) |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:1` | big_component | 6 | componente grande (169 líneas) |
| `frontend-ops/src/views/BansView.vue:1` | big_component | 6 | componente grande (241 líneas) |
| `frontend-ops/src/views/LogsView.vue:1` | big_component | 6 | componente grande (240 líneas) |
| `backend-service1/app/api/v1/endpoints/banned_ips.py:50` | high_complexity | 5 | función 'read_banned_ips' con complejidad 6 |
| `backend-service1/app/api/v1/endpoints/banned_ips.py:103` | high_complexity | 5 | función 'ban_ip_manual' con complejidad 6 |
| `backend-service1/app/core/config.py:178` | high_complexity | 5 | método 'Settings._validate_runtime_consistency' con complejidad 6 |
| `backend-service1/app/core/security.py:99` | high_complexity | 5 | función 'password_policy_violations' con complejidad 7 |
| `backend-service1/app/services/auth_service.py:283` | long_method | 5 | método 'AuthService.get_reset_token_info' de 34 líneas |
| `backend-service1/app/services/auth_service.py:283` | high_complexity | 5 | método 'AuthService.get_reset_token_info' con complejidad 7 |
| `backend-service1/app/services/mail_service.py:93` | long_method | 5 | método 'MailService._send_via_smtp' de 38 líneas |
| `backend-service1/app/services/mail_service.py:93` | high_complexity | 5 | método 'MailService._send_via_smtp' con complejidad 7 |
| `backend-service2/app/api.py:75` | high_complexity | 5 | función 'list_logs' con complejidad 13 |
| `backend-service2/app/auth.py:58` | high_complexity | 5 | función 'authenticate' con complejidad 8 |
| `backend-service2/app/bans.py:108` | long_method | 5 | método 'BanService.ban' de 61 líneas |
| `backend-service2/app/bans.py:201` | long_method | 5 | método 'BanService.unban' de 63 líneas |
| `backend-service2/app/bans.py:201` | high_complexity | 5 | método 'BanService.unban' con complejidad 6 |
| `backend-service2/app/bans.py:296` | long_method | 5 | método 'BanService.reconcile' de 40 líneas |
| `backend-service2/app/bans.py:296` | high_complexity | 5 | método 'BanService.reconcile' con complejidad 11 |
| `backend-service2/app/engine.py:41` | long_method | 5 | método 'SecurityEngine.process' de 40 líneas |
| `backend-service2/app/engine.py:41` | high_complexity | 5 | método 'SecurityEngine.process' con complejidad 7 |
| `backend-service2/app/main.py:19` | high_complexity | 5 | función 'create_app' con complejidad 7 |
| `backend-service2/app/monitor.py:126` | high_complexity | 5 | método 'LogMonitor.run_maintenance' con complejidad 6 |
| `backend-service2/app/monitor.py:151` | long_method | 5 | método 'LogMonitor._log' de 34 líneas |
| `backend-service2/app/monitor.py:151` | high_complexity | 5 | método 'LogMonitor._log' con complejidad 9 |
| `backend-service2/app/parser.py:131` | long_method | 5 | método 'SSHParser.parse' de 36 líneas |
| `backend-service2/app/parser.py:131` | high_complexity | 5 | método 'SSHParser.parse' con complejidad 7 |
| `backend-service2/app/redis_config.py:87` | high_complexity | 5 | método 'RedisConfigReader.match_whitelist' con complejidad 6 |
| `backend-service2/app/runner.py:40` | high_complexity | 5 | función 'main' con complejidad 8 |
| `backend-service2/app/tailer.py:50` | high_complexity | 5 | método 'LogTailer.read_available' con complejidad 6 |
| `backend-service2/app/tailer.py:72` | high_complexity | 5 | método 'LogTailer._prepare_file' con complejidad 7 |
| `backend-service2/app/telemetry.py:85` | high_complexity | 5 | método 'TelemetryStore.list_events' con complejidad 13 |
| `backend-service2/app/ufw.py:143` | long_method | 5 | método 'UfwExecutor._execute' de 37 líneas |
| `backend-service2/app/ufw.py:143` | high_complexity | 5 | método 'UfwExecutor._execute' con complejidad 11 |
| `backend-service2/app/unban_worker.py:130` | high_complexity | 5 | método 'UnbanWorker._read_and_process' con complejidad 8 |
| `backend-service2/app/unban_worker.py:175` | long_method | 5 | método 'UnbanWorker._handle' de 39 líneas |
| `backend-service2/scripts/demo_ufw.py:83` | high_complexity | 5 | función 'main' con complejidad 13 |
| `frontend-admin/src/context/AuthProvider.jsx:46` | high_complexity | 5 | función 'useEffect' con complejidad 11 |
| `frontend-admin/src/context/AuthProvider.jsx:49` | high_complexity | 5 | función 'bootstrap' con complejidad 11 |
| `frontend-admin/src/hooks/useBanConfig.js:23` | high_complexity | 5 | función 'useBanConfig' con complejidad 6 |
| `frontend-admin/src/hooks/useBanConfig.js:31` | high_complexity | 5 | función 'useEffect' con complejidad 6 |
| `frontend-admin/src/hooks/useBanConfig.js:34` | high_complexity | 5 | función 'loadConfig' con complejidad 6 |
| `frontend-admin/src/pages/ForgotPasswordPage.jsx:20` | high_complexity | 5 | función 'ForgotPasswordPage' con complejidad 8 |
| `frontend-admin/src/pages/ForgotPasswordPage.jsx:30` | high_complexity | 5 | función 'handleSubmit' con complejidad 7 |
| `frontend-admin/src/pages/LoginPage.jsx:16` | high_complexity | 5 | función 'LoginPage' con complejidad 17 |
| `frontend-admin/src/pages/LoginPage.jsx:45` | high_complexity | 5 | función 'handleSubmit' con complejidad 12 |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:26` | high_complexity | 5 | función 'ResetPasswordPage' con complejidad 19 |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:45` | high_complexity | 5 | función 'useEffect' con complejidad 9 |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:54` | high_complexity | 5 | función 'verify' con complejidad 8 |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:95` | high_complexity | 5 | función 'handleSubmit' con complejidad 6 |
| `frontend-admin/src/pages/SetupPage.jsx:19` | high_complexity | 5 | función 'SetupPage' con complejidad 12 |
| `frontend-admin/src/pages/SetupPage.jsx:35` | high_complexity | 5 | función 'validate' con complejidad 6 |
| `frontend-admin/src/utils/validation.js:51` | high_complexity | 5 | función 'getPasswordViolations' con complejidad 8 |
| `frontend-admin/src/utils/validation.js:143` | high_complexity | 5 | función 'isValidIPv6' con complejidad 9 |
| `frontend-admin/src/utils/validation.js:171` | high_complexity | 5 | función 'isValidIpOrCidr' con complejidad 9 |
| `backend-service1/app/api/v1/endpoints/auth.py:198` | long_function | 4 | función 'forgot_password' de 30 líneas |
| `backend-service1/app/api/v1/endpoints/banned_ips.py:50` | long_function | 4 | función 'read_banned_ips' de 30 líneas |
| `backend-service1/app/api/v1/endpoints/banned_ips.py:103` | long_function | 4 | función 'ban_ip_manual' de 84 líneas |
| `backend-service1/app/api/v1/endpoints/banned_ips.py:209` | long_function | 4 | función 'unban_ip_manual' de 80 líneas |
| `backend-service1/app/api/v1/endpoints/config.py:183` | long_function | 4 | función 'remove_whitelist_entry' de 37 líneas |
| `backend-service1/app/api/v1/endpoints/history.py:50` | long_function | 4 | función 'read_banned_ip_history' de 30 líneas |
| `backend-service1/app/core/security.py:136` | long_function | 4 | función '_build_password_hasher' de 30 líneas |
| `backend-service1/app/core/security.py:208` | long_function | 4 | función 'verify_password' de 30 líneas |
| `backend-service1/app/core/security.py:251` | long_function | 4 | función 'create_access_token' de 40 líneas |
| `backend-service1/app/core/security.py:293` | long_function | 4 | función 'decode_access_token' de 36 líneas |
| `backend-service1/app/db/redis.py:47` | long_function | 4 | función 'wait_for_redis' de 35 líneas |
| `backend-service1/app/main.py:89` | long_function | 4 | función 'create_app' de 37 líneas |
| `backend-service1/app/main.py:131` | long_function | 4 | función '_register_exception_handlers' de 33 líneas |
| `backend-service1/app/services/mail_service.py:136` | long_params | 4 | método 'MailService._smtp_auth_and_send' con 5 parámetros |
| `backend-service2/app/api.py:75` | long_function | 4 | función 'list_logs' de 43 líneas |
| `backend-service2/app/api.py:164` | long_function | 4 | función 'request_unban' de 37 líneas |
| `backend-service2/app/auth.py:58` | long_function | 4 | función 'authenticate' de 32 líneas |
| `backend-service2/app/bans.py:90` | long_params | 4 | método 'BanService.__init__' con 6 parámetros |
| `backend-service2/app/main.py:19` | long_function | 4 | función 'create_app' de 39 líneas |
| `backend-service2/app/monitor.py:23` | long_params | 4 | método 'LogMonitor.__init__' con 8 parámetros |
| `backend-service2/app/runner.py:40` | long_function | 4 | función 'main' de 78 líneas |
| `backend-service2/app/telemetry.py:85` | long_params | 4 | método 'TelemetryStore.list_events' con 6 parámetros |
| `backend-service2/app/ufw.py:72` | long_params | 4 | método 'UfwExecutor.__init__' con 7 parámetros |
| `backend-service2/app/unban_worker.py:51` | long_params | 4 | método 'UnbanWorker.__init__' con 9 parámetros |
| `backend-service2/scripts/demo_engine.py:41` | long_function | 4 | función 'main' de 41 líneas |
| `backend-service2/scripts/demo_ufw.py:51` | long_function | 4 | función 'parse_args' de 30 líneas |
| `backend-service2/scripts/demo_ufw.py:83` | long_function | 4 | función 'main' de 70 líneas |
| `frontend-admin/src/components/ui.jsx:14` | long_params | 4 | función 'Button' con 6 parámetros |
| `frontend-admin/src/components/ui.jsx:32` | long_params | 4 | función 'Field' con 11 parámetros |
| `frontend-admin/src/components/ui.jsx:76` | long_params | 4 | función 'PasswordField' con 10 parámetros |
| `frontend-admin/src/components/ui.jsx:149` | long_params | 4 | función 'AuthLayout' con 5 parámetros |
| `frontend-admin/src/context/AuthProvider.jsx:46` | long_function | 4 | función 'useEffect' de 42 líneas |
| `frontend-admin/src/context/AuthProvider.jsx:49` | long_function | 4 | función 'bootstrap' de 35 líneas |
| `frontend-admin/src/hooks/useBanConfig.js:23` | long_function | 4 | función 'useBanConfig' de 70 líneas |
| `frontend-admin/src/pages/DashboardPage.jsx:32` | long_function | 4 | función 'DashboardPage' de 132 líneas |
| `frontend-admin/src/pages/ForgotPasswordPage.jsx:20` | long_function | 4 | función 'ForgotPasswordPage' de 82 líneas |
| `frontend-admin/src/pages/ForgotPasswordPage.jsx:30` | long_function | 4 | función 'handleSubmit' de 30 líneas |
| `frontend-admin/src/pages/LoginPage.jsx:16` | long_function | 4 | función 'LoginPage' de 109 líneas |
| `frontend-admin/src/pages/LoginPage.jsx:45` | long_function | 4 | función 'handleSubmit' de 44 líneas |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:26` | long_function | 4 | función 'ResetPasswordPage' de 148 líneas |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:45` | long_function | 4 | función 'useEffect' de 31 líneas |
| `frontend-admin/src/pages/ResetPasswordPage.jsx:95` | long_function | 4 | función 'handleSubmit' de 34 líneas |
| `frontend-admin/src/pages/SetupPage.jsx:19` | long_function | 4 | función 'SetupPage' de 122 líneas |
| `frontend-ops/src/api/client.js:92` | long_params | 4 | función 'fetchLogs' con 5 parámetros |

**Componente demasiado grande (BigC)** — 5 hallazgo(s) en 5 archivo(s):

| Archivo | Línea(s) | Señal | Detalle |
|---|---|---|---|
| `frontend-admin/src/components/ui.jsx` | 1 | big_component | componente grande (151 líneas) |
| `frontend-admin/src/pages/DashboardPage.jsx` | 1 | big_component | componente grande (159 líneas) |
| `frontend-admin/src/pages/ResetPasswordPage.jsx` | 1 | big_component | componente grande (169 líneas) |
| `frontend-ops/src/views/BansView.vue` | 1 | big_component | componente grande (241 líneas) |
| `frontend-ops/src/views/LogsView.vue` | 1 | big_component | componente grande (240 líneas) |

**Baja cohesión (Coh)** — 4 hallazgo(s) en 4 archivo(s):

| Archivo | Línea(s) | Señal | Detalle |
|---|---|---|---|
| `backend-service1/app/core/config.py` | 32 | low_cohesion | clase 'Settings' con baja cohesión (2%) |
| `backend-service1/app/schemas/auth.py` | 35 | low_cohesion | clase 'AdminRecord' con baja cohesión (0%) |
| `backend-service2/app/monitor.py` | 20 | low_cohesion | clase 'LogMonitor' con baja cohesión (32%) |
| `backend-service2/app/ufw.py` | 69 | low_cohesion | clase 'UfwExecutor' con baja cohesión (29%) |

**Complejidad alta (Compl)** — 41 hallazgo(s) en 26 archivo(s):

| Archivo | Línea(s) | Señal | Detalle |
|---|---|---|---|
| `backend-service1/app/api/v1/endpoints/banned_ips.py` | 50, 103 | high_complexity | función 'read_banned_ips' con complejidad 6 |
| `backend-service1/app/core/config.py` | 178 | high_complexity | método 'Settings._validate_runtime_consistency' con complejidad 6 |
| `backend-service1/app/core/security.py` | 99 | high_complexity | función 'password_policy_violations' con complejidad 7 |
| `backend-service1/app/services/auth_service.py` | 283 | high_complexity | método 'AuthService.get_reset_token_info' con complejidad 7 |
| `backend-service1/app/services/mail_service.py` | 93 | high_complexity | método 'MailService._send_via_smtp' con complejidad 7 |
| `backend-service2/app/api.py` | 75 | high_complexity | función 'list_logs' con complejidad 13 |
| `backend-service2/app/auth.py` | 58 | high_complexity | función 'authenticate' con complejidad 8 |
| `backend-service2/app/bans.py` | 201, 296 | high_complexity | método 'BanService.unban' con complejidad 6 |
| `backend-service2/app/engine.py` | 41 | high_complexity | método 'SecurityEngine.process' con complejidad 7 |
| `backend-service2/app/main.py` | 19 | high_complexity | función 'create_app' con complejidad 7 |
| `backend-service2/app/monitor.py` | 126, 151 | high_complexity | método 'LogMonitor.run_maintenance' con complejidad 6 |
| `backend-service2/app/parser.py` | 131 | high_complexity | método 'SSHParser.parse' con complejidad 7 |
| `backend-service2/app/redis_config.py` | 87 | high_complexity | método 'RedisConfigReader.match_whitelist' con complejidad 6 |
| `backend-service2/app/runner.py` | 40 | high_complexity | función 'main' con complejidad 8 |
| `backend-service2/app/tailer.py` | 50, 72 | high_complexity | método 'LogTailer.read_available' con complejidad 6 |
| `backend-service2/app/telemetry.py` | 85 | high_complexity | método 'TelemetryStore.list_events' con complejidad 13 |
| `backend-service2/app/ufw.py` | 143 | high_complexity | método 'UfwExecutor._execute' con complejidad 11 |
| `backend-service2/app/unban_worker.py` | 130 | high_complexity | método 'UnbanWorker._read_and_process' con complejidad 8 |
| `backend-service2/scripts/demo_ufw.py` | 83 | high_complexity | función 'main' con complejidad 13 |
| `frontend-admin/src/context/AuthProvider.jsx` | 46, 49 | high_complexity | función 'useEffect' con complejidad 11 |
| `frontend-admin/src/hooks/useBanConfig.js` | 23, 31, 34 | high_complexity | función 'useBanConfig' con complejidad 6 |
| `frontend-admin/src/pages/ForgotPasswordPage.jsx` | 20, 30 | high_complexity | función 'ForgotPasswordPage' con complejidad 8 |
| `frontend-admin/src/pages/LoginPage.jsx` | 16, 45 | high_complexity | función 'LoginPage' con complejidad 17 |
| `frontend-admin/src/pages/ResetPasswordPage.jsx` | 26, 45, 54, 95 | high_complexity | función 'ResetPasswordPage' con complejidad 19 |
| `frontend-admin/src/pages/SetupPage.jsx` | 19, 35 | high_complexity | función 'SetupPage' con complejidad 12 |
| `frontend-admin/src/utils/validation.js` | 51, 143, 171 | high_complexity | función 'getPasswordViolations' con complejidad 8 |

**Acoplamiento alto (Acop)** — 20 hallazgo(s) en 16 archivo(s):

| Archivo | Línea(s) | Señal | Detalle |
|---|---|---|---|
| `backend-service1/app/core/config.py` | 32 | high_coupling | clase 'Settings' muy acoplada (CBO=59) |
| `backend-service1/app/schemas/auth.py` | 92 | high_coupling | clase 'SetupRequest' muy acoplada (CBO=9) |
| `backend-service1/app/schemas/config.py` | 21, 49, 91, 118 | high_coupling | clase 'BanSettings' muy acoplada (CBO=9) |
| `backend-service1/app/services/auth_service.py` | 50, 137 | high_coupling | clase 'ResetOutcome' muy acoplada (CBO=8) |
| `backend-service1/app/services/config_service.py` | 64 | high_coupling | clase 'ConfigService' muy acoplada (CBO=30) |
| `backend-service1/app/services/mail_service.py` | 51 | high_coupling | clase 'MailService' muy acoplada (CBO=30) |
| `backend-service2/app/bans.py` | 87 | high_coupling | clase 'BanService' muy acoplada (CBO=37) |
| `backend-service2/app/config.py` | 17 | high_coupling | clase 'Settings' muy acoplada (CBO=38) |
| `backend-service2/app/engine.py` | 28 | high_coupling | clase 'SecurityEngine' muy acoplada (CBO=25) |
| `backend-service2/app/models.py` | 17 | high_coupling | clase 'SSHEvent' muy acoplada (CBO=12) |
| `backend-service2/app/monitor.py` | 20 | high_coupling | clase 'LogMonitor' muy acoplada (CBO=44) |
| `backend-service2/app/redis_config.py` | 61 | high_coupling | clase 'RedisConfigReader' muy acoplada (CBO=18) |
| `backend-service2/app/tailer.py` | 19 | high_coupling | clase 'LogTailer' muy acoplada (CBO=10) |
| `backend-service2/app/telemetry.py` | 53 | high_coupling | clase 'TelemetryStore' muy acoplada (CBO=21) |
| `backend-service2/app/ufw.py` | 69 | high_coupling | clase 'UfwExecutor' muy acoplada (CBO=19) |
| `backend-service2/app/unban_worker.py` | 48 | high_coupling | clase 'UnbanWorker' muy acoplada (CBO=28) |

**Cobertura (Cob)** — unidades por debajo del umbral:

| Unidad | Cobertura | Líneas cubiertas / totales |
|---|---:|---:|
| `backend-service1` | 60.2% | 634/1054 |

---
_Informe generado por la cátedra. Los umbrales corresponden al perfil `exigente`. Ante dudas, revisá el archivo y la línea señalados y el criterio en `CRITERIOS-CALIDAD.md`._
<!-- evaluacion:fin -->
