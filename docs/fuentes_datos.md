# Fuentes de Datos

Todos los datasets provienen de [datos.gov.co](https://www.datos.gov.co). En total son **7
fuentes de datos distintas**, cargadas desde **10 archivos CSV** locales en `sources/`; la
inversión territorial es la única fuente publicada en más de una ficha (una por año, 2015 a
2018).

## Cantidad de datasets utilizados

Nivel declarado: **Intermedio** → requiere entre 3 y 10 conjuntos de datos, con al menos 1 de
datos.gov.co. Este proyecto usa **7 fuentes** (10 archivos), todas de datos.gov.co — no se
incorporan fuentes externas fuera del portal oficial.

## Tabla de datasets

| Dataset | Archivo local | Ficha en datos.gov.co |
|---|---|---|
| Inversión por comunas y corregimientos 2015 | `sources/inversion_por_comunas_y_corregimientos_2015_medellin.csv` | [Inversión por comuna y corregimiento Medellín 2015](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2015/2enc-enmu/about_data) |
| Inversión por comunas y corregimientos 2016 | `sources/inversion_por_comunas_y_corregimientos_2016_medellin.csv` | [Inversión por comuna y corregimiento Medellín 2016](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2016/3y4s-qt57/about_data) |
| Inversión por comunas y corregimientos 2017 | `sources/inversion_por_comunas_y_corregimientos_2017_medellin.csv` | [Inversión por comuna y corregimiento Medellín 2017](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2017/3e4c-pzjq/about_data) |
| Inversión por comunas y corregimientos 2018 | `sources/inversion_por_comunas_y_corregimientos_2018.csv` | [Inversión por comuna y corregimiento Medellín 2018](https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2018/uyrj-ehja) |
| Beneficiarios de becas y créditos educación superior (Antioquia) | `sources/becas_creditos_educacion_superior_antioquia.csv` ⚠️ *renombrar tras descargar* | [Beneficiarios de becas y créditos de programas de acceso a la educación superior de Antioquia](https://www.datos.gov.co/Educaci-n/Beneficiaros-de-becas-y-creditos-de-programas-de-a/ya7f-466y/about_data) |
| Subsidios y Contribuciones EPM (servicios públicos) | `sources/subsidios_contribuciones_epm_servicios.csv` ⚠️ *renombrar tras descargar* | [Subsidios y Contribuciones de Servicios Públicos Domiciliarios – EPM](https://www.datos.gov.co/Minas-y-Energ-a/Subsidios-y-Contribuciones-de-Servicios-P-blicos-D/av6t-m6ju/about_data) |
| Régimen subsidiado (salud) | `sources/subsidiado.csv` | [Afiliados al régimen subsidiado de Medellín](https://www.datos.gov.co/en/dataset/Afiliados-al-r-gimen-subsidiado-de-Medell-n/n7qb-ahpa/about_data) |
| Subsidios y Contribuciones Aseo | `sources/subsidios_y_contribuciones_aseo.csv` | [Subsidios y contribuciones aseo](https://www.datos.gov.co/dataset/Subsidios-y-contribuciones-aseo/db2v-e8wa/about_data) |
| Implementación de acciones de inclusión/discapacidad | `sources/implementacion_acciones_personas_discapacidad_familiares_cuidadores_2023.csv` | [Implementación de acciones de inclusión social para personas con discapacidad](https://www.datos.gov.co/dataset/Implementaci-n-de-acciones-de-inclusi-n-social-par/hdjq-kape/about_data) |
| Subsidios y Contribuciones EPM (directos) | `sources/subsidio_contribuciones_epm.csv` | [Subsidios y Contribuciones EPM Energía Gas Acueducto](https://www.datos.gov.co/dataset/Subsidios-y-Contribuciones-EPM-Energ-a-Gas-Acueduc/dag3-4sey/about_data) |

⚠️ **Nota sobre nombres con fecha de exportación:** los archivos de "Beneficiarios de becas y
créditos" y "Subsidios y Contribuciones EPM (servicios públicos)" se exportan desde
datos.gov.co con la fecha de descarga incluida en el nombre (ej. `..._20260708.csv`). Ese
sufijo cambia según el día en que descargues el archivo, por lo que **no** coincidirá con el
nombre fijo que espera `load_raw_datasets()` en `data_processor.py`. Debes renombrar el
archivo descargado al nombre estable indicado en la tabla antes de colocarlo en `sources/`, o
actualizar `load_raw_datasets()` para que apunte al nombre real que descargaste.

## Alcance real del consumo de API (Socrata)

Solo la **inversión territorial** (4 fichas, 2015-2018) consulta primero la API REST de
datos.gov.co (Socrata), con respaldo automático en el CSV local si la API falla
(`datos_gov_api.py`, `load_investment_year_with_api_fallback`).

Las otras **6 fuentes** (becas, EPM servicios, régimen subsidiado, aseo,
inclusión/discapacidad y EPM directos) se leen **únicamente desde CSV local**; no tienen
integración con la API todavía. Esto se documenta como limitación conocida del alcance actual
(Sprint 2 del backlog), no como funcionalidad ya cubierta.

Para activar el consumo real de API en vez del respaldo local, ver la sección "Configuración
de la API de datos.gov.co (Socrata)" en la [Guía de validación](validation_guide.md).

## Instrucciones de descarga

1. Crear una carpeta llamada `sources/` en la raíz del proyecto (si no existe).
2. Descargar cada uno de los 10 archivos CSV listados arriba desde su ficha en datos.gov.co.
3. Guardarlos dentro de `sources/` usando **exactamente** el nombre de archivo indicado en la
   tabla (los nombres deben coincidir con `INVESTMENT_FILES_BY_YEAR` y `load_raw_datasets()`
   en `data_processor.py`).
4. Renombrar los dos archivos marcados con ⚠️ antes de colocarlos en `sources/`.

Sin estos 10 archivos, `python app.py` lanzará `FileNotFoundError` al arrancar.