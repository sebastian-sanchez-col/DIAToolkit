# Planteamiento del Problema

## Título del proyecto

**DIAToolkit — Distributional Impact Analysis: Toolkit**
Simulador de Impacto Presupuestal: IA + Datos Abiertos para apoyar decisiones de inversión
pública en Medellín.

## Problema abordado

La información sobre inversión pública territorial en Medellín existe en datos abiertos, pero
está **dispersa en múltiples fuentes**, cada una con su propio formato, periodicidad y nivel de
cobertura geográfica. Esto impide responder con evidencia una pregunta central:

> **¿La ciudad invierte más donde más se necesita?**

Concretamente, hoy no es fácil para un ciudadano o un funcionario:

- Cruzar la inversión histórica por comuna con indicadores de vulnerabilidad social
  (afiliación a régimen subsidiado de salud, beneficiarios de programas de inclusión/
  discapacidad, estrato socioeconómico).
- Detectar si dos fuentes oficiales están, sin saberlo, duplicando el mismo dato (como ocurre
  con los subsidios "EPM servicios" y "EPM directos", ver
  [`conclusiones.md`](conclusiones.md)).
- Saber si los datos que está consultando ya están desactualizados antes de tomar una decisión
  con ellos.
- Simular un escenario presupuestal futuro sin depender de un análisis manual ad-hoc.

## Necesidad pública / institucional

- **Ciudadanía:** acceso democratizado a información presupuestal — cualquier persona puede
  consultar y entender cómo se invierten los recursos públicos en su comuna, en lenguaje
  natural, sin depender de conocimientos técnicos.
- **Administración pública:** una herramienta de apoyo a la decisión basada en evidencia
  objetiva, que reduce la dependencia de análisis manuales y subjetivos.

## Objetivo

Construir una plataforma basada en IA que integre datos abiertos para:

1. Clasificar la vulnerabilidad socioeconómica de cada comuna/corregimiento.
2. Simular la inversión pública esperada dado un escenario demográfico hipotético.
3. Facilitar consultas ciudadanas en lenguaje natural sobre inversión, subsidios y estrato,
   siempre citando la fuente y la fecha del dato.

## Justificación (valor público)

| Dimensión | Aporte |
|---|---|
| **Social** | Facilita el control ciudadano sobre la equidad territorial de la inversión pública. |
| **Institucional** | Ofrece a planeadores municipales un simulador prescriptivo basado en datos históricos reales, no en supuestos. |
| **Transparencia** | Toda cifra mostrada por el chatbot o el dashboard cita su fuente, su fecha de corte y — cuando aplica — advierte si el dato está desactualizado (ver `compute_timeliness` en `data_processor.py`). |
| **Escalabilidad** | El pipeline (`data_processor.py`) tolera cambios de esquema en las fuentes (matching flexible de columnas, normalización de comunas, deduplicación por periodo) y podría extenderse a otros municipios con datasets de estructura similar en datos.gov.co. |

## Alcance declarado (nivel Intermedio)

- 7 fuentes de datos distintas (≥ 3 requeridas), repartidas en 10 archivos CSV.
- ~15 variables analíticas (dentro del rango 10-20 exigido para nivel Intermedio).
- Modelos Random Forest + KMeans, con limpieza/transformación/integración real de múltiples
  fuentes (no solo un dataset trivial).

Ver el detalle de datasets en [`fuentes_datos.md`](fuentes_datos.md) y de variables en
[`diccionario_datos.md`](diccionario_datos.md).