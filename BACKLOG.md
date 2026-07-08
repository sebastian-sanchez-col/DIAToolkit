# BACKLOG.md — DIAToolkit (Reto 7, Concurso Datos al Ecosistema 2026)

Backlog documentado siguiendo la estructura estándar enseñada en la sesión
*"Metodología Scrum, Historias de Usuario y Sprint"*: cada historia sigue el
formato `Como <rol> quiero <función> para <beneficio>`, con criterios de
aceptación explícitos y sin ambigüedad técnica, en lenguaje funcional.

---

## Épica 1 — Consulta ciudadana de inversión territorial

### HU-01
**Como** ciudadano de Medellín
**quiero** preguntarle al chatbot en qué comuna se invirtió más
**para** poder evaluar si la inversión pública fue equitativa

**Criterios de aceptación:**
- Dado que el usuario escribe una pregunta sobre "mayor inversión", el chatbot
  responde con el nombre de la comuna y el monto promedio anual.
- El chatbot cita el periodo de los datos (2015-2018) y advierte su antigüedad.

### HU-02
**Como** ciudadano
**quiero** conocer la comuna con menor inversión promedio
**para** identificar posibles zonas desatendidas

**Criterios de aceptación:**
- La respuesta incluye el nombre de la comuna, el monto y la fuente.

### HU-03
**Como** ciudadano
**quiero** comparar la inversión entre dos comunas específicas
**para** entender la diferencia relativa entre ellas

**Criterios de aceptación:**
- El chatbot reconoce el nombre de ambas comunas en la pregunta y devuelve
  ambos montos junto con la diferencia porcentual.
- Si una comuna no existe en el dataset, el chatbot lo indica explícitamente
  (no inventa un valor).

### HU-04
**Como** ciudadano
**quiero** ver la evolución de la inversión de mi comuna año por año (2015-2018)
**para** saber si ha aumentado o disminuido con el tiempo

**Criterios de aceptación:**
- La tabla o gráfico muestra los 4 años disponibles, no solo el promedio.
- Si un año no tiene dato para esa comuna, se muestra como "sin dato", no como 0.

### HU-05
**Como** funcionario de planeación municipal
**quiero** exportar la matriz de inversión por comuna a un archivo descargable
**para** usarla en reportes internos fuera del dashboard

**Criterios de aceptación:**
- Existe un botón o endpoint que descarga la tabla en CSV o XLSX.

---

## Épica 2 — Subsidios de servicios públicos (EPM y Aseo)

### HU-06
**Como** ciudadano
**quiero** conocer el total de subsidios de servicios públicos otorgados en la ciudad
**para** entender el esfuerzo fiscal destinado a esta ayuda

**Criterios de aceptación:**
- Si las fuentes (EPM, Aseo) no comparten el mismo periodo, el chatbot las
  muestra desagregadas con su fecha, no como un total combinado engañoso.

### HU-07
**Como** analista de datos del equipo
**quiero** que el sistema detecte automáticamente si dos fuentes de subsidio son
la misma fuente duplicada
**para** evitar contar el mismo subsidio dos veces en los totales de ciudad

**Criterios de aceptación:**
- `diagnostic_check_duplicate_subsidy_sources` corre en cada arranque y deja
  el resultado disponible en `city_level_metrics`.

### HU-08
**Como** ciudadano
**quiero** saber cuántos suscriptores subsidiados de aseo hay en la ciudad
**para** dimensionar el alcance del programa

**Criterios de aceptación:**
- El chatbot responde con el total y advierte si algún registro individual
  supera el umbral de población de referencia (posible outlier).

### HU-09
**Como** ciudadano
**quiero** entender qué significa que la cifra de EPM sea "neta"
**para** no confundir subsidio bruto con subsidio menos contribución

**Criterios de aceptación:**
- Toda respuesta que incluya la cifra de EPM añade la nota aclaratoria
  correspondiente (`_net_subsidy_caveat`).

---

## Épica 3 — Régimen subsidiado de salud

### HU-10
**Como** ciudadano
**quiero** saber cuántos afiliados al régimen subsidiado hay por comuna
**para** relacionar vulnerabilidad en salud con inversión pública

**Criterios de aceptación:**
- El dato se muestra como participación relativa (`health_affiliates_share`),
  no como conteo absoluto, para no confundir "más gente" con "más vulnerable".

### HU-11
**Como** analista de datos
**quiero** que las filas con comuna=99 (código no documentado oficialmente)
se excluyan del análisis territorial pero se mantengan en las métricas de ciudad
**para** no perder cobertura de ciudad ni inventar una comuna falsa

