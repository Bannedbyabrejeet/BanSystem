<!-- evaluacion:inicio -->
# Evaluación — Bannedbyabrejeet/BanSystem

> Documento **generado automáticamente** por la cátedra de Programación III (RepoSense + análisis de calidad + constancia). **No editar a mano**: se regenera en cada evaluación.
> Rama evaluada: `main`. Análisis **heurístico** (regex + métricas): es una criba para orientar la revisión, **no una nota**.
> Generado: 2026-10-28.

## 1. Veredicto

| Aspecto | Resultado |
|---|---|
| Tipo de proyecto | frontend |
| Índice de calidad de servicios | **6/100** (mínimo 60) |
| Criterios cumplidos | **8/15** |
| Aprobado (semáforo) | **NO** |
| Código (LOC) | 6,812 |
| Archivos de código | 75 |
| Tests (archivos) | 12 |
| Cobertura de líneas | 81.0% (mínimo 80%) |
| Capas detectadas | vistas, servicios, estado |

> **Aprobado** exige cumplir **todos** los criterios del semáforo. No es una nota: sirve para ordenar y priorizar la revisión.

## 2. Autoría (RepoSense)

| Autor | Commits | Código (LOC) | Tests (LOC) | Docs (LOC) | Días activos | % del código |
|---|---:|---:|---:|---:|---:|---:|
| SantiMulet | 13 | 4,188 | 804 | 2,287 | 10 | 100% |
| manu_abrego_1913 | 5 | 0 | 0 | 253 | 5 | 0% |

> _El LOC de autoría lo calcula RepoSense sobre el historial y puede diferir del LOC de código del análisis de calidad (que mira solo el estado de `main`)._

> **Reparto del trabajo:** SantiMulet concentra el 100% de las líneas de código. Un reparto muy desigual suele indicar que la integración no fue realmente en equipo; vale la pena reconstruir cómo se coordinó.

## 3. Constancia (IC) — todas las ramas

> El IC mide **cuándo** se trabajó (sesiones por semana, pausas y recencia), no cuánto ni con qué calidad. Se calcula sobre **todas las ramas** de todos los repositorios del alumno, no sólo `main`.

| Alumno | Sesiones | Cumplimiento | Pausa | Recencia | IC | Nivel | Para subir de nivel |
|---|--:|--:|--:|--:|--:|--|--|
| SantiMulet | 8 | 37% | 23 d | 50% | **31** | No aprueba | Cumplimiento 37% (mín. 50%); Pausa 23 d (máx. 10 d) |
| manu_abrego_1913 | 3 | 14% | 61 d | 50% | **16** | No aprueba | Cumplimiento 14% (mín. 50%); Pausa 61 d (máx. 10 d) |

> Para aprobar el IC: **2 sesiones por semana** sostenidas, sin pausas mayores a **10 días** y con actividad en las **últimas 2 semanas**. Se excluyen merges, bots y al docente. Zona horaria UTC-3.

## 4. Aspectos evaluados

Cada aspecto indica **qué mide**, **por qué importa** y **tu resultado**. Cuando el resultado está en rojo, se agregan preguntas para **investigar la causa** (no hay recetas: entender el porqué es parte de la evaluación).

### 1. Índice de calidad de servicios (indice) — A REVISAR

- **Qué mide:** Un resumen numérico (0-100) que combina todas las señales y métricas del análisis, con topes duros por duplicación.
- **Por qué importa:** Ordena y prioriza la revisión: un índice bajo indica varias señales que conviene mirar juntas.
- **Tu resultado:** índice **6/100** _(mínimo 60)_
- **Para investigar la causa:**
    - ¿En qué momento del proyecto se concentraron los problemas (arranque, integración de partes, cierre)?
    - ¿El índice bajó por muchas señales chicas o por una o dos graves?
    - ¿Se revisó el código integrado después de unir el trabajo de cada integrante?

### 2. Duplicación (DRY) (duplicacion) — OK

