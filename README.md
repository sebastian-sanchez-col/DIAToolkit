# DIAToolkit

**Distributional Impact Analysis: Toolkit**

Aplicación Flask desarrollada para el **Concurso Datos al Ecosistema 2026: IA para Colombia**, dentro de la categoría **Innovación y Tecnología** — Reto 7: *"Diseñar asistentes virtuales que faciliten el acceso ciudadano a datos abiertos"*.

Integra 10 archivos CSV correspondientes a 7 fuentes de datos abiertos distintas de [datos.gov.co](https://www.datos.gov.co) sobre inversión territorial y subsidios sociales en Medellín (la inversión territorial se publica en 4 fichas separadas, una por año 2015-2018), aplica un pipeline de limpieza/auditoría de datos documentado en consola, entrena un modelo predictivo (Random Forest) de inversión por comuna, y expone un dashboard interactivo con un simulador de escenarios y un asistente conversacional (chatbot NLP) que responde preguntas ciudadanas sobre los datos.

## Cumplimiento con la convocatoria

| Requisito | Estado                                                                                                                                                                                                  |
|---|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Categoría | Innovación y Tecnología                                                                                                                                                                                 |
| Reto | Reto 7 — Asistente virtual de acceso ciudadano a datos abiertos                                                                                                                                         |
| Nivel de complejidad (autodeclarado) | **Intermedio** — 7 fuentes de datos (≥3) repartidas en 10 archivos, ~15 variables analíticas (10-20), modelos Random Forest + KMeans, con limpieza/transformación/integración real de múltiples fuentes |
| Componente de IA | ✅ Analítica predictiva (Random Forest), simulación de escenarios (simulador con variable de año proyectado), agente conversacional con clasificación de intención (TF-IDF + Logistic Regression)        |
| Uso de datos abiertos | ✅ 7 fuentes de datos.gov.co (10 archivos CSV) — ver tabla en [Fuentes de datos](#fuentes-de-datos)                                                                                                      |
| Metodología documentada | ✅ Ver [Metodología (CRISP-ML)](#metodología-crisp-ml)                                                                                                                                                   |
| Historias de usuario y backlog (Scrum) | ✅ Ver [`BACKLOG.md`](./BACKLOG.md) — 25 historias en 10 épicas, 6 sprints                                                                                                                               |

## Project Team

| Name               | Role         | Líder de equipo |
|--------------------|--------------|:---------------:|
| Sonia Gonzalez     | Data science |                 |
| Juan Felipe Jurado | Data science |                 |
| Sebastian Sanchez  | Developer    |      Lider      |


### Responsibilities

* **Data science:** Limpieza y normalización de datos (`data_processor.py`), diagnósticos de calidad, entrenamiento y validación del modelo (`model_trainer.py`).
* **Developer:** Arquitectura de la aplicación Flask (`app.py`), dashboard (`templates/dashboard.html`), chatbot NLP (`chatbot_nlp.py`), documentación y mantenimiento.

## Impacto esperado

El proyecto busca aportar a la **transparencia y gobernanza de la inversión pública territorial** en Medellín: permite a cualquier ciudadano o funcionario consultar, en lenguaje natural, cómo se ha distribuido la inversión por comuna frente a indicadores de vulnerabilidad social (afiliación a régimen subsidiado de salud, beneficiarios de programas de inclusión/discapacidad, estrato socioeconómico), y simular escenarios presupuestales futuros bajo distintas condiciones demográficas.

Impacto potencial:
* **Social:** facilita el control ciudadano sobre la equidad territorial de la inversión pública.
* **Institucional:** ofrece a planeadores municipales un simulador prescriptivo basado en datos históricos reales, no en supuestos.
* **Escalabilidad:** la arquitectura del pipeline (`data_processor.py`) está diseñada para tolerar cambios de esquema en las fuentes (matching flexible de columnas, normalización de comunas, deduplicación por periodo) y podría extenderse a otros municipios con datasets de estructura similar en datos.gov.co.

## Features

* Pipeline de ingesta y limpieza de 10 archivos CSV (7 fuentes reales: inversión multi-año 2015-2018, subsidios EPM servicios y directos, aseo, régimen subsidiado de salud, inclusión/discapacidad, becas)
* Auditoría automática en consola: detección de comunas sin match, duplicados de fuente, artefactos de formato (Excel %), desalineación temporal entre subsidios, etc.
* Modelo predictivo (Random Forest) validado con GroupKFold por comuna, para medir generalización real a territorio no visto
* Diagnóstico de dependencia parcial (PDP) para detectar relaciones no monotónicas o extrapolaciones poco confiables
* Dashboard con gráficos (Chart.js), tabla maestra por comuna, y simulador interactivo de inversión (incluye variable de año proyectado)
* Chatbot conversacional con clasificación de intención (TF-IDF + Logistic Regression)

## Metodología (CRISP-ML)

El desarrollo siguió el ciclo CRISP-ML(Q):

1. **Business Understanding:** identificar si la inversión territorial en Medellín responde a criterios de vulnerabilidad socioeconómica medibles, y ofrecer una herramienta ciudadana para consultarlo.
2. **Data Understanding:** exploración inicial de los 7 datasets (`print_column_names()` en `data_processor.py`), documentando cobertura geográfica real, formatos y calidad de cada fuente.
3. **Data Preparation:** normalización de nombres de comuna, limpieza de formatos numéricos (separadores decimales, artefactos de exportación Excel), deduplicación por periodo, filtrado geográfico verificado — todo con diagnósticos impresos en consola para trazabilidad.
4. **Modeling:** Random Forest Regressor para la inversión territorial; KMeans para clustering de vulnerabilidad; TF-IDF + Logistic Regression para clasificación de intención del chatbot.
5. **Evaluation:** validación GroupKFold agrupada por comuna (para medir generalización real a territorio no visto, no solo a años no vistos de la misma comuna) y diagnóstico de dependencia parcial (PDP) para detectar relaciones espurias o inestables por bajo N.
6. **Deployment:** aplicación Flask con dashboard interactivo, simulador y chatbot, ejecutable localmente (`python app.py`).
7. **Monitoring:** el pipeline reimprime todos los diagnósticos de calidad en cada arranque (`[DIAGNÓSTICO ...]`, `[ALERTA ...]`), funcionando como un chequeo de salud de los datos cada vez que cambian las fuentes.

## Historias de Usuario y Backlog (Metodología Scrum)

Siguiendo la metodología Scrum enseñada en la capacitación correspondiente,
el proyecto documenta su alcance como un backlog de historias de usuario con
formato estándar (`Como / quiero / para`) y criterios de aceptación
verificables, organizado en épicas y sprints.

Ver el detalle completo en [`BACKLOG.md`](./BACKLOG.md) — 25 historias de
usuario distribuidas en 10 épicas (inversión territorial, subsidios, salud,
inclusión social, becas, modelo predictivo, chatbot, calidad de datos,
consumo de APIs y dashboard) y un plan de 6 sprints.

## Fuentes de datos

Todos los datasets provienen de [datos.gov.co](https://www.datos.gov.co). En total son **7 fuentes 
de datos distintas**, cargadas desde **10 archivos CSV** locales en `sources/`; la inversión territorial 
es la única fuente publicada en más de una ficha (una por año, 2015 a 2018).

**Consumo de API:** solo la inversión territorial (4 fichas, 2015-2018) consulta primero la API REST 
de datos.gov.co (Socrata), con respaldo automático en el CSV local si la API falla (`datos_gov_api.py`, 
`load_investment_year_with_api_fallback`). Las otras 6 fuentes (becas, EPM servicios, régimen 
subsidiado, aseo, inclusión/discapacidad y EPM directos) se leen **únicamente desde CSV local**; 
no tienen integración con la API todavía. Esto se documenta como limitación conocida del alcance 
actual (Sprint 2), no como funcionalidad ya cubierta.

| Dataset | Archivo local | Ficha en datos.gov.co |
|---|---|---|
| Inversión por comunas y corregimientos 2015 | `sources/inversion_por_comunas_y_corregimientos_2015_medellin.csv` | [Inversión por comuna y corregimiento Medellín 2015](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2015/2enc-enmu/about_data) |
| Inversión por comunas y corregimientos 2016 | `sources/inversion_por_comunas_y_corregimientos_2016_medellin.csv` | [Inversión por comuna y corregimiento Medellín 2016](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2016/3y4s-qt57/about_data) |
| Inversión por comunas y corregimientos 2017 | `sources/inversion_por_comunas_y_corregimientos_2017_medellin.csv` | [Inversión por comuna y corregimiento Medellín 2017](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2017/3e4c-pzjq/about_data) |
| Inversión por comunas y corregimientos 2018 | `sources/inversion_por_comunas_y_corregimientos_2018.csv` | [Inversión por comuna y corregimiento Medellín 2018](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2018/uyrj-ehja) |
| Beneficiarios de becas y créditos educación superior (Antioquia) | `sources/becas_creditos_educacion_superior_antioquia.csv` ⚠️ *renombrar tras descargar — ver nota abajo* | [Beneficiarios de becas y créditos de programas de acceso a la educación superior de Antioquia](https://www.datos.gov.co/Educaci-n/Beneficiaros-de-becas-y-creditos-de-programas-de-a/ya7f-466y/about_data) |
| Subsidios y Contribuciones EPM (servicios públicos) | `sources/subsidios_contribuciones_epm_servicios.csv` ⚠️ *renombrar tras descargar — ver nota abajo* | [Subsidios y Contribuciones de Servicios Públicos Domiciliarios – EPM](https://www.datos.gov.co/Minas-y-Energ-a/Subsidios-y-Contribuciones-de-Servicios-P-blicos-D/av6t-m6ju/about_data) |
| Régimen subsidiado (salud) | `sources/subsidiado.csv` | [Afiliados al régimen subsidiado de Medellín](https://www.datos.gov.co/en/dataset/Afiliados-al-r-gimen-subsidiado-de-Medell-n/n7qb-ahpa/about_data) |
| Subsidios y Contribuciones Aseo | `sources/subsidios_y_contribuciones_aseo.csv` | [Subsidios y contribuciones aseo](https://www.datos.gov.co/dataset/Subsidios-y-contribuciones-aseo/db2v-e8wa/about_data) |
| Implementación de acciones de inclusión/discapacidad | `sources/implementacion_acciones_personas_discapacidad_...csv` | [Implementación de acciones de inclusión social para personas con discapacidad](https://www.datos.gov.co/dataset/Implementaci-n-de-acciones-de-inclusi-n-social-par/hdjq-kape/about_data) |
| Subsidios y Contribuciones EPM (directos) | `sources/subsidio_contribuciones_epm.csv` | [Subsidios y Contribuciones EPM Energía Gas Acueducto](https://www.datos.gov.co/dataset/Subsidios-y-Contribuciones-EPM-Energ-a-Gas-Acueduc/dag3-4sey/about_data) |

⚠️ **Nota sobre nombres con fecha de exportación:** los archivos de "Beneficiarios de becas y 
créditos" y "Subsidios y Contribuciones EPM (servicios públicos)" se exportan desde datos.gov.co 
con la fecha de descarga incluida en el nombre (ej. `..._20260708.csv`). Ese sufijo cambia según 
el día en que descargues el archivo, por lo que **no** coincidirá con el nombre fijo que espera 
`load_raw_datasets()` en `data_processor.py`. Debes renombrar el archivo descargado al nombre 
estable indicado en la tabla (`becas_creditos_educacion_superior_antioquia.csv` y 
`subsidios_contribuciones_epm_servicios.csv`, respectivamente) antes de colocarlo en `sources/`, 
o actualizar `load_raw_datasets()` para que apunte al nombre real que descargaste.
## Variables analíticas del proyecto

El proyecto integra 15 variables analíticas derivadas de las 7 fuentes de datos, dentro del
rango exigido para el nivel de complejidad **Intermedio** (10-20 variables). Se agrupan en tres
niveles según dónde se usan:

**Features del modelo predictivo (Random Forest, `MODEL_FEATURE_COLUMNS`)** — 4 variables:
| Variable | Descripción |
|---|---|
| `health_affiliates_share` | Participación relativa de la comuna en afiliados al régimen subsidiado de salud |
| `inclusion_share` | Participación relativa de la comuna en beneficiarios de inclusión/discapacidad |
| `mean_utility_stratum` | Estrato socioeconómico promedio de la comuna |
| `year` | Año de la observación (tendencia temporal 2015-2018) |

**Variables territoriales de la matriz maestra (dashboard/chatbot, 1 fila por comuna)** — 7 variables:
| Variable | Descripción |
|---|---|
| `avg_annual_investment` | Inversión pública promedio anual de la comuna (2015-2018) |
| `n_years_with_data` | Número de años con inversión registrada para la comuna |
| `total_subsidized_health_affiliates` | Total de afiliados al régimen subsidiado en la comuna |
| `mean_health_age` | Edad promedio de los afiliados al régimen subsidiado |
| `total_disabled_and_inclusion_beneficiaries` | Total de beneficiarios de programas de inclusión/discapacidad |
| `mean_inclusion_age` | Edad promedio de ingreso a esos programas |
| `vulnerability_cluster` | Clúster de vulnerabilidad (KMeans, Alto/Medio/Bajo) derivado de las variables anteriores |

**Métricas agregadas a nivel de ciudad (`city_level_metrics`, consultables vía chatbot)** — 4 variables:
| Variable | Descripción |
|---|---|
| `total_epm_utility_subsidy_medellin` | Subsidio neto EPM (servicios públicos) para Medellín |
| `total_cleaning_subsidy_medellin` | Subsidio total de aseo para Medellín |
| `total_cleaning_subscribers_medellin` | Suscriptores subsidiados de aseo en Medellín |
| `total_scholarship_beneficiaries_medellin` | Beneficiarios de becas/créditos educativos en Medellín |

(`total_epm_direct_subsidy_medellin` no se cuenta aparte por ser un duplicado confirmado de
`total_epm_utility_subsidy_medellin`; ver nota metodológica correspondiente.)


## Requirements

* Python 3.9+
* pip

## Installation

1. Clonar el repositorio:

```bash
git clone https://github.com/sebastian-sanchez-col/DIAToolkit.git
cd DIAToolkit
```

2. Crear y activar un entorno virtual:

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```
4. Descargar las fuentes de datos:

   Este proyecto **no incluye los archivos CSV** de origen (no se versionan por tamaño).
   Antes de ejecutar la aplicación debes:

   - Crear una carpeta llamada `sources/` en la raíz del proyecto (si no existe).
   - Descargar cada uno de los 10 archivos CSV listados en la tabla
     [Fuentes de datos](#fuentes-de-datos) desde su ficha en datos.gov.co.
   - Guardarlos dentro de `sources/` usando **exactamente** el nombre de archivo
     indicado en esa tabla (los nombres deben coincidir con `INVESTMENT_FILES_BY_YEAR`
     y `load_raw_datasets()` en `data_processor.py`).
   - ⚠️ Para "Beneficiarios de becas y créditos" y "Subsidios y Contribuciones EPM
     (servicios públicos)": el archivo exportado desde datos.gov.co trae la fecha de
     descarga en el nombre (ej. `..._20260708.csv`). Renómbralo al nombre estable
     indicado en la tabla antes de colocarlo en `sources/`, o el pipeline no lo
     encontrará.
   

   Sin este paso, `python app.py` lanzará `FileNotFoundError` al arrancar.

## Running the Application

```bash
python app.py
```

La aplicación quedará disponible en:

```text
http://127.0.0.1:5000
```

Al arrancar, la consola imprime el log completo del pipeline: carga de datos, diagnósticos de calidad, entrenamiento del modelo y métricas de validación. Revisar ese log es la forma más rápida de detectar si algún dataset cambió de estructura.

## Endpoints

| Method | Endpoint     | Description                                                        |
| ------ | ------------ | ------------------------------------------------------------------ |
| GET    | `/`          | Dashboard principal (tabla, gráficos, panel de simulación, chat)   |
| POST   | `/simulate`  | Recibe variables del simulador y devuelve la inversión predicha    |
| POST   | `/chat`      | Recibe un mensaje de texto y devuelve la respuesta del chatbot NLP |

### `/simulate` — form-data esperado
`health_affiliates`, `stratum`, `disability_programs`, `year`

### `/chat` — JSON esperado
```json
{ "message": "¿cuál es el estrato promedio de las comunas?" }
```

## Notas metodológicas importantes

Estas decisiones están documentadas también como logs en consola durante el arranque (`[DECISIÓN METODOLÓGICA]`, `[ALERTA ...]`), pero se resumen aquí para referencia rápida:

* **Becas y créditos educativos**: el dataset es de cobertura departamental (Antioquia), no municipal. Tras filtrar por Medellín solo queda ~0.23% de las filas (N=33), una muestra insuficiente para desagregar por comuna. Se reporta únicamente como métrica agregada de ciudad (consultable vía chatbot) y se **excluye** del modelo predictivo, del análisis territorial y de las tarjetas de resumen del dashboard.
* **Subsidios EPM directos vs. servicios**: se confirmó (comparando valores fila por fila, no solo la suma) que ambas fuentes son el mismo dataset republicado dos veces en datos.gov.co. Se excluye 'EPM directos' de cualquier total combinado para no duplicar el conteo.
* **Comuna código 99 (régimen subsidiado de salud)**: una porción de las filas (~12.6% en la última corrida; ver el log [DIAGNÓSTICO CÓDIGO 99] al arrancar para el porcentaje exacto de cada corrida) tienen comuna=99, valor no documentado en la ficha técnica oficial del dataset. Se excluyen del análisis territorial por comuna pero se mantienen en las métricas agregadas de ciudad.
* **Homogeneidad temporal de subsidios**: aseo y EPM servicios no corresponden al mismo periodo (diferencia de ~972 días en la ejecución de referencia), por lo que no se suman como un total único de ciudad; se muestran desagregados con su periodo de referencia.
* **Estrato socioeconómico del modelo** (`mean_utility_stratum`): se calcula desde el dataset de inclusión/discapacidad (8,021 filas), no desde EPM (mayor cobertura de suscriptores). EPM se usa solo como valor de respaldo para comunas sin dato. Ver comentario en `_build_territorial_aggregates()` en `data_processor.py`.
* **Cobertura de la API (Socrata)**: solo se implementó para inversión territorial (4 fichas). 
  Extender el mismo patrón de `fetch_dataset_from_api` a becas, EPM servicios, régimen subsidiado, 
  aseo, inclusión/discapacidad y EPM directos queda pendiente; hoy esas 6 fuentes dependen 
  exclusivamente del CSV local en `sources/`.
* **Nombres de archivo con fecha de exportación (becas y EPM servicios)**: los archivos
  `Beneficiaros_de_becas_y_creditos_..._20260708.csv` y
  `Subsidios_y_Contribuciones_..._EPM_..._20260708.csv` incluyen la fecha en que fueron
  exportados desde datos.gov.co (`20260708`), no un identificador estable del dataset. Si
  descargas estos dos archivos hoy, el sufijo de fecha será distinto y **no coincidirá** con
  el nombre esperado por `load_raw_datasets()` en `data_processor.py`, causando
  `FileNotFoundError` al arrancar. Antes de ejecutar el proyecto, renombra ambos archivos a
  un nombre estable sin fecha (por ejemplo `becas_creditos_educacion_superior_antioquia.csv`
  y `subsidios_contribuciones_epm_servicios.csv`) y actualiza las dos líneas `pd.read_csv(...)`
  correspondientes en `load_raw_datasets()` para que apunten a esos nombres. Pendiente:
  actualizar también la tabla de "Fuentes de datos" más abajo con los nombres finales elegidos.

## Project Structure

```text
DIAToolkit/
├── app.py                 # Rutas Flask, orquesta el pipeline al arrancar
├── data_processor.py       # Carga, limpieza, auditoría y agregación de datos
├── model_trainer.py        # Entrenamiento y validación del modelo Random Forest
├── chatbot_nlp.py          # Clasificador de intención + generación de respuestas
├── requirements.txt
├── sources/                 # CSVs de entrada (no versionados / provistos aparte)
├── templates/
│   └── dashboard.html
└── README.md
```

## Reproducibilidad de los datos fuente

Los archivos CSV no se incluyen en este repositorio por su tamaño, pero son 100% reproducibles: 
descarga cada uno desde el enlace correspondiente en la tabla de "Fuentes de datos" y colócalo en 
`sources/` con el nombre exacto de archivo indicado en esa misma tabla (los nombres deben coincidir 
con `INVESTMENT_FILES_BY_YEAR` y `load_raw_datasets()` en `data_processor.py`). Sin estos 10 archivos, 
`python app.py` fallará al arrancar.

## Publicación

* Repositorio público: https://github.com/sebastian-sanchez-col/DIAToolkit.git
* Registrado en la sección de usos de datos.gov.co: https://herramientas.datos.gov.co/usos/distributional-impact-analysis-toolkit