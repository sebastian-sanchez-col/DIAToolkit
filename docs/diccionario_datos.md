# Diccionario de Datos

Este documento describe, para cada una de las 7 fuentes, las columnas crudas que el pipeline
efectivamente consume (según `data_processor.py`), y luego las **variables analíticas
derivadas** que se construyen a partir de ellas y que alimentan el modelo, el dashboard y el
chatbot.

## 1. Columnas crudas por fuente

### Inversión por comuna y corregimiento (2015-2018)

| Columna cruda (candidatos aceptados) | Descripción | Uso en el pipeline |
|---|---|---|
| `Nombre Comuna` / `NOMBRE_COMUNA` / `Comuna` (variantes) | Nombre textual de la comuna o corregimiento | Se normaliza con `clean_commune_name()` a una de las 21 llaves estándar de `MEDELLIN_TERRITORIES` |
| `Comuna` / `Codigo Comuna` (variantes) | Código o nombre usado para descartar filas sin comuna | `dropna_col` en `load_investment_year()` |
| `Inversion` / `Valor Inversion` / `Monto` (variantes) | Monto de inversión, en la unidad reportada por la ficha (millones de pesos) | `robust_numeric_clean()` × `INVESTMENT_UNIT_MULTIPLIER_DEFAULT` (1,000,000) → `investment_value` |
| *(agregada por el pipeline)* `year` | Año de la ficha (2015, 2016, 2017 o 2018) | Se asigna según el archivo/dataset consultado, no viene en el CSV |

### Régimen subsidiado (salud) — `subsidiado.csv`

| Columna cruda | Descripción | Uso en el pipeline |
|---|---|---|
| `comuna` | Código numérico de comuna (1-16, 50-90, o 99 no documentado) | Validado contra `VALID_COMMUNE_CODES`; el código 99 se documenta como limitación conocida (ver `conclusiones.md`) |
| `edad` | Edad del afiliado | Se recorta (clip) entre 0 y 105 años para evitar valores absurdos |
| `consecutivo` | Identificador de fila | Usado como llave de conteo (`count`) para `total_subsidized_health_affiliates` y como llave de unicidad en el scorecard de calidad |

### Inclusión social y discapacidad

| Columna cruda | Descripción | Uso en el pipeline |
|---|---|---|
| `COMUNA DE RESIDENCIA` | Comuna del beneficiario | Normalizada con `clean_commune_name()` |
| `ESTRATO SOCIOECONÓMICO` | Categoría de estrato en texto (`BAJO-BAJO`, `MEDIO`, etc.) | Mapeada a número 1-6 con `map_stratum_category()` / `STRATUM_CATEGORY_TO_NUMBER` |
| `CONDICIÓN DE DISCAPACIDAD` | Tipo de condición reportada | Usada como llave de conteo para `total_disabled_and_inclusion_beneficiaries` |
| `AÑOS CUMPLIDOS AL INGRESO DEL PROGRAMA` | Edad de ingreso al programa | Promedio → `mean_inclusion_age` |

### Subsidios EPM (servicios públicos)

| Columna cruda | Descripción | Uso en el pipeline |
|---|---|---|
| `Municipio o Sector` | Ubicación geográfica (texto libre) | Filtro `filter_to_medellin()` (contiene "MEDELL") |
| `estrato` | Estrato o categoría de usuario (residencial 1-6, o Comercio/Industria/Oficial/Especial para no residenciales) | Se conserva el texto crudo en `_raw_stratum_category` antes de convertir a número, para no colapsar categorías comerciales distintas |
| `valor` | Monto del subsidio o contribución (signo negativo = subsidio, positivo = contribución) | `robust_numeric_clean()`; se documenta como cifra **neta** (ver `_net_subsidy_caveat` en `chatbot_nlp.py`) |
| `Tipo de subsidio`, `Departamento`, `servicio`, `tipo` | Categóricas usadas como llave compuesta de deduplicación | `key_columns_override` en `diagnostic_and_dedupe_by_period()` |
| `año`, `Mes` | Periodo del registro | Construye la fecha interna con `build_period_from_year_month()` |

### Subsidios EPM (directos)

Mismas columnas que "EPM servicios" pero con nombres en snake_case (`municipio_o_sector`,
`estrato`, `valor`, `tipo_de_subsidio`, `departamento`, `a_o`, `mes`, `servicio`, `tipo`).
**Ver nota importante:** se confirmó que esta fuente es un duplicado exacto de "EPM servicios"
(ver `conclusiones.md`), por lo que se excluye de los totales combinados de ciudad.