- **Qué mide:** Porcentaje de bloques de código repetidos (similitud) en el repositorio.
- **Por qué importa:** Cada copia se mantiene por separado: un arreglo hay que repetirlo y los defectos se multiplican.
- **Tu resultado:** **5.4%** de duplicación _(máximo 15%)_

### 3. Secretos hardcodeados (SEC) — A REVISAR

- **Qué mide:** Credenciales, tokens o claves escritos directamente en el código en vez de leerse de variables de entorno.
- **Por qué importa:** Un secreto en el repositorio queda expuesto en el historial aunque luego se borre, y compromete al servicio y a sus usuarios.
- **Tu resultado:** **1** secreto(s) hardcodeado(s) _(máximo 0)_
- **Para investigar la causa:**
    - ¿De dónde salió ese valor: un ejemplo, una prueba rápida, una copia de un compañero?
    - ¿En qué momento entró al código y por qué no se sacó antes de cerrar la tarea?
    - ¿Se acordó cómo manejar credenciales antes de empezar, o se postergó para el final?

### 4. Consultas SQL por concatenación (SQL) — OK

- **Qué mide:** Consultas SQL armadas concatenando o interpolando valores en vez de usar parámetros.
- **Por qué importa:** Es la puerta clásica a inyección: un valor que llega de afuera puede cambiar la consulta.
- **Tu resultado:** **0** consulta(s) SQL por concatenación _(máximo 0)_

### 5. Separación en capas (capas) — OK

- **Qué mide:** Si el código está separado en capas reconocibles (backend: presentación / lógica / datos; frontend: vistas / servicios / estado).
- **Por qué importa:** Sin separación, cada archivo hace de todo y cualquier cambio toca varios lugares a la vez.
- **Tu resultado:** **3** capa(s) detectada(s): vistas, servicios, estado _(mínimo 2 capas (a partir de 150 LOC))_

### 6. Acceso a datos dentro del componente (HTTP) — OK

- **Qué mide:** Llamadas `fetch`/`axios` dentro de componentes de UI en vez de una capa de servicios/API.
- **Por qué importa:** Duplica la lógica de acceso a datos y acopla la vista al backend: un cambio de API toca muchos componentes.
- **Tu resultado:** **0** llamada(s) a la API dentro de componente(s) _(máximo 0)_

### 7. Depuración olvidada (DBG) — A REVISAR

- **Qué mide:** Mensajes de depuración olvidados (`console.log`, `print`, `debugger`).
- **Por qué importa:** Generan ruido en los registros, pueden filtrar datos y dan sensación de código sin terminar.
- **Tu resultado:** **5** mensaje(s) de depuración olvidado(s) _(máximo 0)_
- **Para investigar la causa:**
    - ¿Fue depuración que quedó al cerrar una tarea, o se usó como registro permanente?
    - ¿Hubo una revisión final antes de cerrar la issue o la entrega?
    - ¿Quién agregó cada mensaje y con qué objetivo?

### 8. Uso del tipo `any` (Any) — OK

- **Qué mide:** Uso de `any` en TypeScript, que desactiva la verificación de tipos.
- **Por qué importa:** Se pierde la ayuda del compilador justo donde los datos vienen de afuera (API, formularios).
- **Tu resultado:** **0** uso(s) de `any` _(máximo 2)_

### 9. Componente demasiado grande (BigC) — A REVISAR

- **Qué mide:** Componentes de UI muy extensos, que suelen mezclar render, estado y lógica.
- **Por qué importa:** Son difíciles de leer, probar y reutilizar, y sus cambios tienen efectos inesperados.
- **Tu resultado:** **3** componente(s) demasiado grande(s) _(máximo 1)_
- **Para investigar la causa:**
    - ¿El componente creció a medida que se agregaban requisitos, sin volver a dividirlo?
    - ¿Mezcla responsabilidades distintas (mostrar, calcular, pedir datos)?
    - ¿Se dividió por pantalla o por unidad de responsabilidad?

### 10. Baja cohesión (Coh) — A REVISAR

