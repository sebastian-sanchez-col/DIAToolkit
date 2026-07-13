# DIAToolkit

**Distributional Impact Analysis: Toolkit**

Aplicación Flask desarrollada para el **Concurso Datos al Ecosistema 2026: IA para Colombia**,
categoría **Gobernanza y transparencia** — Reto 7: *"Diseñar asistentes virtuales que faciliten el
acceso ciudadano a datos abiertos"*.

Integra 7 fuentes de datos abiertos de [datos.gov.co](https://www.datos.gov.co) sobre inversión
territorial y subsidios sociales en Medellín, aplica un pipeline de limpieza/auditoría de datos,
entrena un modelo predictivo (Random Forest) de inversión por comuna, y expone un dashboard
interactivo con un simulador de escenarios y un chatbot conversacional.

## Resumen del proyecto

| Campo | Valor |
|---|---|
| Categoría | Gobernanza y transparencia |
| Reto | Reto 7 — Asistente virtual de acceso ciudadano a datos abiertos |
| Nivel de complejidad | Intermedio |
| ID de equipo | 244 |
| Componente de IA | Random Forest (predicción), KMeans (clustering), TF-IDF + Logistic Regression (chatbot) |
| Datasets usados | 7 fuentes de datos.gov.co (10 archivos CSV) |
| Validación del modelo | GroupKFold (5 folds) por comuna, N=84 — R² ≈ 0.64 (± 0.11) |
| Equipo | Juan Sebastián Sanchez (líder), Juan Felipe Jurado, Sonia Luz González Pardo |

## Tipo de análisis y resultados clave

- **Tipo de análisis:** Predictivo (regresión, Random Forest Regressor) + clustering no supervisado (KMeans) + clasificación de intención (TF-IDF + Logistic Regression para el chatbot).
- **Modelo principal:** Random Forest Regressor, validado con GroupKFold (5 folds) agrupado por comuna, N=84 → **R² ≈ 0.64 (± 0.11)**.
- **Hallazgo clave:** las comunas con mayor participación relativa en régimen subsidiado de salud (r = -0.38) e inclusión social (r = -0.34) muestran, en promedio, **menor** inversión pública histórica — evidencia de una posible desalineación entre necesidad social y asignación de recursos (correlación, no causalidad; ver [`conclusiones.md`](docs/conclusiones.md) para el detalle completo y las limitaciones documentadas).
- **Impacto potencial:** ver tabla completa en [`conclusiones.md`](docs/conclusiones.md#4-impacto-potencial).

## Documentación del proyecto

Este README es solo un punto de entrada. El detalle completo está separado en `docs/`:

- **[Planteamiento del problema](docs/planteamiento_problema.md)**
- **[Marco metodológico](docs/marco_metodologico.md)**
- **[Fuentes de datos](docs/fuentes_datos.md)**
- **[Diccionario de datos](docs/diccionario_datos.md)**
- **[Arquitectura](docs/architecture.md)**
- **[Conclusiones](docs/conclusiones.md)** — incluye resultados reales del modelo (R², correlaciones)
- **[Guía de validación](docs/validation_guide.md)**
- **[Backlog de historias de usuario (Scrum)](BACKLOG.md)**


## Solución en producción (demo en vivo)

> ⚠ El proyecto solo corre localmente (`python app.py`). La imagen docker
> permite comprobar. Durante la sustentación se mostrará la demo corriendo
> localmente, compartiendo pantalla.

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

La app queda disponible en `http://127.0.0.1:5000`. Ver la
[Guía de validación](docs/validation_guide.md) para instrucciones de verificación.

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
├── recursos/
│   ├── portada.png
│   └── Simulador_de_Impacto_Presupuestal.pdf
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
* Contenedor listo (Docker Hub): `docker pull ataches/diatoolkit:latest`

### Enlaces de acceso

* [Descargar archivo original (.PPTX)](recursos/presentacion.pptx) — *Para abrir y editar en PowerPoint.*
* [Ver presentación en línea (.PDF)](recursos/presentacion.pdf) — *Abre el visor interactivo de GitHub o GitLab.*
* [Descarga directa (.PDF)](recursos/presentacion.pdf?raw=true&inline=false) — *Fuerza la descarga en ambas plataformas.*