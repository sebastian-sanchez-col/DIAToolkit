# Guía de Validación

Esta guía está dirigida a un **evaluador externo** que quiera correr DIAToolkit localmente y
verificar, por sí mismo, cada resultado que el proyecto afirma tener (scorecard de calidad,
detección de duplicados, validación del modelo, respuestas del chatbot), sin tener que confiar
únicamente en la documentación.

## 1. Requisitos previos

- Python 3.10+ instalado.
- Los **10 archivos CSV** listados en [`fuentes_datos.md`](fuentes_datos.md), descargados desde
  datos.gov.co y colocados en `sources/` con **exactamente** los nombres indicados en esa tabla
  (dos de ellos requieren renombrarse manualmente tras descargarlos, ver la nota ⚠️ en ese
  documento).
- Conexión a internet (opcional, solo si se quiere probar el consumo real de la API Socrata en
  vez del respaldo local — ver sección 2).

```bash
git clone https://github.com/sebastian-sanchez-col/DIAToolkit.git
cd DIAToolkit
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configuración de la API de datos.gov.co (Socrata)

Solo las 4 fichas de **inversión territorial** (2015-2018) consultan la API Socrata antes de
caer al CSV local (`load_investment_year_with_api_fallback` en `datos_gov_api.py`). Esto es
opcional: el proyecto funciona igual sin configurar nada, usando el respaldo local.

### 2.1 Uso sin token (por defecto)

Sin ninguna variable de entorno configurada, `datos_gov_api.py` consulta la API de forma
anónima. Socrata permite un volumen bajo de peticiones anónimas por hora; con 4 datasets y
paginación de 5000 filas, normalmente basta para una sola corrida de validación.

### 2.2 Uso con `SOCRATA_APP_TOKEN` (recomendado para evaluaciones repetidas)

Si vas a ejecutar el pipeline varias veces en poco tiempo (por ejemplo, para probar distintos
escenarios), configura un App Token gratuito de Socrata para evitar limitación por volumen:

```bash
export SOCRATA_APP_TOKEN="tu_token_aqui"   # Windows: set SOCRATA_APP_TOKEN=tu_token_aqui
python app.py
```

El token se agrega automáticamente al header `X-App-Token` de cada petición
(`REQUEST_HEADERS` en `datos_gov_api.py`). Si no se define la variable, el header simplemente
se omite y la petición se hace sin token.

### 2.3 Cómo verificar cuál fuente se usó realmente (API o CSV)

Al arrancar, la consola imprime, para cada uno de los 4 años de inversión, una línea como:

```
[FUENTE INVERSIÓN 2017] Origen de los datos: api
```
o
```
[FUENTE INVERSIÓN 2017] Origen de los datos: csv_local_fallback
```

Esto te permite confirmar si el pipeline realmente consultó la API o si cayó al respaldo local
(por ejemplo, por falta de conexión o un límite de tasa alcanzado). Si quieres **forzar** el
camino de fallback para probar que funciona, basta con desconectar la red o renombrar
temporalmente el archivo local correspondiente y observar que aparece la alerta
`[ALERTA API] Falló la consulta a ... Se usará el respaldo local en CSV si está disponible.`
seguida de `csv_local_fallback`.

## 3. Ejecutar la aplicación

```bash
python app.py
```

La consola debe mostrar, en orden, algo similar a:

```
[INFO PIPELINE] Ejecutando rutinas de agregación de datos reales desde data_processor...
Iniciando la carga de archivos CSV...
Cargando datasets de inversión multi-año (2015-2018)...
[FUENTE INVERSIÓN 2015] Origen de los datos: ...
...
🔍 INICIANDO AUDITORÍA - ESTADO DE LA PIPELINE: [...]
[CALIDAD - COMPLETITUD] ...
[CALIDAD - UNICIDAD] ...
[CALIDAD - VALIDEZ] ...
[CALIDAD - OPORTUNIDAD] ...
[DUPLICADO CONFIRMADO] 'EPM servicios' y 'EPM directos' tienen exactamente los mismos ...
[INFO PIPELINE] Ajustando modelos avanzados de Machine Learning sobre métricas de producción...
[VALIDACIÓN MODELO - GroupKFold por comuna, k=5] R² promedio = ...
[DIAGNÓSTICO PDP - Dependencia Parcial de 'mean_utility_stratum'] ...
[ÉXITO PIPELINE] Asignación de memoria completa. Pipelines completamente unificados.
[INICIO SISTEMA] Inicializando el contenedor de Flask en el puerto 5000...
```

Si en vez de esto ves un `FileNotFoundError`, revisa que los 10 archivos de `sources/` existan
con el nombre exacto esperado (sección 1).

La app queda disponible en `http://127.0.0.1:5000`.