- **Qué mide:** Una clase o unidad cuyos métodos y campos no están relacionados entre sí.
- **Por qué importa:** Una unidad que cambia por motivos distintos es frágil y cuesta entenderla.
- **Tu resultado:** **2** unidad(es) con baja cohesión _(máximo 0)_
- **Para investigar la causa:**
    - ¿La unidad agrupa cosas que en realidad pertenecen a lugares distintos?
    - ¿Cambia por motivos diferentes según la tarea?
    - ¿Se pensó su responsabilidad antes de escribirla, o se fue agregando?

### 11. Complejidad alta (Compl) — A REVISAR

- **Qué mide:** Complejidad ciclomática: cantidad de caminos posibles dentro de una función (condicionales, bucles, casos).
- **Por qué importa:** Muchos caminos = difícil de seguir y de probar; suelen esconderse casos sin cubrir.
- **Tu resultado:** **47** bloque(s) de complejidad alta _(máximo 5 por 1000 LOC (tenés 6812 LOC))_
- **Para investigar la causa:**
    - ¿Se agregaron condiciones a medida que aparecían casos nuevos?
    - ¿Se probaron todos los caminos o solo el caso principal?
    - ¿Hay reglas de negocio mezcladas con detalles técnicos?

### 12. Funciones/métodos largos o con muchos parámetros (Tam) — OK

- **Qué mide:** Tamaño de las funciones/métodos y cantidad de parámetros.
- **Por qué importa:** Una función que hace varias cosas cuesta leerla, nombrarla y reutilizarla.
- **Tu resultado:** **42** función/método(s) largos o con muchos parámetros _(máximo 10 por 1000 LOC)_

### 13. Acoplamiento alto (Acop) — A REVISAR

- **Qué mide:** Cuánto depende una unidad de las partes internas de otra.
- **Por qué importa:** Piezas muy enlazadas hacen que un cambio se propague y que sea difícil reemplazar partes.
- **Tu resultado:** **16** unidad(es) con acoplamiento alto _(máximo 2 por 1000 LOC)_
- **Para investigar la causa:**
    - ¿Las piezas se conocen en detalle entre sí (acceden a campos o estructuras internas)?
    - ¿El acceso a datos ocurre desde lugares que no son los responsables?
    - ¿Se puede cambiar una parte sin tocar las demás?

### 14. Cobertura de tests (Cob) — OK

- **Qué mide:** Porcentaje de líneas de código ejecutadas por la suite de tests (cobertura real, no cantidad de archivos de test).
- **Por qué importa:** Un test que existe pero no ejecuta el código no protege de nada: la cobertura muestra qué partes quedan sin verificar.
- **Tu resultado:** **81.0%** de líneas cubiertas _(mínimo 80% de líneas)_

### 15. Vistas del frontend (Vistas) — OK

- **Qué mide:** Cantidad de vistas/componentes de pantalla del frontend.
- **Por qué importa:** El frontend se mide por pantallas: pocas vistas sugiere poca cobertura de la interfaz pedida.
- **Tu resultado:** **13** vista(s)/componente(s) _(mínimo 8)_

## 5. Qué falta para aprobar

Criterios que hoy están en rojo y qué habría que cambiar para alcanzar el nivel de aprobación (perfil `exigente`):

