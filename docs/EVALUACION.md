<!-- evaluacion:inicio -->
# Evaluación — Bannedbyabrejeet/BanSystem

> Documento **generado automáticamente** por la cátedra de Programación III (RepoSense + análisis de calidad + constancia). **No editar a mano**: se regenera en cada evaluación.
> Rama evaluada: `main`. Análisis **heurístico** (regex + métricas): es una criba para orientar la revisión, **no una nota**.
> Generado: 2026-11-18.

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
| SantiMulet | 11 | 40% | 23 d | 50% | **33** | No aprueba | Cumplimiento 40% (mín. 50%) |
| manu_abrego_1913 | 6 | 22% | 61 d | 50% | **21** | No aprueba | Cumplimiento 22% (mín. 50%) |

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

> Se consideran las **28 clases** del período (miércoles y viernes, según `config/constancia.json`; feriados y semanas sin clase descontados). Para cada alumno se muestra la actividad **en cada clase** y también la actividad **fuera de los días de clase** (fines de semana u otros días). `Commits` = commits de trabajo (no-merge); `Merges` = merges de PR (también son push). Los días sin actividad dicen **sin actividad**.

### manu_abrego_1913

**11/28 clases con actividad** · total del período: 12 commits · 10 merges

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

**Fuera de clase:** sin actividad registrada.

### SantiMulet

**14/28 clases con actividad** · total del período: 23 commits · 10 merges

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

**Fuera de clase:** sin actividad registrada.

## 7. Anexo: archivos donde se originan los problemas

Se listan los archivos y líneas que el análisis marca para cada criterio en rojo. Para **duplicación** se muestran los archivos con más líneas repetidas; para **cobertura**, las unidades por debajo del umbral.

**Índice (indice)** — señales que más pesan:

- `backend-service1/app/main.py:89` — long_function: función 'create_app' de 37 líneas
- `backend-service1/app/main.py:131` — long_function: función '_register_exception_handlers' de 33 líneas
- `backend-service1/app/db/redis.py:47` — long_function: función 'wait_for_redis' de 35 líneas
- `backend-service1/app/core/config.py:32` — low_cohesion: clase 'Settings' con baja cohesión (2%)
- `backend-service1/app/core/config.py:32` — high_coupling: clase 'Settings' muy acoplada (CBO=59)
- `backend-service1/app/core/config.py:178` — high_complexity: método 'Settings._validate_runtime_consistency' con complejidad 6
- `backend-service1/app/core/security.py:99` — high_complexity: función 'password_policy_violations' con complejidad 7
- `backend-service1/app/core/security.py:136` — long_function: función '_build_password_hasher' de 30 líneas
- `backend-service1/app/core/security.py:208` — long_function: función 'verify_password' de 30 líneas
- `backend-service1/app/core/security.py:251` — long_function: función 'create_access_token' de 40 líneas
- `backend-service1/app/core/security.py:293` — long_function: función 'decode_access_token' de 36 líneas
- `backend-service1/app/api/v1/endpoints/config.py:183` — long_function: función 'remove_whitelist_entry' de 37 líneas
- `backend-service1/app/api/v1/endpoints/auth.py:198` — long_function: función 'forgot_password' de 30 líneas
- `backend-service1/app/api/v1/endpoints/history.py:50` — long_function: función 'read_banned_ip_history' de 30 líneas
- `backend-service1/app/api/v1/endpoints/banned_ips.py:50` — long_function: función 'read_banned_ips' de 30 líneas
- `backend-service1/app/api/v1/endpoints/banned_ips.py:50` — high_complexity: función 'read_banned_ips' con complejidad 6
- `backend-service1/app/api/v1/endpoints/banned_ips.py:103` — long_function: función 'ban_ip_manual' de 84 líneas
- `backend-service1/app/api/v1/endpoints/banned_ips.py:103` — high_complexity: función 'ban_ip_manual' con complejidad 6
- `backend-service1/app/api/v1/endpoints/banned_ips.py:209` — long_function: función 'unban_ip_manual' de 80 líneas
- `backend-service1/app/schemas/config.py:21` — high_coupling: clase 'BanSettings' muy acoplada (CBO=9)
- `backend-service1/app/schemas/config.py:49` — high_coupling: clase 'WhitelistEntryRequest' muy acoplada (CBO=11)
- `backend-service1/app/schemas/config.py:91` — high_coupling: clase 'BanRecord' muy acoplada (CBO=9)
- `backend-service1/app/schemas/config.py:118` — high_coupling: clase 'HistoryEntry' muy acoplada (CBO=9)
- `backend-service1/app/schemas/auth.py:35` — low_cohesion: clase 'AdminRecord' con baja cohesión (0%)
- `backend-service1/app/schemas/auth.py:92` — high_coupling: clase 'SetupRequest' muy acoplada (CBO=9)
- `backend-service1/app/services/mail_service.py:51` — high_coupling: clase 'MailService' muy acoplada (CBO=30)
- `backend-service1/app/services/mail_service.py:93` — long_method: método 'MailService._send_via_smtp' de 38 líneas
- `backend-service1/app/services/mail_service.py:93` — high_complexity: método 'MailService._send_via_smtp' con complejidad 7
- `backend-service1/app/services/mail_service.py:136` — long_params: método 'MailService._smtp_auth_and_send' con 5 parámetros
- `backend-service1/app/services/config_service.py:64` — high_coupling: clase 'ConfigService' muy acoplada (CBO=30)
- … y 94 hallazgo(s) más.

