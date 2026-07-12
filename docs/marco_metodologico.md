# Marco Metodológico

El proyecto combina dos marcos complementarios: **CRISP-ML(Q)** define las
fases técnicas del ciclo de vida del modelo, mientras que **Scrum** organiza cómo el equipo
ejecutó esas fases en sprints iterativos. La presencia de uno no anula al otro; ambos se
aplican de forma simultánea.

## Metodología técnica: CRISP-ML(Q)

El desarrollo siguió el ciclo CRISP-ML(Q):

1. **Business Understanding:** identificar si la inversión territorial en Medellín responde a
   criterios de vulnerabilidad socioeconómica medibles, y ofrecer una herramienta ciudadana
   para consultarlo.
2. **Data Understanding:** exploración inicial de los 7 datasets (`print_column_names()` en
   `data_processor.py`), documentando cobertura geográfica real, formatos y calidad de cada
   fuente.
3. **Data Preparation:** normalización de nombres de comuna, limpieza de formatos numéricos
   (separadores decimales, artefactos de exportación Excel), deduplicación por periodo,
   filtrado geográfico verificado — todo con diagnósticos impresos en consola para
   trazabilidad.
4. **Modeling:** Random Forest Regressor para la inversión territorial; KMeans para clustering
   de vulnerabilidad; TF-IDF + Logistic Regression para clasificación de intención del
   chatbot.
5. **Evaluation:** validación GroupKFold agrupada por comuna (para medir generalización real a
   territorio no visto, no solo a años no vistos de la misma comuna) y diagnóstico de
   dependencia parcial (PDP) para detectar relaciones espurias o inestables por bajo N.
6. **Deployment:** aplicación Flask con dashboard interactivo, simulador y chatbot, ejecutable
   localmente (`python app.py`).
7. **Monitoring:** el pipeline reimprime todos los diagnósticos de calidad en cada arranque
   (`[DIAGNÓSTICO ...]`, `[ALERTA ...]`), funcionando como un chequeo de salud de los datos
   cada vez que cambian las fuentes.

## Gestión del proyecto: Scrum

Siguiendo la metodología Scrum, el alcance se documentó como un backlog de historias de
usuario con formato estándar (`Como <rol> / quiero <función> / para <beneficio>`) y criterios
de aceptación verificables, organizado en épicas y sprints.

Ver el detalle completo en [`BACKLOG.md`](../BACKLOG.md) — 25 historias de usuario
distribuidas en 10 épicas y un plan de 6 sprints:

| Sprint | Objetivo | Entregable |
|---|---|---|
| 1 | Ingesta y limpieza base | `data_processor.py` (carga + auditoría) |
| 2 | Calidad de datos formal + APIs | `build_quality_scorecard`, `datos_gov_api.py` |
| 3 | Modelo predictivo | `model_trainer.py` |
| 4 | Chatbot conversacional | `chatbot_nlp.py` |
| 5 | Dashboard y storytelling | `dashboard.html`, `app.py` |
| 6 | Casos de uso adicionales y cierre | Documentación final + sustentación |

## Roles del equipo

| Rol                                  | Responsable | Enfoque |
|--------------------------------------|---|---|
| Desarollador - Product Owner / líder | Sebastian Sanchez | Priorización de backlog, arquitectura Flask, dashboard, chatbot |
| Data Science                         | Sonia Gonzalez | Limpieza y normalización de datos, diagnósticos de calidad |
| Data Science                         | Juan Felipe Jurado | Entrenamiento y validación del modelo |