| Criterio | Resultado actual | Meta | Qué arreglar |
|---|---|---|---|
| Índice de calidad de servicios (indice) | índice **6/100** | mínimo 60 | Subir el índice a ≥60 corrigiendo primero las señales de más peso: duplicación, secretos, SQL y capas. |
| Secretos hardcodeados (SEC) | **1** secreto(s) hardcodeado(s) | máximo 0 | Leer credenciales de variables de entorno o del gestor de secretos y sacarlas del código; 0 casos. |
| Depuración olvidada (DBG) | **5** mensaje(s) de depuración olvidado(s) | máximo 0 | Quitar `console.log`/`print`/`debugger` del código de producción; 0 casos. |
| Componente demasiado grande (BigC) | **3** componente(s) demasiado grande(s) | máximo 1 | Dividir el componente por responsabilidad en subcomponentes; ≤1 componente grande. |
| Baja cohesión (Coh) | **2** unidad(es) con baja cohesión | máximo 0 | Separar en unidades con una sola responsabilidad; 0 clases con baja cohesión. |
| Complejidad alta (Compl) | **47** bloque(s) de complejidad alta | máximo 5 por 1000 LOC (tenés 6812 LOC) | Extraer ramas y reglas a funciones con nombre propio; ≤5 bloques por 1000 LOC. |
| Acoplamiento alto (Acop) | **16** unidad(es) con acoplamiento alto | máximo 2 por 1000 LOC | Reducir dependencias directas entre unidades; ≤2 por 1000 LOC. |

> Empezá por las señales de seguridad (**SEC**, **SQL**) y por la **duplicación**: son las que más pesan en el índice y las más rápidas de verificar a ojo.

## 6. Anexo: dónde mirar

Archivos donde el análisis encontró cada señal en rojo (sin número de línea, a propósito):

**Secretos hardcodeados (SEC)** — 1 archivo(s):
- `backend-service1/app/core/constants.py`

**Depuración olvidada (DBG)** — 1 archivo(s):
- `backend-service2/scripts/demo_engine.py`

**Componente demasiado grande (BigC)** — 3 archivo(s):
- `frontend-admin/src/components/ui.jsx`
- `frontend-admin/src/pages/DashboardPage.jsx`
- `frontend-admin/src/pages/ResetPasswordPage.jsx`

**Baja cohesión (Coh)** — 2 archivo(s):
- `backend-service1/app/core/config.py`
- `backend-service1/app/schemas/auth.py`

**Complejidad alta (Compl)** — 26 archivo(s):
- `backend-service1/app/api/v1/endpoints/banned_ips.py`
- `backend-service1/app/core/config.py`
- `backend-service1/app/core/security.py`
- `backend-service1/app/services/auth_service.py`
- `backend-service1/app/services/mail_service.py`
- `backend-service1/tests/conftest.py`
- `backend-service1/tests/test_auth_api.py`
- `backend-service1/tests/test_config_api.py`
- `backend-service1/tests/test_security.py`
- `backend-service2/app/engine.py`
- `backend-service2/app/main.py`
- `backend-service2/app/monitor.py`
- `backend-service2/app/parser.py`
- `backend-service2/app/redis_config.py`
- `backend-service2/app/tailer.py`
- `backend-service2/tests/test_engine.py`
- `backend-service2/tests/test_health.py`
- `backend-service2/tests/test_monitor.py`
- `backend-service2/tests/test_parser.py`
- `frontend-admin/src/context/AuthProvider.jsx`
- `frontend-admin/src/hooks/useBanConfig.js`
- `frontend-admin/src/pages/ForgotPasswordPage.jsx`
- `frontend-admin/src/pages/LoginPage.jsx`
- `frontend-admin/src/pages/ResetPasswordPage.jsx`
- `frontend-admin/src/pages/SetupPage.jsx`
- `frontend-admin/src/utils/validation.js`

**Acoplamiento alto (Acop)** — 12 archivo(s):
- `backend-service1/app/core/config.py`
- `backend-service1/app/schemas/auth.py`
- `backend-service1/app/schemas/config.py`
- `backend-service1/app/services/auth_service.py`
- `backend-service1/app/services/config_service.py`
- `backend-service1/app/services/mail_service.py`
- `backend-service2/app/config.py`
- `backend-service2/app/engine.py`
- `backend-service2/app/models.py`
- `backend-service2/app/monitor.py`
- `backend-service2/app/redis_config.py`
- `backend-service2/app/tailer.py`

---
_Informe generado por la cátedra. Los umbrales corresponden al perfil `exigente`. Ante dudas, revisá el archivo señalado y el criterio en `CRITERIOS-CALIDAD.md`._
<!-- evaluacion:fin -->