**Componente demasiado grande (BigC)** — 5 hallazgo(s) en 5 archivo(s):

| Archivo | Línea(s) | Señal |
|---|---|---|
| `frontend-admin/src/components/ui.jsx` | 1 | componente grande (151 líneas) |
| `frontend-admin/src/pages/DashboardPage.jsx` | 1 | componente grande (159 líneas) |
| `frontend-admin/src/pages/ResetPasswordPage.jsx` | 1 | componente grande (169 líneas) |
| `frontend-ops/src/views/BansView.vue` | 1 | componente grande (241 líneas) |
| `frontend-ops/src/views/LogsView.vue` | 1 | componente grande (240 líneas) |

**Baja cohesión (Coh)** — 4 hallazgo(s) en 4 archivo(s):

| Archivo | Línea(s) | Señal |
|---|---|---|
| `backend-service1/app/core/config.py` | 32 | clase 'Settings' con baja cohesión (2%) |
| `backend-service1/app/schemas/auth.py` | 35 | clase 'AdminRecord' con baja cohesión (0%) |
| `backend-service2/app/monitor.py` | 20 | clase 'LogMonitor' con baja cohesión (32%) |
| `backend-service2/app/ufw.py` | 69 | clase 'UfwExecutor' con baja cohesión (29%) |

**Complejidad alta (Compl)** — 41 hallazgo(s) en 26 archivo(s):

