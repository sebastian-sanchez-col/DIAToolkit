# DIAToolkit

**Distributional Impact Analysis: Toolkit**

Aplicación Flask desarrollada para el **Concurso Datos al Ecosistema 2026: IA para Colombia**,
categoría **Innovación y Tecnología** — Reto 7: *"Diseñar asistentes virtuales que faciliten el
acceso ciudadano a datos abiertos"*.

Integra 7 fuentes de datos abiertos de [datos.gov.co](https://www.datos.gov.co) sobre inversión
territorial y subsidios sociales en Medellín, aplica un pipeline de limpieza/auditoría de datos,
entrena un modelo predictivo (Random Forest) de inversión por comuna, y expone un dashboard
interactivo con un simulador de escenarios y un chatbot conversacional.

## Resumen del proyecto

| Campo | Valor |
|---|---|
| Categoría | Innovación y Tecnología |
| Reto | Reto 7 — Asistente virtual de acceso ciudadano a datos abiertos |
| Nivel de complejidad | Intermedio |
| Componente de IA | Random Forest (predicción), KMeans (clustering), TF-IDF + Logistic Regression (chatbot) |
| Datasets usados | 7 fuentes de datos.gov.co (10 archivos CSV) |
| Equipo | Sonia Gonzalez, Juan Felipe Jurado, Sebastian Sanchez (líder) |

## Documentación del proyecto

Este README es solo un punto de entrada. El detalle completo está separado en `docs/`:

- **[Planteamiento del problema](docs/planteamiento_problema.md)** — necesidad ciudadana/institucional, objetivo y justificación de valor público.
- **[Marco metodológico](docs/marco_metodologico.md)** — CRISP-ML(Q) y Scrum aplicados al proyecto.
- **[Fuentes de datos](docs/fuentes_datos.md)** — los 7 datasets usados, sus fichas oficiales y el alcance real de la integración vía API.
- **[Diccionario de datos](docs/diccionario_datos.md)** — columnas de cada fuente cruda y las variables analíticas derivadas.
- **[Arquitectura](docs/architecture.md)** — diagrama y descripción del pipeline, el modelo y la app.
- **[Conclusiones](docs/conclusiones.md)** — hallazgos, limitaciones conocidas e impacto potencial.
- **[Guía de validación](docs/validation_guide.md)** — cómo un evaluador puede correr el proyecto y verificar cada resultado por sí mismo.
- **[Backlog de historias de usuario (Scrum)](BACKLOG.md)** — 25 HU en 10 épicas, 6 sprints.

## Solución en producción (demo en vivo)

> ⚠️ **Pendiente:** hoy el proyecto solo corre localmente (`python app.py`). Aún no hay
> despliegue público ni imagen Docker publicada. Ver la sección "Estado de despliegue" al
> final de este README para el detalle de lo que falta y cómo cerrarlo.

## Quick start

```bash
git clone https://github.com/sebastian-sanchez-col/DIAToolkit.git
cd DIAToolkit
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Antes de ejecutar, descarga las 10 fuentes CSV indicadas en
[`docs/fuentes_datos.md`](docs/fuentes_datos.md) y colócalas en `sources/`.

```bash
python app.py
```

La app queda disponible en `http://127.0.0.1:5000`. Para instrucciones detalladas de cómo
verificar cada resultado (logs de consola, endpoints, preguntas de prueba al chatbot), ver la
[Guía de validación](docs/validation_guide.md).

## Project Structure

```text
DIAToolkit/
├── README.md
├── BACKLOG.md
├── app.py
├── data_processor.py
├── model_trainer.py
├── chatbot_nlp.py
├── datos_gov_api.py
├── requirements.txt
├── docs/
│   ├── planteamiento_problema.md
│   ├── marco_metodologico.md
│   ├── fuentes_datos.md
│   ├── diccionario_datos.md
│   ├── architecture.md
│   ├── conclusiones.md
│   └── validation_guide.md
├── sources/                # CSVs de entrada (no versionados / provistos aparte)
└── templates/
    └── dashboard.html
```

## Publicación

* Repositorio público: https://github.com/sebastian-sanchez-col/DIAToolkit.git
* Registrado en la sección de usos de datos.gov.co: https://herramientas.datos.gov.co/usos/distributional-impact-analysis-toolkit