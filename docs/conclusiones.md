# Conclusiones

Este documento consolida los **hallazgos clave**, su **interpretación**, las **limitaciones
conocidas** (documentadas de forma honesta, no ocultas) y el **impacto potencial** de
DIAToolkit. Es la referencia que resume, en un solo lugar, todas las alertas y notas
metodológicas que hoy están dispersas como comentarios y `print()` a lo largo de
`data_processor.py` y `model_trainer.py`.

## 1. Hallazgos clave

### 1.1 Inversión territorial (2015-2018)

- La inversión promedio anual por comuna/corregimiento (`avg_annual_investment`) muestra una
  dispersión considerable entre las 21 comunas y corregimientos de Medellín.
- Los corregimientos rurales (códigos 50-90: Palmitas, San Cristóbal, Altavista, San Antonio de
  Prado, Santa Elena) tienden a mostrar promedios de inversión **altos en términos absolutos**
  a pesar de su menor densidad poblacional. Esto **no es un error de cruce de datos**, se
  verificó fila por fila que el nombre crudo de la comuna corresponde al corregimiento correcto, 
  esto es un efecto esperado de medir inversión **total**, no *per cápita*: un solo proyecto de
  infraestructura rural (vía, acueducto veredal) cuesta un monto similar sin importar cuánta
  gente lo usa, y al haber pocos proyectos por año en esos territorios, cada uno pesa más en el
  promedio.
- **Implicación práctica:** este indicador **no debe leerse como una medida de equidad** sin
  ajustar por población. Es una limitación de interpretación, no de los datos en sí.

### 1.2 Subsidios de servicios públicos (EPM y Aseo)

- Se confirmó, comparando los valores individuales fila por fila (no solo la suma agregada),
  que **"EPM servicios" y "EPM directos" son la misma fuente republicada dos veces** en
  datos.gov.co bajo fichas distintas (`diagnostic_check_duplicate_subsidy_sources`). Sumarlas
  como si fueran programas independientes duplicaría el subsidio real.
- Las tres fuentes de subsidio de ciudad (EPM servicios, EPM directos, Aseo) **no siempre
  comparten el mismo periodo de corte**. Cuando la diferencia entre periodos supera 31 días, el
  chatbot y el dashboard presentan los montos **desagregados por fuente y fecha**, en vez de un
  total combinado potencialmente engañoso.
- La cifra de EPM es un **neto** (subsidios menos contribuciones, codificado con signo en la
  misma columna `valor`), no un subsidio bruto, toda respuesta que la menciona incluye esa
  aclaración.

### 1.3 Régimen subsidiado de salud e inclusión social

- Una fracción de los registros del régimen subsidiado tiene `comuna = 99`, un código que **no
  está documentado** en la ficha técnica oficial del dataset. No se pudo confirmar si significa
  "sin dato geográfico", "zona rural" u otra categoría, así que estas filas se excluyen del
  análisis territorial por comuna, pero sí se cuentan en las métricas agregadas de ciudad.
- El estrato socioeconómico por comuna se deriva principalmente de la fuente de
  inclusión/discapacidad; cuando falta ese dato para una comuna, se usa como respaldo el
  estrato promedio de EPM (`reference_global_stratum`), una fuente distinta, usada solo como
  aproximación, no como dato primario.

### 1.4 Becas y créditos educativos

- El dataset de becas es de cobertura **departamental** (Antioquia), no municipal. Tras
  filtrar por Medellín, la muestra que queda es una fracción muy pequeña del total original.
  **Decisión metodológica documentada:** dado ese N insuficiente, la cifra se reporta
  únicamente como métrica agregada de ciudad y se excluye del modelo predictivo y del análisis
  territorial por comuna, para no introducir conclusiones falsas basadas en muestras casi
  vacías.

### 1.5 Modelo predictivo (Random Forest)

- La validación `GroupKFold` agrupada por comuna (dejando comunas **completas** fuera del
  entrenamiento en cada fold, no solo años sueltos de la misma comuna) mide generalización real
  a territorio no visto. El reporte de consola en cada ejecución expone el R² y el MAE promedio
  por fold si el R² promedio cae bajo 0.3, el pipeline lo advierte explícitamente en vez de
  ocultarlo.
- El diagnóstico de dependencia parcial (PDP) sobre el estrato socioeconómico
  (`diagnostic_partial_dependence_stratum`) verifica si el efecto de esa variable sobre la
  predicción es monotónico o errático. Cuando aparecen tramos crecientes y decrecientes
  simultáneos, se interpreta como posible inestabilidad por N bajo o interacción compleja con
  otras variables, no como una relación causal confiable con el estrato.
- El primer tramo de la curva PDP (el extremo del rango de estrato observado) se audita aparte:
  un salto desproporcionado ahí suele indicar que hay muy pocas comunas/años observados en ese
  extremo, y se marca como zona del modelo a tratar con cautela.

## 2. Interpretación

Tomando los hallazgos anteriores en conjunto, la evidencia disponible **no permite afirmar de
forma concluyente** que la inversión pública en Medellín (2015-2018) haya seguido un criterio
explícito de vulnerabilidad socioeconómica medible con las variables actuales
(`health_affiliates_share`, `inclusion_share`, `mean_utility_stratum`). El correlograma
(`diagnostic_correlation_check`) sí muestra relaciones (positivas o negativas) entre estas
variables y la inversión total, pero:

- El N efectivo de entrenamiento es bajo (21 territorios × 4 años ≈ 84 observaciones), lo que
  limita la confianza estadística de cualquier conclusión causal.
- La inversión rural está dominada por el efecto de "proyecto único, no per cápita" descrito en
  el hallazgo 1.1, lo que puede distorsionar cualquier lectura simple de "a más vulnerabilidad,
  más/menos inversión".
- El estrato socioeconómico depende de una fuente (inclusión/discapacidad) con cobertura
  parcial, complementada con un valor de respaldo de otra fuente distinta (EPM), la variable en
  sí tiene ruido de origen que se propaga a cualquier conclusión basada en ella.

En resumen: el modelo y el dashboard son una **herramienta honesta de exploración**, no un
veredicto definitivo sobre equidad territorial. El mostrar el R² real, advertir
sobre N bajo, advertir sobre extrapolación, es en sí misma parte del valor del proyecto.

## 3. Limitaciones conocidas (documentadas, no ocultas)

| Limitación | Dónde se documenta en el código | Tratamiento |
|---|---|---|
| Dato de inversión desactualizado (última carga: 2018) | `compute_timeliness`, `TIMELINESS_STALE_DAYS_WARNING` | Se advierte si la antigüedad supera 2 años; a la fecha actual, **supera ampliamente ese umbral** (~7-8 años), por lo que toda cifra de inversión debe presentarse siempre con la advertencia de "dato histórico, no vigente" |
| Dimensión de **Exactitud** no medible | `build_quality_scorecard` | Se documenta explícitamente como limitación conocida (no existe fuente de verdad externa para comparar), no se reporta como 0% ni se oculta |
| Código `comuna = 99` sin documentar | `_restrict_health_affiliates_to_valid_communes` | Se excluye del análisis territorial, se mantiene en el agregado de ciudad, y se reporta el porcentaje afectado |
| Becas: cobertura casi vacía tras filtro geográfico | `_log_scholarship_methodology_decision` | Se reporta solo a nivel ciudad; excluida del modelo y del análisis por comuna |
| Duplicado EPM servicios / EPM directos | `diagnostic_check_duplicate_subsidy_sources` | Se excluye "EPM directos" de cualquier total combinado |
| Desalineación temporal entre fuentes de subsidio | `_check_subsidies_temporal_alignment` | Se presentan desagregadas con su fecha en vez de sumarse |
| Artefacto de exportación Excel (`%` en `total_subsidio`) | `robust_numeric_clean` | Verificado contra la fuente original; se revierte la multiplicación ×100 solo en las filas afectadas |
| N bajo para el modelo (21 comunas × 4 años) | `validate_model_with_group_kfold` | Se advierte si R² promedio < 0.3; se documenta como limitación de tamaño de muestra, no se disfraza |
| Inversión rural alta no ajustada por población | Nota metodológica en `_build_territorial_aggregates` | Se documenta para no leerse como indicador de equidad sin ajuste |
| Modelo no persiste entre reinicios | Ver [`architecture.md`](architecture.md) | Se reentrena en cada arranque; no hay versión servida en `models/*.pkl` |
| Solo 4 de 10 archivos consumen la API Socrata | `fuentes_datos.md`, HU-23 del backlog | Alcance explícito de Sprint 2; las otras 6 fuentes quedan como trabajo futuro |

## 4. Impacto potencial

| Dimensión | Aporte concreto                                                                                                                                                                                                                                                                                                      |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Social** | Permite a cualquier ciudadano preguntar, en lenguaje natural, en qué comuna se invirtió más o menos, sin depender de saber leer un CSV o un portal de datos abiertos.                                                                                                                                                |
| **Institucional** | Ofrece a un equipo de planeación un simulador prescriptivo basado en datos históricos reales, con las advertencias de confiabilidad (R², extrapolación) integradas, en vez de una cifra sin contexto.                                                                                                                |
| **Transparencia** | Cada cifra que el chatbot entrega cita su fuente y fecha de corte (`DATA_GOVERNANCE`, `_governance_footer`), y advierte cuando el dato es potencialmente engañoso (duplicado, desalineado, desactualizado).                                                                                                          |
| **Metodológico** | El scorecard de 6 dimensiones y la validación GroupKFold son prácticas replicables para cualquier equipo que integre múltiples fuentes administrativas dispares, el patrón (detectar duplicados, verificar alineación temporal, documentar lo no medible) es reutilizable más allá de Medellín.                      |
| **Riesgo si se ignoran las limitaciones** | Si el simulador se usa como si el R² fuera alto y los datos estuvieran vigentes, podría llevar a decisiones presupuestales basadas en una proyección de baja confiabilidad sobre datos de hace varios años. Este riesgo está mitigado por las advertencias explícitas, pero depende de que el usuario final las lea. |

## 5. Recomendaciones / trabajo futuro

1. **Actualizar la fuente de inversión** más allá de 2018, o migrar completamente a consumo vivo
   de la API Socrata si datos.gov.co ya publica años más recientes.
2. **Extender la integración de API** (HU-23, Sprint 2) a las 6 fuentes que hoy solo se cargan
   desde CSV local.
3. **Persistir el modelo entrenado** (`models/*.pkl`) para no reentrenar en cada arranque, y
   habilitar un endpoint de reentrenamiento explícito cuando cambien las fuentes.
4. **Agregar una métrica de inversión per cápita** además de la inversión total, para poder
   leer la equidad territorial sin el sesgo de "proyecto único" en zonas rurales.