| Archivo | Línea(s) | Señal |
|---|---|---|
| `backend-service1/app/api/v1/endpoints/banned_ips.py` | 50, 103 | función 'read_banned_ips' con complejidad 6 |
| `backend-service1/app/core/config.py` | 178 | método 'Settings._validate_runtime_consistency' con complejidad 6 |
| `backend-service1/app/core/security.py` | 99 | función 'password_policy_violations' con complejidad 7 |
| `backend-service1/app/services/auth_service.py` | 283 | método 'AuthService.get_reset_token_info' con complejidad 7 |
| `backend-service1/app/services/mail_service.py` | 93 | método 'MailService._send_via_smtp' con complejidad 7 |
| `backend-service2/app/api.py` | 75 | función 'list_logs' con complejidad 13 |
| `backend-service2/app/auth.py` | 58 | función 'authenticate' con complejidad 8 |
| `backend-service2/app/bans.py` | 201, 296 | método 'BanService.unban' con complejidad 6 |
| `backend-service2/app/engine.py` | 41 | método 'SecurityEngine.process' con complejidad 7 |
| `backend-service2/app/main.py` | 19 | función 'create_app' con complejidad 7 |
| `backend-service2/app/monitor.py` | 126, 151 | método 'LogMonitor.run_maintenance' con complejidad 6 |
| `backend-service2/app/parser.py` | 131 | método 'SSHParser.parse' con complejidad 7 |
| `backend-service2/app/redis_config.py` | 87 | método 'RedisConfigReader.match_whitelist' con complejidad 6 |
| `backend-service2/app/runner.py` | 40 | función 'main' con complejidad 8 |
| `backend-service2/app/tailer.py` | 50, 72 | método 'LogTailer.read_available' con complejidad 6 |
| `backend-service2/app/telemetry.py` | 85 | método 'TelemetryStore.list_events' con complejidad 13 |
| `backend-service2/app/ufw.py` | 143 | método 'UfwExecutor._execute' con complejidad 11 |
| `backend-service2/app/unban_worker.py` | 130 | método 'UnbanWorker._read_and_process' con complejidad 8 |
| `backend-service2/scripts/demo_ufw.py` | 83 | función 'main' con complejidad 13 |
| `frontend-admin/src/context/AuthProvider.jsx` | 46, 49 | función 'useEffect' con complejidad 11 |
| … | … | y 6 archivo(s) más |

**Acoplamiento alto (Acop)** — 20 hallazgo(s) en 16 archivo(s):

| Archivo | Línea(s) | Señal |
|---|---|---|
| `backend-service1/app/core/config.py` | 32 | clase 'Settings' muy acoplada (CBO=59) |
| `backend-service1/app/schemas/auth.py` | 92 | clase 'SetupRequest' muy acoplada (CBO=9) |
| `backend-service1/app/schemas/config.py` | 21, 49, 91, 118 | clase 'BanSettings' muy acoplada (CBO=9) |
| `backend-service1/app/services/auth_service.py` | 50, 137 | clase 'ResetOutcome' muy acoplada (CBO=8) |
| `backend-service1/app/services/config_service.py` | 64 | clase 'ConfigService' muy acoplada (CBO=30) |
| `backend-service1/app/services/mail_service.py` | 51 | clase 'MailService' muy acoplada (CBO=30) |
| `backend-service2/app/bans.py` | 87 | clase 'BanService' muy acoplada (CBO=37) |
| `backend-service2/app/config.py` | 17 | clase 'Settings' muy acoplada (CBO=38) |
| `backend-service2/app/engine.py` | 28 | clase 'SecurityEngine' muy acoplada (CBO=25) |
| `backend-service2/app/models.py` | 17 | clase 'SSHEvent' muy acoplada (CBO=12) |
| `backend-service2/app/monitor.py` | 20 | clase 'LogMonitor' muy acoplada (CBO=44) |
| `backend-service2/app/redis_config.py` | 61 | clase 'RedisConfigReader' muy acoplada (CBO=18) |
| `backend-service2/app/tailer.py` | 19 | clase 'LogTailer' muy acoplada (CBO=10) |
| `backend-service2/app/telemetry.py` | 53 | clase 'TelemetryStore' muy acoplada (CBO=21) |
| `backend-service2/app/ufw.py` | 69 | clase 'UfwExecutor' muy acoplada (CBO=19) |
| `backend-service2/app/unban_worker.py` | 48 | clase 'UnbanWorker' muy acoplada (CBO=28) |

**Cobertura (Cob)** — unidades por debajo del umbral:

- `backend-service1` — 60.2% (634/1054 líneas)

---
_Informe generado por la cátedra. Los umbrales corresponden al perfil `exigente`. Ante dudas, revisá el archivo y la línea señalados y el criterio en `CRITERIOS-CALIDAD.md`._
<!-- evaluacion:fin -->
