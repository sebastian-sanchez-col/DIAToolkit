# Arquitectura del Sistema

Este documento describe cómo están organizados los componentes de **DIAToolkit**, cómo fluyen
los datos desde las fuentes crudas hasta el dashboard/chatbot, y qué decisiones de diseño
sustentan esa organización. Es el complemento técnico de
[`marco_metodologico.md`](marco_metodologico.md) (que explica el *proceso*, CRISP-ML(Q) +
Scrum) y de [`diccionario_datos.md`](diccionario_datos.md) (que explica las *variables*).

> 📎 El diagrama visual de referencia (`documentation/arquitectura_sistema.png`, mencionado en
> el README) aún no ha sido generado como imagen; este documento cubre esa misma información en
> formato texto/diagrama Mermaid mientras se produce esa versión gráfica.

## 1. Visión general por capas

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. FUENTES                                                         │
│     datos.gov.co → 7 fuentes / 10 archivos CSV (ver fuentes_datos.md)│
└──────────────────────────────┬────────────────────────────────────--┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  2. INGESTA (datos_gov_api.py)                                       │
│     Solo inversión (4 fichas): API Socrata → fallback CSV local      │
│     Las otras 6 fuentes: CSV local directo (load_raw_datasets)       │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│  3. LIMPIEZA Y CALIDAD (data_processor.py)                            │
│     Normalización · Deduplicación · Filtro geográfico · Scorecard    │
│     de calidad (6 dimensiones) · Auditoría de nulos/duplicados       │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                ┌──────────────┴───────────────┐
                │                               │
┌───────────────▼──────────────┐   ┌────────────▼────────────────────┐
│ master_matrix (display)      │   │ master_matrix_panel (training)  │
│ 1 fila x comuna (21 filas)   │   │ 1 fila x comuna x año (N mayor) │
└───────────────┬──────────────┘   └────────────┬─────────────────--─┘
                │                               │