## 4. Verificación por endpoint

### 4.1 `GET /` — Dashboard

Abre `http://127.0.0.1:5000` en el navegador. Verifica que:

- La tabla muestre las 21 comunas/corregimientos de `MEDELLIN_TERRITORIES`.
- El gráfico de barras esté ordenado de mayor a menor `avg_annual_investment`.
- Se muestre un resumen del `quality_scorecard` (ver interpretación en la sección 6).
- El control de año del simulador tenga como rango mínimo el primer año con inversión real y
  como máximo el año siguiente al último observado (`MIN_SIMULATION_YEAR` /
  `MAX_SIMULATION_YEAR` en `app.py`).

### 4.2 `POST /simulate` — Simulador prescriptivo

```bash
curl -X POST http://127.0.0.1:5000/simulate \
  -d "stratum=3" -d "health_affiliates=500" -d "disability_programs=50" -d "year=2019"
```

Respuesta esperada (formato):

```json
{
  "success": true,
  "predicted_investment": 123456789.01,
  "extrapolation_warning": null
}
```

**Prueba de la advertencia de extrapolación:** envía un `year` mayor al último año observado
más uno (por ejemplo, `year=2030`). El campo `extrapolation_warning` debe dejar de ser `null` y
explicar que el Random Forest no extrapola tendencias, solo repite el límite superior observado
(ver `HU-14` en el backlog).

**Prueba de robustez ante parámetros ausentes:** envía la petición sin ningún parámetro
(`curl -X POST http://127.0.0.1:5000/simulate`). Debe seguir devolviendo `"success": true`,
usando los valores por defecto (`request.form.get(..., default)`), sin lanzar una excepción no
controlada.

### 4.3 `POST /chat` — Chatbot conversacional

```bash
curl -X POST http://127.0.0.1:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "cual es la comuna con mayor inversion"}'
```

Respuesta esperada (formato):

```json
{"success": true, "response": "Analizando la matriz territorial: la zona con **mayor inversión promedio anual** es ..."}
```

## 5. Preguntas de prueba para el chatbot (por intención)

Usa estas preguntas para verificar que cada intención (`TRAINING_DATA` en `chatbot_nlp.py`)
responde con el contenido esperado y, cuando aplica, con el pie de página de gobernanza
(fuente + fecha):

| Intención | Pregunta de prueba | Qué verificar en la respuesta |
|---|---|---|
| `saludo` | "hola" | Mensaje de bienvenida, sin cifras |
| `inversion` | "cual es la comuna con mayor inversion" | Nombre de comuna + monto promedio 2015-2018, no un total acumulado |
| `subsidios` | "cuanto subsidio se dio en total" | Si los periodos no están alineados, cifras **desagregadas por fuente y fecha**, no un total único; nota de "neto" para EPM |
| `estrato` | "cual es el estrato promedio de las comunas" | Estrato promedio + comuna con estrato más bajo |
| `promedio` | "cual es el promedio de inversion" | Cifra de `avg_annual_investment` promedio + desglose de subsidios |
| `modelo_ml` | "cual es la variable mas importante para la ia" | Nombre **traducido** (`FEATURE_TRANSLATION`), no el nombre técnico de columna (ej. no debe responder literalmente `mean_utility_stratum`) |
| `becas` | "cuantos beneficiarios de becas hay" | Cifra a nivel de ciudad + advertencia explícita de que no se desagrega por comuna |
| *(fuera de dominio)* | "cuéntame un chiste" | Debe caer en `desconocido`, con sugerencias de preguntas válidas, no una respuesta inventada |

**Prueba de baja confianza:** envía una pregunta ambigua o con vocabulario poco frecuente en el
entrenamiedo (por ejemplo, una frase muy corta o fuera de las categorías). Si la confianza del
clasificador cae bajo 55%, la respuesta debe incluir la advertencia
`⚠️ No tengo alta certeza de haber entendido tu pregunta (confianza: NN%)` (ver `HU-17`).

## 6. Cómo interpretar el scorecard de calidad

El scorecard (`city_level_metrics['quality_scorecard']`) reporta, por cada una de las 4 fuentes
principales, hasta 6 dimensiones. Para verificarlo manualmente:

- **Completitud:** cuenta en el CSV crudo cuántas filas tienen **todas** las columnas
  obligatorias diligenciadas y compara contra el porcentaje impreso en consola
  (`[CALIDAD - COMPLETITUD]`).
- **Unicidad:** revisa si el dataset tiene una llave de negocio real (por ejemplo,
  `consecutivo` en régimen subsidiado); si no la tiene, el scorecard debe reportar `None` con
  una nota explicando por qué se omite, no un valor inventado.
- **Validez:** para régimen subsidiado, confirma que el porcentaje reportado corresponde a la
  proporción de filas con `0 <= edad <= 105`.
- **Oportunidad (Timeliness):** confirma que la antigüedad reportada en días coincide con la
  diferencia entre la fecha de hoy y el periodo más reciente de cada fuente. Con los datos
  actuales (inversión hasta 2018), esta antigüedad debe superar ampliamente el umbral de alerta
  de `TIMELINESS_STALE_DAYS_WARNING` (730 días ≈ 2 años).
- **Consistencia:** debe estar presente solo para "Subsidios EPM servicios" y "Subsidios Aseo",
  derivada de dos señales ya calculadas (alineación temporal + detección de duplicado EPM), no
  de una métrica nueva sin sustento.
- **Exactitud:** debe aparecer documentada como **no medible** (limitación conocida por falta
  de fuente de verdad externa), nunca como `0%` sin explicación.

## 7. Cómo interpretar la validación del modelo

En la consola, busca el bloque `[VALIDACIÓN MODELO - GroupKFold por comuna, k=N]`:

- Verifica que `k` (número de folds) no exceda el número de comunas distintas
  (`MAX_GROUPKFOLD_SPLITS = 5`, `MIN_COMMUNES_FOR_GROUPKFOLD = 5`).
- Si el R² promedio reportado es menor a `LOW_R2_WARNING_THRESHOLD` (0.3), debe aparecer la
  alerta `⚠️ ALERTA: R² promedio bajo bajo validación agrupada por comuna...` — confirma que
  esta alerta no se omite ni se suaviza en el reporte.
- En el bloque `[DIAGNÓSTICO PDP - Dependencia Parcial de 'mean_utility_stratum']`, confirma que
  el listado de valores de estrato vs. predicción promedio es coherente con el signo de la
  correlación simple reportada justo antes (`X[feature_name].corr(y)`).

## 8. Checklist de aceptación (mapeo a `BACKLOG.md`)

Para una validación exhaustiva por historia de usuario, usa los criterios de aceptación ya
definidos en [`BACKLOG.md`](../BACKLOG.md) — cada HU indica exactamente qué archivo/función
implementa el criterio y qué se espera ver en consola, en el dashboard o en la respuesta del
chatbot. Prioriza especialmente:

- **HU-04 / HU-06** (duplicado EPM y nota de "neto") — Épica 2.
- **HU-08** (comuna 99) y **HU-12** (decisión metodológica de becas) — Épica 3/5.
- **HU-14 / HU-15 / HU-16** (extrapolación, GroupKFold, PDP) — Épica 6.
- **HU-17 / HU-18** (incertidumbre del chatbot, gobernanza de fuente) — Épica 7.
- **HU-20 / HU-21** (scorecard de calidad, alerta de antigüedad) — Épica 8.

## 9. Problemas comunes al validar

| Síntoma | Causa probable | Solución |
|---|---|---|
| `FileNotFoundError` al arrancar | Falta un archivo en `sources/` o tiene un nombre distinto al esperado | Revisar la tabla de [`fuentes_datos.md`](fuentes_datos.md), especialmente los 2 archivos que requieren renombrarse |
| `Origen de los datos: csv_local_fallback` siempre, incluso con internet | Límite de tasa anónimo de Socrata alcanzado, o `dataset_id` incorrecto | Configurar `SOCRATA_APP_TOKEN` (sección 2.2) |
| El scorecard muestra `None` en "unicidad" para una fuente | Esa fuente no tiene una llave de negocio confiable definida en `key_cols` | Es el comportamiento esperado, no un error — ver sección 6 |
| El chatbot responde "desconocido" a una pregunta que debería reconocer | La frase no coincide lo suficiente con `TRAINING_DATA` en `chatbot_nlp.py` | Reformular con vocabulario más cercano a los ejemplos de esa intención, o considerar ampliar `TRAINING_DATA` |
| `/simulate` devuelve `"success": false` | Parámetro no convertible a `float`, o el modelo no está entrenado (pipeline no llegó a completarse en el arranque) | Revisar el mensaje de `error` en la respuesta JSON y los logs de arranque |