**Criterios de aceptación:**
- El pipeline reporta el porcentaje de filas con comuna=99 en cada corrida.

---

## Épica 4 — Inclusión social y discapacidad

### HU-12
**Como** ciudadano
**quiero** conocer la comuna con más beneficiarios de programas de inclusión
para personas con discapacidad
**para** verificar si la oferta social llega a las zonas correctas

**Criterios de aceptación:**
- El chatbot responde con el nombre de la comuna y el total de beneficiarios.

### HU-13
**Como** analista de datos
**quiero** que el estrato promedio por comuna tenga un valor de respaldo
cuando falte el dato de inclusión/discapacidad
**para** que ninguna comuna quede sin estrato en el modelo

**Criterios de aceptación:**
- Se usa `reference_global_stratum` (derivado de EPM) como fallback, con nota
  metodológica visible en el código y en el README.

---

## Épica 5 — Becas y educación superior

### HU-14
**Como** ciudadano
**quiero** saber cuántos beneficiarios de becas y créditos hay en Medellín
**para** conocer el alcance del programa educativo

**Criterios de aceptación:**
- La cifra se presenta únicamente a nivel de ciudad, con la advertencia de que
  no se desagrega por comuna por tamaño de muestra insuficiente.

### HU-15
**Como** analista de datos
**quiero** que el sistema documente por qué las becas se excluyen del modelo
predictivo y del análisis territorial
**para** dejar trazabilidad de la decisión metodológica

**Criterios de aceptación:**
- `_log_scholarship_methodology_decision` imprime la justificación completa
  al arrancar el pipeline.

---

## Épica 6 — Simulador prescriptivo (Machine Learning)

### HU-16
**Como** funcionario de planeación
**quiero** simular la inversión estimada dado un estrato, afiliados en salud y
beneficiarios de inclusión
**para** anticipar necesidades presupuestales de una comuna hipotética

**Criterios de aceptación:**
- El endpoint `/simulate` devuelve una predicción numérica y no falla ante
  parámetros ausentes (usa valores por defecto razonables).

### HU-17
**Como** funcionario de planeación
**quiero** que el simulador me advierta si el año proyectado excede el rango
de entrenamiento
**para** no interpretar una extrapolación como una predicción confiable

**Criterios de aceptación:**
- Si `year > max_trained_year`, la consola imprime la alerta correspondiente
  (ya implementado) y el dashboard también la muestra al usuario final.

### HU-18
**Como** miembro del equipo de datos
**quiero** validar el modelo con GroupKFold agrupado por comuna
**para** medir generalización real a territorio no visto, no solo a otro año
de la misma comuna

**Criterios de aceptación:**
- El reporte de consola muestra R² y MAE promedio por fold, y advierte si el
  R² es bajo (< 0.3).

### HU-19
**Como** miembro del equipo de datos
**quiero** un diagnóstico de dependencia parcial (PDP) sobre el estrato
**para** detectar si el efecto de esa variable es monotónico o inestable por N bajo

**Criterios de aceptación:**
- `diagnostic_partial_dependence_stratum` se ejecuta en cada entrenamiento y
  reporta si hay tramos crecientes y decrecientes simultáneos.

---

## Épica 7 — Chatbot conversacional

### HU-20
**Como** ciudadano
**quiero** que el chatbot me diga cuando no está seguro de haber entendido mi
pregunta
**para** no confiar en una respuesta mal encaminada

**Criterios de aceptación:**
- Si la confianza del clasificador es menor a 55%, la respuesta incluye una
  advertencia explícita de incertidumbre (`classify_with_confidence`).

### HU-21
**Como** ciudadano
**quiero** que cada respuesta cite la fuente y la fecha de actualización del dato
**para** poder verificarlo yo mismo en datos.gov.co

**Criterios de aceptación:**
- Toda respuesta cuyo intent tenga gobernanza documentada (`DATA_GOVERNANCE`)
  incluye el pie de página con fuente, fecha y política de uso.

### HU-22
**Como** ciudadano
**quiero** preguntarle al chatbot cuál es la variable más importante del modelo
**para** entender qué explica mejor la inversión territorial

**Criterios de aceptación:**
- La respuesta usa el nombre traducido de la variable (`FEATURE_TRANSLATION`),
  no el nombre técnico de la columna.

---

## Épica 8 — Calidad y gobernanza de datos

### HU-23
**Como** miembro del equipo de datos
**quiero** un scorecard formal de las 6 dimensiones de calidad (completitud,
unicidad, validez, consistencia, exactitud, oportunidad)
**para** poder reportar objetivamente el estado de cada fuente