┌───────────────▼───────────────────────────────▼──────────────────────┐
│  4. MODELADO (model_trainer.py)                                       │
│     KMeans (clusters de vulnerabilidad) · Random Forest (inversión)  │
│     Validación GroupKFold por comuna · Diagnóstico PDP de estrato    │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│  5. APLICACIÓN (app.py — Flask)                                       │
│     GET  /          → dashboard.html (tabla, gráfico, insights IA)    │
│     POST /simulate  → predicción puntual del Random Forest           │
│     POST /chat      → get_assistant_response (chatbot_nlp.py)        │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│  6. INTERFAZ (templates/dashboard.html)                               │
│     Tabla por comuna · Gráfico de barras · Simulador · Chat en vivo  │
└────────────────────────────────────────────────────────────────────--┘
```

## 2. Responsabilidad de cada módulo

| Módulo | Responsabilidad | No hace |
|---|---|---|
| `datos_gov_api.py` | Consulta la API REST (Socrata) paginada por `$limit`/`$offset`; si falla, delega en el CSV local (`load_investment_year_with_api_fallback`) | No limpia ni transforma datos; solo los obtiene crudos |
| `data_processor.py` | Carga, limpia, normaliza, deduplica, filtra geográficamente, calcula el scorecard de calidad y construye las dos matrices finales (`master_matrix`, `master_matrix_panel`) | No entrena modelos ni sirve HTTP |
| `model_trainer.py` | Clustering (KMeans) sobre `master_matrix`; entrenamiento y validación (GroupKFold, PDP) del Random Forest sobre `master_matrix_panel` | No conoce el origen de los datos crudos, solo consume las matrices ya construidas |
| `chatbot_nlp.py` | Clasifica intención (TF-IDF + Logistic Regression) y arma la respuesta en lenguaje natural con gobernanza de fuente/fecha | No accede a los CSV crudos; solo recibe `df_master`, `ai_insights` y `city_level_metrics` ya calculados |
| `app.py` | Orquesta el arranque (`run_pipeline`), expone las rutas Flask, calcula el rango de años de simulación | No implementa lógica de negocio de limpieza ni de modelado; delega en los otros tres módulos |
| `templates/dashboard.html` | Renderiza tabla, gráfico, formulario de simulación y widget de chat | No contiene lógica de cálculo; consume lo que `app.py` le inyecta en el render |

## 3. Flujo de datos en detalle (arranque de la aplicación)

El arranque de `app.py` ejecuta `run_pipeline()` una única vez, de forma síncrona, **antes** de
que Flask empiece a aceptar peticiones (`df_master, ai_insights, trained_rf, city_level_metrics
= run_pipeline()` a nivel de módulo). Esto significa:

1. `process_and_create_master_matrix()` (en `data_processor.py`) ejecuta, en este orden:
   - `load_raw_datasets()` — lee las 6 fuentes que no tienen integración API.
   - `load_investment_multiyear()` — para cada año 2015-2018, intenta la API Socrata
     (`load_investment_year_with_api_fallback`) y cae a CSV local si falla.
   - Filtro geográfico a Medellín (`filter_to_medellin`, o whitelist de prestador para aseo).
   - Limpieza de estratos, deduplicación por periodo (`diagnostic_and_dedupe_by_period`).
   - `build_quality_scorecard()` — 4 dimensiones medidas + consistencia derivada.
   - Limpieza numérica robusta (`robust_numeric_clean`), detección de outliers y de fuentes
     duplicadas (EPM servicios vs. directos).
   - Ensamblaje de `master_matrix` (1 fila/comuna) y `master_matrix_panel` (1 fila/comuna/año).
2. `train_advanced_models()` (en `model_trainer.py`) recibe ambas matrices:
   - Clustering de vulnerabilidad sobre `master_matrix` (display).
   - Entrenamiento + validación GroupKFold + PDP del Random Forest sobre `master_matrix_panel`.
3. `app.py` guarda los resultados (`df_master`, `ai_insights`, `trained_rf`,
   `city_level_metrics`) como **estado global en memoria** del proceso Flask.
4. Cada petición HTTP (`/`, `/simulate`, `/chat`) lee ese estado ya calculado; **no se vuelve a
   ejecutar el pipeline por petición**.

### Implicación de diseño importante

Como el pipeline corre una sola vez al arrancar el proceso, **reiniciar la app es la única
forma de recalcular todo** (por ejemplo, si cambian los CSV en `sources/`). No existe hoy un
endpoint de refresco ni un job programado — es una limitación de arquitectura documentada
también en [`conclusiones.md`](conclusiones.md).

## 4. Por qué dos matrices (`master_matrix` vs. `master_matrix_panel`)

Esta separación no es accidental, está documentada explícitamente en el docstring de
`train_advanced_models`:

- **`master_matrix` (display):** una fila por comuna/corregimiento (21 filas). Es lo que ve el
  dashboard y el chatbot. No tiene columna `year`, porque para mostrarle una cifra a un
  ciudadano no tiene sentido repetir 4 filas por comuna.
- **`master_matrix_panel` (training):** una fila por comuna × año. Es lo que entrena el Random
  Forest, porque el modelo necesita `year` como feature (tendencia temporal) y se beneficia de
  un N más alto (21 comunas × 4 años en vez de 21 filas).

Mezclar ambas estructuras produciría una fuga conceptual: entrenar con una fila por comuna
perdería la variable temporal; mostrar en el dashboard una fila por comuna-año duplicaría
visualmente cada territorio.

## 5. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend / servidor | Python 3, Flask |
| Procesamiento de datos | pandas, numpy |
| Modelado | scikit-learn (`RandomForestRegressor`, `KMeans`, `StandardScaler`, `GroupKFold`, `partial_dependence`) |
| NLP del chatbot | scikit-learn (`TfidfVectorizer`, `LogisticRegression`) |
| Ingesta externa | `requests` contra la API Socrata de datos.gov.co |
| Frontend | `templates/dashboard.html` (Flask/Jinja2) |

## 6. Decisiones de diseño relevantes

- **GroupKFold por `commune_clean` en vez de `train_test_split` aleatorio:** con un N tan bajo
  (21 comunas), un split aleatorio dejaría la misma comuna en train y test en años distintos,
  inflando artificialmente el R². Agrupar por comuna mide generalización real a territorio no
  visto (ver `validate_model_with_group_kfold` en `model_trainer.py`).
- **Modelo final entrenado sobre el 100% de los datos:** la validación GroupKFold se usa para
  *medir* qué tan bien generaliza el enfoque, no para seleccionar el modelo final que se sirve
  en producción — una vez validado el enfoque, se reentrena con todos los datos disponibles
  para maximizar la información que usa el simulador.
- **Detección activa de duplicados y desalineación temporal antes de sumar fuentes:** en vez de
  sumar ciegamente "EPM servicios" + "EPM directos" + "Aseo", el pipeline verifica primero si
  son la misma fuente republicada (`diagnostic_check_duplicate_subsidy_sources`) y si miden el
  mismo periodo (`_check_subsidies_temporal_alignment`) antes de presentar un total combinado.
- **Fallback API → CSV explícito y no silencioso:** cada carga de inversión imprime en consola
  cuál fue el origen real de los datos (`[FUENTE INVERSIÓN {year}] Origen de los datos: ...`),
  para que un fallo de red no pase desapercibido como si fuera dato fresco de la API.

## 7. Limitaciones arquitectónicas conocidas

- El modelo Random Forest **no se persiste en disco** (no hay carpeta `models/` con `.pkl`):
  se reentrena en memoria cada vez que arranca el proceso Flask. Esto es aceptable para el
  alcance actual (N pequeño, entrenamiento rápido), pero no escala si el pipeline crece.
- No existe **cacheo** de las respuestas del chatbot ni de las consultas a la API Socrata.
- No hay **contenedor Docker** ni despliegue público todavía (ver estado en el `README.md`
  principal, sección "Solución en producción").
- No hay **suite de pruebas automatizadas** (`tests/`) ni pipeline de CI que valide drift de
  datos en cada cambio, a diferencia de proyectos de referencia similares (ver
  `.github/workflows/mlops-pipeline.yml` en el ejemplo de Seguridad Vial usado como benchmark
  de nivel Intermedio).

## 8. Extensibilidad

El diseño de `find_column()` (matching flexible de nombres de columna, tolerante a acentos y
mayúsculas) y de `clean_commune_name()` (matching por palabra clave, no por texto exacto) hace
que el pipeline tolere cambios menores de esquema en las fuentes de datos.gov.co sin romperse.
En teoría, extender el proyecto a otro municipio de Antioquia requeriría:

1. Reemplazar `MEDELLIN_TERRITORIES` y `_COMMUNE_KEYWORDS` por el listado de comunas/barrios del
   nuevo municipio.
2. Ajustar `filter_to_medellin()` (hoy hace match de texto `"MEDELL"`) al nuevo nombre.
3. Verificar que las 7 fuentes originales tengan equivalentes publicados para ese municipio en
   datos.gov.co — no se puede asumir automáticamente.