### Subsidios y Contribuciones Aseo

| Columna cruda | Descripción | Uso en el pipeline |
|---|---|---|
| `prestador` | Nombre del prestador del servicio | Usado como whitelist geográfica (`CLEANING_PROVIDERS_MEDELLIN`) cuando no hay columna geográfica real, y como llave de deduplicación |
| `periodo` | Fecha del registro (ya viene como fecha real, a diferencia de EPM) | Parseada directamente con `pd.to_datetime(..., dayfirst=True)` |
| `total_subsidio` | Monto total del subsidio | `robust_numeric_clean()` |
| `suscriptores_subsidiados` | Cantidad de suscriptores subsidiados | Convertido a entero; auditado contra `CLEANING_SUBSCRIBERS_POPULATION_REFERENCE` para detectar outliers |

### Becas y créditos educación superior (Antioquia)

| Columna cruda | Descripción | Uso en el pipeline |
|---|---|---|
| `MUNICIPIO DE RESIDENCIA` | Municipio del beneficiario (cobertura departamental, no solo Medellín) | Filtro `filter_to_medellin()`; **solo ~0.23% de las filas quedan como Medellín** (ver limitación en `conclusiones.md`) |
| `ESTRATO` | Estrato del beneficiario, en formato numérico con posible ruido de texto | `extract_leading_number()` |

## 2. Variables analíticas derivadas

### Features del modelo predictivo (Random Forest, `MODEL_FEATURE_COLUMNS`)

| Variable | Descripción | Fuente(s) crudas de origen |
|---|---|---|
| `health_affiliates_share` | Participación relativa de la comuna en afiliados al régimen subsidiado de salud | Régimen subsidiado (salud) |
| `inclusion_share` | Participación relativa de la comuna en beneficiarios de inclusión/discapacidad | Inclusión social y discapacidad |
| `mean_utility_stratum` | Estrato socioeconómico promedio de la comuna (con fallback desde EPM si falta el dato de inclusión/discapacidad) | Inclusión y discapacidad (primaria) + EPM servicios (fallback) |
| `year` | Año de la observación (tendencia temporal 2015-2018) | Inversión multi-año |

### Variables territoriales de la matriz maestra (dashboard/chatbot, 1 fila por comuna)

| Variable | Descripción |
|---|---|
| `avg_annual_investment` | Inversión pública promedio anual de la comuna (2015-2018), **incluyendo años sin inversión registrada como cero** |
| `n_years_with_data` | Número de años (de 4) en los que la comuna tuvo inversión real registrada (> 0) |
| `total_subsidized_health_affiliates` | Total de afiliados al régimen subsidiado en la comuna |
| `mean_health_age` | Edad promedio de los afiliados al régimen subsidiado |
| `total_disabled_and_inclusion_beneficiaries` | Total de beneficiarios de programas de inclusión/discapacidad |
| `mean_inclusion_age` | Edad promedio de ingreso a esos programas |
| `vulnerability_cluster` | Clúster de vulnerabilidad (KMeans, 0=Alto / 1=Medio / 2=Bajo) derivado de `health_affiliates_share`, `inclusion_share` y el estrato invertido |

### Métricas agregadas a nivel de ciudad (`city_level_metrics`, consultables vía chatbot)

| Variable | Descripción |
|---|---|
| `total_epm_utility_subsidy_medellin` | Subsidio neto EPM (servicios públicos) para Medellín |
| `total_epm_direct_subsidy_medellin` | Subsidio EPM directos (no se suma al total combinado: duplicado confirmado de la anterior) |
| `total_cleaning_subsidy_medellin` | Subsidio total de aseo para Medellín |
| `total_cleaning_subscribers_medellin` | Suscriptores subsidiados de aseo en Medellín |
| `total_scholarship_beneficiaries_medellin` | Beneficiarios de becas/créditos educativos en Medellín (solo a nivel ciudad, ver limitación de muestra) |
| `subsidies_periods_aligned` | Booleano: si las fuentes de subsidio de ciudad miden ventanas de tiempo comparables |
| `quality_scorecard` | Diccionario con las 4 dimensiones de calidad medibles (completitud, unicidad, validez, oportunidad) + consistencia derivada, por cada una de las 4 fuentes principales |

Ver el detalle de cómo se calcula cada dimensión de calidad en `build_quality_scorecard()`
dentro de `data_processor.py`, y su interpretación en [`conclusiones.md`](conclusiones.md).