**Criterios de aceptación:**
- `build_quality_scorecard` corre sobre las 4 fuentes principales y queda
  disponible en `city_level_metrics['quality_scorecard']`.

### HU-24
**Como** ciudadano
**quiero** que se me advierta si estoy consultando datos desactualizados
**para** no tomar decisiones con información que ya no representa la realidad

**Criterios de aceptación:**
- `compute_timeliness` marca alerta si la antigüedad del dato supera 2 años,
  y esa alerta llega hasta el chatbot o el dashboard.

### HU-25
**Como** miembro del equipo de datos
**quiero** que la auditoría de nulos y duplicados se ejecute automáticamente
en cada arranque
**para** detectar regresiones de calidad si cambia una fuente

**Criterios de aceptación:**
- `run_data_audit_report` se ejecuta sobre todos los datasets crudos antes
  de cualquier transformación y sus resultados quedan en el log de consola.

---

## Épica 9 — Consumo de APIs y estándares de datos

### HU-26
**Como** miembro del equipo de datos
**quiero** que el pipeline consuma la API REST (Socrata) de datos.gov.co como
fuente primaria
**para** trabajar siempre con el dato más reciente publicado, no solo con una
copia local estática

**Criterios de aceptación:**
- `fetch_dataset_from_api` se invoca antes de leer el CSV local para las
  4 fichas de inversión.
- Si la API falla, el pipeline usa el CSV local automáticamente sin detenerse.

### HU-27
**Como** miembro del equipo de datos
**quiero** que las llamadas a la API sigan el estándar REST (GET, JSON,
paginación `$limit`/`$offset`)
**para** cumplir con las buenas prácticas de consumo de APIs enseñadas en la
capacitación

**Criterios de aceptación:**
- El módulo `datos_gov_api.py` documenta explícitamente el verbo HTTP, el
  formato de respuesta y el mecanismo de paginación usado.

---

## Épica 10 — Dashboard y visualización

### HU-28
**Como** ciudadano
**quiero** ver la inversión por comuna en un gráfico, no solo en una tabla
**para** identificar patrones territoriales de un vistazo

**Criterios de aceptación:**
- El gráfico de barras (`subsidiesChart`) ordena las comunas de mayor a menor
  inversión promedio.

### HU-29
**Como** ciudadano
**quiero** que el dashboard incluya una narrativa breve de "historia con datos"
(contexto → hallazgo → llamado a la acción)
**para** entender el mensaje sin tener que interpretar los gráficos por mi cuenta

**Criterios de aceptación:**
- Cada gráfico del dashboard tiene un texto introductorio de 2-3 líneas que
  explica qué se debe concluir de él, siguiendo el framework de storytelling
  con datos visto en la sesión de Power BI.

### HU-30
**Como** ciudadano
**quiero** ver el estado de calidad de los datos que sustentan el dashboard
**para** confiar (o desconfiar apropiadamente) de las cifras mostradas

**Criterios de aceptación:**
- El dashboard muestra un resumen visible de `quality_scorecard` (por ejemplo,
  un badge de "datos con X años de antigüedad").

---

## Plan de Sprints

| Sprint | Objetivo | Historias incluidas | Entregable |
|---|---|---|---|
| Sprint 1 | Ingesta y limpieza base | HU-01, HU-06, HU-10, HU-12, HU-14, HU-25 | `data_processor.py` (carga + auditoría) |
| Sprint 2 | Calidad de datos formal + APIs | HU-23, HU-24, HU-26, HU-27 | `build_quality_scorecard`, `datos_gov_api.py` |
| Sprint 3 | Modelo predictivo | HU-16, HU-17, HU-18, HU-19 | `model_trainer.py` |
| Sprint 4 | Chatbot conversacional | HU-20, HU-21, HU-22 | `chatbot_nlp.py` |
| Sprint 5 | Dashboard y storytelling | HU-02, HU-03, HU-04, HU-05, HU-28, HU-29, HU-30 | `dashboard.html`, `app.py` |
| Sprint 6 | Casos de uso adicionales y cierre | HU-07, HU-08, HU-09, HU-11, HU-13, HU-15 | Documentación final + sustentación |

**Sprint Planning:** reunión inicial por sprint para seleccionar historias del
backlog priorizadas por el equipo (Product Owner = líder del equipo).
**Daily:** seguimiento corto de avance/bloqueos entre Data Science y Developer.
**Sprint Review:** demo funcional de las historias completadas frente al
equipo, validando contra los criterios de aceptación.
**Sprint Retrospectiva:** espacio interno del equipo de desarrollo para
identificar mejoras al proceso, sin la presencia del product owner.