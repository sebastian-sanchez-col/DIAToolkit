# data_processor.py

import re

import unicodedata
import numpy as np
import pandas as pd
from datos_gov_api import load_investment_year_with_api_fallback
from datetime import date

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------


INVESTMENT_UNIT_MULTIPLIER_DEFAULT = 1_000_000

CLEANING_COLUMN_CANDIDATES = [
    'MUNICIPIO DE RESIDENCIA', 'municipio_de_residencia', 'Municipio de Residencia',
    'municipio_o_sector', 'Municipio o Sector', 'municipio', 'Municipio', 'MUNICIPIO',
]

INVESTMENT_COLUMN_CANDIDATES = {
    'comuna_name': ['Nombre Comuna', 'nombre_comuna', 'NOMBRE_COMUNA', 'NOMBRE COMUNA',
                    'Comuna', 'comuna', 'COMUNA'],
    'comuna_id_for_dropna': ['Comuna', 'comuna', 'COMUNA', 'Codigo Comuna', 'codigo_comuna',
                             'CODIGO_COMUNA'],
    'valor_inversion': ['Inversion', 'inversion', 'INVERSION', 'Valor Inversion',
                        'valor_inversion', 'Valor', 'VALOR', 'Monto', 'monto'],
}

# Model feature contract shared with model_trainer.py / app.py.
MODEL_FEATURE_COLUMNS = [
    "health_affiliates_share",
    "inclusion_share",
    "mean_utility_stratum",
    "year"
]

# Human-readable Spanish labels for each model feature. Centralized here so
# that the dashboard (app.py) and the chatbot (chatbot_nlp.py) always describe the
# same variable using exactly the same phrasing.
FEATURE_TRANSLATION = {
    'health_affiliates_share': 'Densidad Demográfica Vulnerable (Participación Relativa, Régimen Subsidiado)',
    'inclusion_share': 'Vulnerabilidad Prioritaria (Participación Relativa, Inclusión Social)',
    'mean_utility_stratum': 'Nivel de Capacidad Socioeconómica Promedio (Estrato Real)',
    'year': 'Año de la Inversión (Tendencia Temporal Multi-Año)',
}

STRATUM_CATEGORY_TO_NUMBER = {
    'BAJO-BAJO': 1,
    'BAJO': 2,
    'MEDIO-BAJO': 3,
    'MEDIO': 4,
    'MEDIO-ALTO': 5,
    'ALTO': 6,
    'SIN DATO': np.nan,
    'SIN ESTRATIFICAR': np.nan,
}

CLEANING_PROVIDERS_MEDELLIN = [
    'Empresas Varias de Medellin',
]

SPANISH_MONTH_TO_NUMBER = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'SETIEMBRE': 9, 'OCTUBRE': 10,
    'NOVIEMBRE': 11, 'DICIEMBRE': 12,
}

VALID_COMMUNE_CODES = list(range(1, 17)) + [50, 60, 70, 80, 90]

MEDELLIN_TERRITORIES = [
    '01 - POPULAR', '02 - SANTA CRUZ', '03 - MANRIQUE', '04 - ARANJUEZ',
    '05 - CASTILLA', '06 - DOCE DE OCTUBRE', '07 - ROBLEDO', '08 - VILLA HERMOSA',
    '09 - BUENOS AIRES', '10 - LA CANDELARIA', '11 - LAURELES ESTADIO', '12 - LA AMERICA',
    '13 - SAN JAVIER', '14 - EL POBLADO', '15 - GUAYABAL', '16 - BELEN',
    '50 - SAN SEBASTIÁN DE PALMITAS', '60 - SAN CRISTÓBAL', '70 - ALTAVISTA',
    '80 - SAN ANTONIO DE PRADO', '90 - SANTA ELENA'
]

INVESTMENT_FILES_BY_YEAR = {
    2015: ('sources/inversion_por_comunas_y_corregimientos_2015_medellin.csv', '2enc-enmu'),
    2016: ('sources/inversion_por_comunas_y_corregimientos_2016_medellin.csv', '3y4s-qt57'),
    2017: ('sources/inversion_por_comunas_y_corregimientos_2017_medellin.csv', '3e4c-pzjq'),
    2018: ('sources/inversion_por_comunas_y_corregimientos_2018.csv', 'uyrj-ehja'),
}

REFERENCE_STRATUM_FALLBACK = 2.4
CLEANING_SUBSCRIBERS_POPULATION_REFERENCE = 2_600_000  # approx. population of Medellín

# ---------------------------------------------------------------------------
# Data Quality Scorecard (6 formal dimensions, per the Data Quality session)
# ---------------------------------------------------------------------------

TIMELINESS_STALE_DAYS_WARNING = 365 * 2

# ---------------------------------------------------------------------------
# Generic text utilities
# ---------------------------------------------------------------------------

def strip_accents(text):
    """Removes accents and diacritics from a string."""
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch))


def find_column(df, candidates):
    """Finds the first column in df matching any candidate name, accent/case-insensitive."""
    normalized_lookup = {
        strip_accents(str(col)).upper().strip(): col
        for col in df.columns
    }
    for candidate in candidates:
        key = strip_accents(str(candidate)).upper().strip()
        if key in normalized_lookup:
            return normalized_lookup[key]
    return None


# ---------------------------------------------------------------------------
# Commune name matching
# ---------------------------------------------------------------------------

_COMMUNE_KEYWORDS = [
    ('POPULAR', 1, '01 - POPULAR'),
    ('SANTA CRUZ', 2, '02 - SANTA CRUZ'),
    ('MANRIQUE', 3, '03 - MANRIQUE'),
    ('ARANJUEZ', 4, '04 - ARANJUEZ'),
    ('CASTILLA', 5, '05 - CASTILLA'),
    ('DOCE DE OCTUBRE', 6, '06 - DOCE DE OCTUBRE'),
    ('ROBLEDO', 7, '07 - ROBLEDO'),
    ('VILLA HERMOSA', 8, '08 - VILLA HERMOSA'),
    ('BUENOS AIRES', 9, '09 - BUENOS AIRES'),
    ('LA CANDELARIA', 10, '10 - LA CANDELARIA'),
    ('LAURELES', 11, '11 - LAURELES ESTADIO'),
    ('LA AMERICA', 12, '12 - LA AMERICA'),
    ('SAN JAVIER', 13, '13 - SAN JAVIER'),
    ('POBLADO', 14, '14 - EL POBLADO'),
    ('GUAYABAL', 15, '15 - GUAYABAL'),
    ('BELEN', 16, '16 - BELEN'),
    ('PALMITAS', 50, '50 - SAN SEBASTIÁN DE PALMITAS'),
    ('SAN CRISTOBAL', 60, '60 - SAN CRISTÓBAL'),
    ('ALTAVISTA', 70, '70 - ALTAVISTA'),
    ('SAN ANTONIO', 80, '80 - SAN ANTONIO DE PRADO'),
    ('PRADO', 80, '80 - SAN ANTONIO DE PRADO'),
    ('SANTA ELENA', 90, '90 - SANTA ELENA'),
]


def clean_commune_name(text):
    """Standardizes raw commune names into unified alphanumeric keys."""
    if pd.isna(text):
        return "UNKNOWN"

    normalized_text = strip_accents(str(text).upper().strip())
    match = re.search(r'\d+', normalized_text)
    commune_number = int(match.group()) if match else None

    for keyword, code, standardized_key in _COMMUNE_KEYWORDS:
        if keyword in normalized_text or commune_number == code:
            return standardized_key

    return 'OTHER_ZONE'


def map_stratum_category(series):
    """Normalizes and maps string-based stratum descriptions to numbers."""
    normalized = series.astype(str).str.upper().str.strip()
    return normalized.map(STRATUM_CATEGORY_TO_NUMBER)



def compute_completeness(df, required_columns, label_for_log):
    """Completeness = records with ALL mandatory fields filled / total * 100."""
    required_columns = [c for c in required_columns if c in df.columns]
    if not required_columns:
        return None
    filled_mask = df[required_columns].notna().all(axis=1)
    score = filled_mask.mean() * 100
    print(f"[CALIDAD - COMPLETITUD] {label_for_log}: {score:.1f}% de filas con todos los "
          f"campos obligatorios {required_columns} diligenciados.")
    return score


def compute_uniqueness(df, key_columns, label_for_log):
    """Uniqueness = unique records / total records * 100."""
    key_columns = [c for c in key_columns if c in df.columns]
    if not key_columns:
        print(f"[CALIDAD - UNICIDAD] {label_for_log}: no se definió una llave de negocio "
              f"confiable para este dataset; se omite esta dimensión (la deduplicación de "
              f"filas exactas ya se cubre en la etapa de purga general).")
        return None
    total = len(df)
    unique = df.drop_duplicates(subset=key_columns).shape[0]
    score = (unique / total * 100) if total else 0
    print(f"[CALIDAD - UNICIDAD] {label_for_log}: {score:.1f}% de registros únicos "
          f"sobre llave {key_columns}.")
    return score


def compute_validity(df, column, validator_fn, label_for_log):
    """Validity = records that meet the format/range rule / total * 100."""
    if column not in df.columns:
        return None
    valid_mask = df[column].apply(validator_fn)
    score = valid_mask.mean() * 100
    print(f"[CALIDAD - VALIDEZ] {label_for_log}: {score:.1f}% de '{column}' cumple "
          f"la regla de negocio esperada.")
    return score


def compute_consistency(cross_source_checks, label_for_log):
    """Consistency = % of cross-checks between sources that match.
    Reuses already calculated signals (temporal alignment, duplicates) instead
    of introducing a new metric without backing."""
    if not cross_source_checks:
        return None
    score = sum(1 for ok in cross_source_checks if ok) / len(cross_source_checks) * 100
    print(f"[CALIDAD - CONSISTENCIA] {label_for_log}: {score:.1f}% de verificaciones "
          f"cruzadas entre fuentes fueron coherentes.")
    return score


def compute_timeliness(period_end, label_for_log, reference_date=None):
    """
    Timeliness = availability_time - event_time.
    Previously, this project NEVER reported this: investment data (2015-2018)
    was presented without warning that, as of the execution date, it is several years
    old.
    """
    if period_end is None or pd.isna(period_end):
        print(f"[CALIDAD - OPORTUNIDAD] {label_for_log}: no se pudo determinar la fecha "
              f"del dato más reciente.")
        return None

    reference_date = reference_date or pd.Timestamp(date.today())
    staleness_days = (reference_date - period_end).days

    print(f"[CALIDAD - OPORTUNIDAD] {label_for_log}: el dato más reciente es de "
          f"{period_end.date()}, es decir {staleness_days} días de antigüedad respecto "
          f"a hoy ({reference_date.date()}).")

    if staleness_days > TIMELINESS_STALE_DAYS_WARNING:
        print(f"  ⚠️ ALERTA DE OPORTUNIDAD: {label_for_log} tiene más de "
              f"{TIMELINESS_STALE_DAYS_WARNING // 365} años sin actualizarse. "
              f"Cualquier conclusión o simulación basada en esta fuente debe advertir "
              f"al usuario final que está usando datos históricos, no vigentes.")
    return staleness_days


def build_quality_scorecard(datasets_config):
    """
    datasets_config: lista de dicts, cada uno con:
      {'df':..., 'label':..., 'required_cols':[...], 'key_cols':[...],
       'validity_column':..., 'validity_fn':..., 'period_end':...}
    Imprime y retorna un resumen consolidado de las 6 dimensiones por dataset.
    """
    print("[CALIDAD - EXACTITUD] No se calcula: no existe una fuente de verdad externa "
          "para comparar los valores de estas fuentes administrativas. Se documenta como "
          "limitación conocida del scorecard, no como dato faltante por descuido.")
    scorecard = {}
    for cfg in datasets_config:
        label = cfg['label']
        scorecard[label] = {
            'completitud': compute_completeness(cfg['df'], cfg.get('required_cols', []), label),
            'unicidad': compute_uniqueness(cfg['df'], cfg.get('key_cols', []), label),
            'validez': compute_validity(cfg['df'], cfg.get('validity_column'),
                                        cfg.get('validity_fn', lambda x: True), label)
            if cfg.get('validity_column') else None,
            'consistencia': None,
            'oportunidad_dias': compute_timeliness(cfg.get('period_end'), label),
            'exactitud': None,
        }
    return scorecard


# ---------------------------------------------------------------------------
# Numeric / period cleaning utilities
# ---------------------------------------------------------------------------

def extract_leading_number(series):
    """Extracts numeric values located at the beginning of parsed strings."""
    extracted = series.astype(str).str.extract(r'(\d+)')[0]
    return pd.to_numeric(extracted, errors='coerce')


def _fix_decimal_thousand_separators(value):
    """Normalizes mixed decimal/thousands separators (e.g. '1.234,56' -> '1234.56')."""
    if not value:
        return "0"
    if '.' in value and ',' not in value:
        parts = value.split('.')
        if len(parts[-1]) == 3:
            return value.replace('.', '')
    if ',' in value and '.' in value:
        return value.replace('.', '').replace(',', '.')
    elif ',' in value:
        return value.replace(',', '.')
    return value


def robust_numeric_clean(series, label_for_log=None):
    """Cleans numeric formats from strings with diverse decimal/thousands separators.

    If a '%' symbol is detected in the raw values, it is no longer silently
    discarded: it was confirmed against the original source (EPM CSV without
    the '%' symbol, e.g. stratum 1 = -6000, Industria = 3000, Comercio = 5000)
    that the text with '%' corresponds exactly to the real value multiplied by
    100 (e.g. '300.000,00%' is the real value 3000, not 300000). This matches
    the classic Excel export bug: a numeric cell formatted as a percentage
    exports the number already multiplied by 100, followed by the '%' symbol.
    Therefore, when '%' is detected, that multiplication is reverted by
    dividing by 100 after cleaning the format.
    """
    raw_values = series.astype(str)
    percentage_mask = raw_values.str.contains('%', na=False)
    n_with_percentage = percentage_mask.sum()

    if n_with_percentage > 0 and label_for_log:
        examples = raw_values[percentage_mask].unique()[:5].tolist()
        print(f"[CORRECCIÓN FORMATO] {label_for_log}: {n_with_percentage} de {len(raw_values)} filas "
              f"contenían el símbolo '%' (ej: {examples}). Verificado contra la fuente original: "
              f"esto es un artefacto de exportación desde Excel (celda formateada como porcentaje, "
              f"que exporta el número YA multiplicado por 100), no un porcentaje real. "
              f"Se está dividiendo automáticamente entre 100 para recuperar el valor real.")

    cleaned = raw_values.str.replace(r'[^\d,.-]', '', regex=True).str.strip()
    cleaned = cleaned.apply(_fix_decimal_thousand_separators)
    numeric = pd.to_numeric(cleaned, errors='coerce').fillna(0.0)

    # Revert the x100 multiplication only for rows whose raw text had '%'
    # (other rows do not have this artifact and must not be touched).
    if percentage_mask.any():
        aligned_mask = percentage_mask.reindex(numeric.index, fill_value=False)
        numeric.loc[aligned_mask] = numeric.loc[aligned_mask] / 100.0

    return numeric


def build_period_from_year_month(df, year_col, month_col=None):
    """
    Builds a period column (Timestamp, day 1 of each month) from a year column
    (integer) and, optionally, a month column (numeric or Spanish name).

    Exists to avoid the bug where pd.to_datetime(2019) interprets the integer
    as 2019 NANOSECONDS since 1970 instead of the year 2019 — an error that is
    not easily noticed because the count of distinct periods stays correct,
    but produces false dates.
    """
    year_numeric = pd.to_numeric(df[year_col], errors='coerce')

    if month_col is not None and month_col in df.columns:
        raw_month = df[month_col]
        month_numeric = pd.to_numeric(raw_month, errors='coerce')

        needs_name_mapping = month_numeric.isna() & raw_month.notna()
        if needs_name_mapping.any():
            normalized_month_names = (
                raw_month[needs_name_mapping].astype(str)
                .apply(strip_accents).str.upper().str.strip()
            )
            month_numeric.loc[needs_name_mapping] = normalized_month_names.map(SPANISH_MONTH_TO_NUMBER)

        month_numeric = month_numeric.fillna(1).clip(lower=1, upper=12).astype(int)
    else:
        month_numeric = pd.Series(1, index=df.index)

    valid_rows = year_numeric.notna()
    period = pd.Series(pd.NaT, index=df.index, dtype='datetime64[ns]')
    period.loc[valid_rows] = pd.to_datetime(
        {'year': year_numeric[valid_rows].astype(int), 'month': month_numeric[valid_rows], 'day': 1},
        errors='coerce'
    )
    return period


# ---------------------------------------------------------------------------
# Geographic filtering
# ---------------------------------------------------------------------------

def filter_cleaning_to_medellin_by_provider(df, label_for_log="Subsidios y Contribuciones Aseo"):
    """Filters the cleaning (aseo) dataset to Medellín using a provider whitelist,
    for datasets that lack a real geographic column."""
    if 'prestador' not in df.columns:
        print(f"[ALERTA ASEO] No existe la columna 'prestador' en {label_for_log}. No se puede filtrar.")
        return df, False

    mask = df['prestador'].isin(CLEANING_PROVIDERS_MEDELLIN)
    filtered = df[mask].copy()
    included_providers = sorted(df.loc[mask, 'prestador'].unique().tolist())
    excluded_providers = sorted(df.loc[~mask, 'prestador'].unique().tolist())

    print(f"[FILTRO GEOGRÁFICO (whitelist prestador)] {label_for_log}: {len(df)} filas -> {len(filtered)} filas. "
          f"Prestadores incluidos: {included_providers}. "
          f"Prestadores excluidos ({len(excluded_providers)}): {excluded_providers[:10]}"
          f"{'...' if len(excluded_providers) > 10 else ''}")

    return filtered, True


def filter_to_medellin(df, column, label_for_log):
    """Filters a dataframe to rows whose geographic column contains 'MEDELL'."""
    if column not in df.columns:
        print(f"[ALERTA FILTRO] La columna '{column}' no existe en {label_for_log}. No se aplicó filtro geográfico.")
        return df

    normalized = df[column].astype(str).str.upper().str.strip()
    mask = normalized.str.contains('MEDELL', na=False)
    filtered = df[mask].copy()

    pct_kept = len(filtered) / len(df) * 100 if len(df) else 0
    print(f"[FILTRO GEOGRÁFICO] {label_for_log}: {len(df)} filas totales -> {len(filtered)} filas de Medellín "
          f"({pct_kept:.2f}% del total).")

    if pct_kept < 5:
        top_unmatched = normalized[~mask].value_counts().head(10)
        print(f"  ⚠️ ALERTA: solo el {pct_kept:.2f}% quedó como Medellín en '{column}'. "
              f"Top valores NO emparejados:")
        for value, count in top_unmatched.items():
            print(f"       '{value}': {count} filas")

    return filtered


# ---------------------------------------------------------------------------
# Diagnostics (read-only, informational; never mutate the pipeline's output)
# ---------------------------------------------------------------------------

def diagnostic_unmatched_communes(df, raw_column, label_for_log):
    """Reports rows whose raw commune value did not match any known commune."""
    if raw_column not in df.columns:
        print(f"[DIAGNÓSTICO COMUNAS] Columna '{raw_column}' no existe en {label_for_log}.")
        return

    total = len(df)
    unmatched_mask = df[raw_column].apply(clean_commune_name) == 'OTHER_ZONE'
    n_unmatched = unmatched_mask.sum()
    pct_unmatched = (n_unmatched / total * 100) if total else 0

    if n_unmatched > 0:
        top_values = df.loc[unmatched_mask, raw_column].astype(str).value_counts().head(10)
        print(f"[DIAGNÓSTICO COMUNAS] {label_for_log}: {n_unmatched:,} de {total:,} filas "
              f"({pct_unmatched:.1f}%) NO emparejadas a ninguna comuna válida (cayeron en 'OTHER_ZONE').")
        print(f"  └─ Top valores crudos sin match (valor: conteo de filas):")
        for value, count in top_values.items():
            print(f"       '{value}': {count:,} filas")
        if pct_unmatched > 30:
            print(f"  ⚠️ ALERTA: {pct_unmatched:.1f}% de '{label_for_log}' quedó sin comuna válida. "
                  f"Confirma si esta columna realmente corresponde a comunas de Medellín "
                  f"(1-16, 50-90) o si el dataset cubre otros municipios/categorías que "
                  f"deben excluirse por diseño (en cuyo caso puede ser normal).")
    else:
        print(f"[DIAGNÓSTICO COMUNAS] {label_for_log}: 100% de las {total:,} filas emparejadas correctamente.")


def diagnostic_zero_after_conversion(series_before, series_after, column_name, label_for_log):
    """Validates if standard numeric casting operations resulted in massive text drops (zeros)."""
    n_zero = (series_after == 0).sum()
    pct_zero = n_zero / len(series_after) * 100 if len(series_after) else 0
    if pct_zero > 50:
        examples = series_before.astype(str).unique()[:5].tolist()
        print(f"[ALERTA CONVERSIÓN] {label_for_log}: {pct_zero:.1f}% de '{column_name}' quedó en 0 "
              f"tras convertir a numérico. Ejemplos de valores crudos: {examples}")


def diagnostic_outlier_check(df, column_name, label_for_log, id_columns=None, top_n=10, population_reference=None):
    """
    Shows the rows with the highest values of column_name to detect whether an
    aggregated total is being inflated by one or a few outliers (e.g. a
    mistyped value, a row accumulated by mistake, etc.).

    population_reference: if passed, compares each individual value against
    that number (e.g. the population of Medellín) and alerts if a single row
    already exceeds it.
    """
    if column_name not in df.columns:
        print(f"[DIAGNÓSTICO OUTLIERS] Columna '{column_name}' no existe en {label_for_log}.")
        return

    id_columns = [c for c in (id_columns or []) if c in df.columns]
    columns_to_show = id_columns + [column_name]

    top_rows = df.sort_values(by=column_name, ascending=False).head(top_n)
    total = df[column_name].sum()

    print(f"[DIAGNÓSTICO OUTLIERS] {label_for_log}: total sumado de '{column_name}' = {total:,.2f}")
    print(f"  └─ Top {top_n} filas con mayor valor individual:")
    for _, row in top_rows.iterrows():
        detail = ", ".join(f"{c}={row[c]}" for c in columns_to_show)
        pct_of_total = (row[column_name] / total * 100) if total else 0
        print(f"       {detail}  ({pct_of_total:.1f}% del total)")

    if population_reference is not None:
        max_value = df[column_name].max()
        if max_value > population_reference:
            print(f"  ⚠️ ALERTA: el valor máximo individual ({max_value:,.0f}) ya supera la "
                  f"referencia de población ({population_reference:,.0f}). Revisar esa fila "
                  f"antes de confiar en el total agregado.")


def diagnostic_check_duplicate_subsidy_sources(df_utility_subsidy, df_epm_subsidies_contributions):
    """
    Compares 'EPM servicios' and 'EPM directos' at the row level (not just
    their aggregate sum) to detect whether they are the same underlying
    dataset republished under two different catalog entries on datos.gov.co.

    Matching only the aggregate sum is a weak signal (different individual
    values could coincidentally add up to the same total). Matching the full
    sorted array of individual 'valor' values is a near-definitive signal:
    two independent subsidy programs matching on every single value is
    statistically implausible. This was independently corroborated against
    the datos.gov.co catalog entries for both resources, which describe the
    same content (EPM subsidies for Energía/Gas/Acueducto y Alcantarillado in
    Antioquia) and share the same column dictionary ('a_o', 'mes', 'valor').
    """
    utility_values = sorted(df_utility_subsidy['valor'].round(2).tolist())
    epm_direct_values = sorted(df_epm_subsidies_contributions['valor'].round(2).tolist())

    same_length = len(utility_values) == len(epm_direct_values)
    confirmed_duplicate = same_length and utility_values == epm_direct_values

    if confirmed_duplicate:
        print(f"[DUPLICADO CONFIRMADO] 'EPM servicios' y 'EPM directos' tienen exactamente los mismos "
              f"{len(utility_values)} valores individuales (no solo la misma suma), y sus fichas en "
              f"datos.gov.co describen el mismo contenido con el mismo diccionario de columnas. Se "
              f"excluye 'EPM directos' de cualquier total combinado de ciudad para no contar el mismo "
              f"subsidio dos veces.")
    elif not same_length:
        print(f"[DIAGNÓSTICO EPM] 'EPM servicios' ({len(utility_values)} filas) y 'EPM directos' "
              f"({len(epm_direct_values)} filas) tienen distinto número de filas tras la limpieza; "
              f"no aplica la comparación de duplicado exacto.")

    return confirmed_duplicate


def diagnostic_correlation_check(df_analytics, label_for_log="Panel"):
    """Evaluates correlations of key variables against the core investment metric.

    Reports both the absolute-count variables and the relative-share variables
    that the actual model trains on, so both diagnostics talk about the same
    underlying concepts.
    """
    print(f"\n[DIAGNÓSTICO CORRELACIÓN - {label_for_log}] Relación entre variables y total_investment "
          f"(N={len(df_analytics)}):")
    columns_to_check = [
        "total_subsidized_health_affiliates",
        "health_affiliates_share",
        "total_disabled_and_inclusion_beneficiaries",
        "inclusion_share",
        "mean_utility_stratum",
    ]
    for column in columns_to_check:
        if column in df_analytics.columns:
            correlation = df_analytics[column].corr(df_analytics["total_investment"])
            direction = "POSITIVA (a más X, más inversión)" if correlation > 0 else "NEGATIVA (a más X, menos inversión)"
            print(f"  └─ {column}: r = {correlation:.3f} -> {direction}")


def run_data_audit_report(datasets, stage_label):
    """Performs an extensive technical audit for null entries and duplicates."""
    print(f"\n🔍 INICIANDO AUDITORÍA - ESTADO DE LA PIPELINE: [{stage_label}]")
    print("=" * 65)

    for name, df in datasets.items():
        print(f"\n📊 DataFrame: {name} | Filas: {len(df)} | Columnas: {len(df.columns)}")
        print("-" * 45)

        null_counts = df.isnull().sum()
        critical_nulls = null_counts[null_counts > 0]
        if not critical_nulls.empty:
            print("❌ MALA GESTIÓN: Se encontraron valores nulos o faltantes:")
            for column, count in critical_nulls.items():
                print(f"  └─ Columna '{column}': {count} filas faltantes ({count / len(df) * 100:.2f}%)")
        else:
            print("✅ GESTIÓN: Cero celdas nulas o faltantes detectadas.")

        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            print(f"❌ MALA GESTIÓN: ¡Se detectaron {duplicate_count} filas idénticas duplicadas!")
        else:
            print("✅ GESTIÓN: Cero filas duplicadas en este entorno.")

    print("\n" + "=" * 65)


def diagnostic_and_dedupe_by_period(df, label_for_log, key_columns_override,
                                     period_col=None, year_col=None, month_col=None):
    """
    Exactly one of these two period sources must be provided:
      - period_col: a column that is already a full, directly parseable date
        (e.g. aseo, with a real date-typed 'periodo' column).
      - year_col (+ optional month_col): builds the period internally by
        combining year and month (see build_period_from_year_month), avoiding
        the bug of integer years being interpreted as nanoseconds.

    key_columns_override is REQUIRED and must include ALL categorical columns
    that distinguish genuinely different data lines (e.g. service, subsidy
    type), not just location. Omitting a real categorical key column collapses
    legitimately distinct rows as if they were duplicates of the same period
    (this already caused real data loss in a previous version).
    """
    df = df.copy()

    if year_col is not None:
        if year_col not in df.columns:
            print(f"[ALERTA PERIODOS] {label_for_log}: la columna de año '{year_col}' no existe. "
                  f"Columnas disponibles: {df.columns.tolist()}.")
            return df, False, {}
        df['_internal_period'] = build_period_from_year_month(df, year_col, month_col)
        period_source_desc = f"año='{year_col}'" + (f", mes='{month_col}'" if month_col else "")
    elif period_col is not None:
        if period_col not in df.columns:
            print(f"[ALERTA PERIODOS] {label_for_log}: la columna de periodo '{period_col}' no existe. "
                  f"Columnas disponibles: {df.columns.tolist()}.")
            return df, False, {}
        df['_internal_period'] = pd.to_datetime(df[period_col], dayfirst=True, errors='coerce')
        period_source_desc = f"columna='{period_col}'"
    else:
        print(f"[ALERTA PERIODOS] {label_for_log}: no se indicó 'period_col' ni 'year_col'; "
              f"no se puede determinar el periodo. Columnas disponibles: {df.columns.tolist()}.")
        return df, False, {}

    n_missing_period = df['_internal_period'].isna().sum()
    if n_missing_period > 0:
        print(f"[ALERTA PERIODOS] {label_for_log}: {n_missing_period} de {len(df)} filas no pudieron "
              f"convertirse a un periodo válido ({period_source_desc}); quedan con periodo NaT y "
              f"podrían perderse o quedar mal ordenadas en la deduplicación.")

    missing_keys = [c for c in key_columns_override if c not in df.columns]
    if missing_keys:
        print(f"[ALERTA PERIODOS] {label_for_log}: las llaves {missing_keys} no existen en el "
              f"dataset. Columnas disponibles: {df.columns.tolist()}. No se pudo deduplicar.")
        return df.drop(columns=['_internal_period']), False, {}

    n_periods_per_key = df.groupby(key_columns_override, dropna=False)['_internal_period'].nunique()
    n_unique_keys = len(n_periods_per_key)
    period_min = df['_internal_period'].min()
    period_max = df['_internal_period'].max()

    print(f"[DIAGNÓSTICO PERIODOS] {label_for_log}: periodo determinado por {period_source_desc}. "
          f"Rango {period_min} -> {period_max}. Promedio de {n_periods_per_key.mean():.1f} "
          f"periodos distintos por combinación de llaves {key_columns_override} "
          f"(máx {n_periods_per_key.max()}). Llaves únicas detectadas: {n_unique_keys}.")

    # If every key has the same number of periods (no dispersion), the row
    # count should divide exactly by that number to yield the unique keys.
    # If it doesn't match, there are rows with EXACTLY duplicated key+period
    # (not another distinct period), and 'keep=last' discards them without
    # summing their value.
    rows_before = len(df)
    if n_periods_per_key.std() < 1e-9:
        expected_rows_without_collision = n_unique_keys * n_periods_per_key.mean()
        if abs(expected_rows_without_collision - rows_before) > 0.5:
            n_collisions = int(round(rows_before - expected_rows_without_collision))
            print(f"  ⚠️ ALERTA: se esperaban {int(expected_rows_without_collision)} filas "
                  f"({n_unique_keys} llaves x {n_periods_per_key.mean():.0f} periodos uniformes), "
                  f"pero hay {rows_before}. Esto indica {n_collisions} fila(s) con la MISMA "
                  f"llave+periodo repetida (no otro periodo distinto). Al quedarse solo con la última "
                  f"fila por llave+periodo, esas filas duplicadas se están descartando sin sumar su "
                  f"valor. Revisar manualmente si son correcciones/duplicados reales a ignorar o si "
                  f"deberían sumarse en vez de deduplicarse.")

    deduped = df.sort_values('_internal_period').drop_duplicates(subset=key_columns_override, keep='last')
    deduped = deduped.drop(columns=['_internal_period'])
    print(f"[DEDUPLICACIÓN PERIODOS] {label_for_log}: {rows_before} filas -> {len(deduped)} filas "
          f"(quedándose solo con el periodo más reciente por combinación de llaves {key_columns_override}, "
          f"para no sumar periodos duplicados como si fueran un único total).")

    period_info = {'period_min': period_min, 'period_max': period_max}
    return deduped, True, period_info


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_investment_year(path, year, dataset_id=None):
    """Loads and normalizes raw investment data for a specific year."""

    if dataset_id:
        df, source_used = load_investment_year_with_api_fallback(dataset_id, path, year)
        print(f"[FUENTE INVERSIÓN {year}] Origen de los datos: {source_used}")
    else:
        try:
            df = pd.read_csv(path)
        except FileNotFoundError:
            print(f"[ALERTA INVERSIÓN {year}] No se encontró el archivo '{path}'. Se omite ese año.")
            return None

    name_col = find_column(df, INVESTMENT_COLUMN_CANDIDATES['comuna_name'])
    if name_col is None:
        print(f"[ALERTA INVERSIÓN {year}] No se encontró columna de nombre de comuna en '{path}'. "
              f"Columnas disponibles: {df.columns.tolist()}. Se omite ese año.")
        return None

    dropna_col = find_column(df, INVESTMENT_COLUMN_CANDIDATES['comuna_id_for_dropna']) or name_col
    df = df.dropna(subset=[dropna_col]).copy()

    value_col = find_column(df, INVESTMENT_COLUMN_CANDIDATES['valor_inversion'])
    if value_col is None:
        print(f"[ALERTA INVERSIÓN {year}] No se encontró columna de valor de inversión en '{path}'. "
              f"Columnas disponibles: {df.columns.tolist()}. Se omite ese año.")
        return None

    df['commune_clean'] = df[name_col].apply(clean_commune_name)
    diagnostic_unmatched_communes(df, name_col, f'Inversión por comuna {year}')

    df['investment_value'] = robust_numeric_clean(df[value_col]) * INVESTMENT_UNIT_MULTIPLIER_DEFAULT
    df['year'] = year

    print(f"[CARGA INVERSIÓN {year}] '{path}': {len(df)} filas cargadas "
          f"(columna comuna='{name_col}', columna valor='{value_col}').")

    return df[['commune_clean', 'investment_value', 'year']]


def load_investment_multiyear():
    """Aggregates multi-year investment records into a single multi-year dataset."""
    yearly_dataframes = []
    for year, (path, dataset_id) in sorted(INVESTMENT_FILES_BY_YEAR.items()):
        df_year = load_investment_year(path, year, dataset_id=dataset_id)
        if df_year is not None:
            yearly_dataframes.append(df_year)

    if not yearly_dataframes:
        raise RuntimeError("[ERROR INVERSIÓN] No se pudo cargar NINGÚN año de inversión. "
                            "Revisa las rutas en INVESTMENT_FILES_BY_YEAR.")

    df_investment_multiyear = pd.concat(yearly_dataframes, ignore_index=True)
    available_years = sorted(df_investment_multiyear['year'].unique().tolist())
    print(f"[INVERSIÓN MULTI-AÑO] Años cargados exitosamente: {available_years}")
    return df_investment_multiyear, available_years


def load_raw_datasets():
    """Reads all raw CSV source files into memory."""
    df_scholarship = pd.read_csv('sources/becas_creditos_educacion_superior_antioquia.csv')
    df_utility_subsidy = pd.read_csv('sources/subsidios_contribuciones_epm_servicios.csv')
    df_subsidized_health_regime_affiliates = pd.read_csv('sources/subsidiado.csv')
    df_subsidy_and_cleaning = pd.read_csv('sources/subsidios_y_contribuciones_aseo.csv')
    df_social_inclusion_actions_for_people_with_disabilities = pd.read_csv(
        'sources/implementacion_acciones_personas_discapacidad_familiares_cuidadores_2023.csv')
    df_epm_subsidies_contributions = pd.read_csv('sources/subsidio_contribuciones_epm.csv')

    return (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
            df_subsidy_and_cleaning, df_social_inclusion_actions_for_people_with_disabilities,
            df_epm_subsidies_contributions)


def print_column_names():
    """Diagnostic tool to inspect raw source columns in console logs."""
    (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
     df_subsidy_and_cleaning, df_social_inclusion_actions_for_people_with_disabilities,
     df_epm_subsidies_contributions) = load_raw_datasets()

    print('Beneficiarios de becas y créditos:', df_scholarship.columns.tolist())
    print('Subsidios y contribuciones de servicios:', df_utility_subsidy.columns.tolist())
    print('Afiliados al regimen subsidiado:', df_subsidized_health_regime_affiliates.columns.tolist())
    print('Subsidios y contribuciones aseo:', df_subsidy_and_cleaning.columns.tolist())
    print('Subsidios y Contribuciones-EPM:', df_epm_subsidies_contributions.columns.tolist())
    print('Implementación de acciones de inclusión social:',
          df_social_inclusion_actions_for_people_with_disabilities.columns.tolist())


# ---------------------------------------------------------------------------
# Stage functions (each handles one dataset's cleaning step, called from the
# orchestrator below)
# ---------------------------------------------------------------------------

def _drop_duplicates_in_place(datasets):
    """Removes exact duplicate rows from each dataset in the given list."""
    for df in datasets:
        df.drop_duplicates(inplace=True)


def _apply_geographic_filters(df_utility_subsidy, df_epm_subsidies_contributions, df_subsidy_and_cleaning):
    """Applies the Medellín geographic filter to the three city-level subsidy datasets."""
    df_utility_subsidy['Municipio o Sector'] = df_utility_subsidy['Municipio o Sector'].fillna('UNKNOWN')
    df_epm_subsidies_contributions['municipio_o_sector'] = (
        df_epm_subsidies_contributions['municipio_o_sector'].fillna('UNKNOWN')
    )

    df_utility_subsidy = filter_to_medellin(
        df_utility_subsidy, 'Municipio o Sector', 'Subsidios y Contribuciones EPM (servicios)')
    df_epm_subsidies_contributions = filter_to_medellin(
        df_epm_subsidies_contributions, 'municipio_o_sector', 'Subsidios y Contribuciones EPM (directos)')

    cleaning_geo_col = find_column(df_subsidy_and_cleaning, CLEANING_COLUMN_CANDIDATES)
    if cleaning_geo_col is not None:
        df_subsidy_and_cleaning = filter_to_medellin(
            df_subsidy_and_cleaning, cleaning_geo_col, 'Subsidios y Contribuciones Aseo')
        cleaning_scope_verified = True
    else:
        # No real geographic column; use the verified provider whitelist.
        df_subsidy_and_cleaning, cleaning_scope_verified = filter_cleaning_to_medellin_by_provider(
            df_subsidy_and_cleaning)

    return (df_utility_subsidy, df_epm_subsidies_contributions, df_subsidy_and_cleaning,
            cleaning_geo_col, cleaning_scope_verified)


def _clean_stratum_columns(df_scholarship, df_utility_subsidy,
                            df_social_inclusion_actions_for_people_with_disabilities):
    """Cleans and normalizes stratum-related columns across the relevant datasets."""
    raw_stratum_scholarship = df_scholarship['ESTRATO'].copy()
    df_scholarship['ESTRATO'] = extract_leading_number(df_scholarship['ESTRATO']).fillna(0).astype(int)
    diagnostic_zero_after_conversion(raw_stratum_scholarship, df_scholarship['ESTRATO'], 'ESTRATO', 'Becas')

    raw_stratum_utility = df_utility_subsidy['estrato'].copy()
    # Keep the raw text BEFORE normalizing, because for non-residential
    # customers this column is not a stratum number but a user category
    # (Comercio, Industria, Oficial, Especial). extract_leading_number would
    # collapse all of them to 0 for having no digits, which made deduplication
    # treat 4 distinct business segments as if they were the same repeated row.
    df_utility_subsidy['_raw_stratum_category'] = raw_stratum_utility
    df_utility_subsidy['estrato'] = extract_leading_number(df_utility_subsidy['estrato']).fillna(0).astype(int)
    diagnostic_zero_after_conversion(raw_stratum_utility, df_utility_subsidy['estrato'], 'estrato',
                                      'Subsidios EPM servicios')

    raw_stratum_inclusion = df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'].copy()
    df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'] = map_stratum_category(
        df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO']
    )
    diagnostic_zero_after_conversion(
        raw_stratum_inclusion,
        df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'],
        'ESTRATO SOCIOECONÓMICO', 'Inclusión y discapacidad')


def _dedupe_city_subsidies_by_period(df_subsidy_and_cleaning, df_utility_subsidy, df_epm_subsidies_contributions):
    """Deduplicates the three city-level subsidy datasets by their most recent period."""
    df_subsidy_and_cleaning, _, cleaning_period_info = diagnostic_and_dedupe_by_period(
        df_subsidy_and_cleaning,
        'Aseo',
        key_columns_override=['prestador'],
        period_col='periodo',  # already a real date in this dataset
    )

    utility_geo_col = find_column(df_utility_subsidy, ['Municipio o Sector', 'municipio_o_sector'])
    df_utility_subsidy, _, utility_period_info = diagnostic_and_dedupe_by_period(
        df_utility_subsidy,
        'Subsidios EPM (servicios públicos)',
        key_columns_override=[c for c in
                              ['Tipo de subsidio', 'Departamento', utility_geo_col,
                               '_raw_stratum_category', 'servicio', 'tipo']
                              if c and c in df_utility_subsidy.columns],
        year_col='año',
        month_col='Mes',
    )

    epm_direct_geo_col = find_column(df_epm_subsidies_contributions, ['municipio_o_sector', 'Municipio o Sector'])
    df_epm_subsidies_contributions, _, epm_direct_period_info = diagnostic_and_dedupe_by_period(
        df_epm_subsidies_contributions,
        'Subsidios EPM (directos)',
        key_columns_override=[c for c in
                              ['tipo_de_subsidio', 'departamento', epm_direct_geo_col, 'estrato', 'servicio', 'tipo']
                              if c and c in df_epm_subsidies_contributions.columns],
        year_col='a_o',
        month_col='mes',
    )

    return (df_subsidy_and_cleaning, df_utility_subsidy, df_epm_subsidies_contributions,
            cleaning_period_info, utility_period_info, epm_direct_period_info)


def _check_subsidies_temporal_alignment(cleaning_period_info, utility_period_info, epm_direct_period_info,
                                         exclude_epm_direct):
    """Checks whether the city-level subsidies still in use measure comparable time windows.

    When 'EPM directos' is a confirmed duplicate of 'EPM servicios', it is
    excluded from this comparison — otherwise a duplicated source would
    count twice towards the alignment check.
    """
    period_infos = [cleaning_period_info, utility_period_info]
    if not exclude_epm_direct:
        period_infos.append(epm_direct_period_info)

    available_period_max = [info.get('period_max') for info in period_infos if info]

    if len(available_period_max) >= 2:
        max_diff_days = (max(available_period_max) - min(available_period_max)).days
        periods_aligned = max_diff_days <= 31
    else:
        max_diff_days = None
        periods_aligned = None

    if periods_aligned is False:
        sources_desc = "aseo y EPM servicios" if exclude_epm_direct else "aseo, EPM servicios y EPM directos"
        print(f"[ALERTA HOMOGENEIDAD TEMPORAL] Los subsidios de ciudad ({sources_desc}) NO corresponden "
              f"al mismo periodo (diferencia máxima: {max_diff_days} días). Sumarlos como 'subsidio "
              f"combinado de ciudad' no es correcto todavía; homogeneizar la ventana temporal antes de "
              f"presentarlo.")
    elif periods_aligned is None:
        print("[ALERTA HOMOGENEIDAD TEMPORAL] No se pudo verificar si los subsidios de ciudad miden el "
              "mismo periodo (al menos uno de los datasets no tiene columna de periodo/fecha "
              "reconocible). Tratar el 'subsidio combinado de ciudad' con cautela.")
    else:
        sources_desc = "aseo y EPM servicios" if exclude_epm_direct else "aseo, EPM servicios y EPM directos"
        print(f"[HOMOGENEIDAD TEMPORAL OK] Los subsidios de ciudad ({sources_desc}) miden periodos "
              f"consistentes (diferencia máxima: {max_diff_days} días).")

    return periods_aligned, max_diff_days


def _restrict_health_affiliates_to_valid_communes(df_subsidized_health_regime_affiliates):
    """Applies age clipping and commune validation to the subsidized health regime dataset."""
    code_99_count = (df_subsidized_health_regime_affiliates['comuna'] == 99).sum()
    total_rows = len(df_subsidized_health_regime_affiliates)
    print(f"[DIAGNÓSTICO CÓDIGO 99] Régimen subsidiado: {code_99_count:,} de {total_rows:,} filas "
          f"({code_99_count / total_rows * 100:.1f}%) tienen comuna=99. La ficha técnica oficial del "
          f"dataset (diccionario de datos) NO define un valor 99 para el campo 'Comuna' (solo describe "
          f"'Número de Comuna', sin tabla de códigos como sí existe para 'Grupo_Poblacional'). Por lo tanto "
          f"NO se puede confirmar si 99 significa 'sin dato geográfico', 'zona rural' u otra categoría. "
          f"Se documenta como limitación conocida: estas filas se excluyen del análisis territorial por "
          f"comuna, pero sí están incluidas en cualquier métrica agregada a nivel de ciudad.")

    df_subsidized_health_regime_affiliates['edad'] = (
        df_subsidized_health_regime_affiliates['edad'].clip(lower=0, upper=105)
    )
    df_subsidized_health_regime_affiliates.loc[
        ~df_subsidized_health_regime_affiliates['comuna'].isin(VALID_COMMUNE_CODES), 'comuna'] = np.nan
    df_subsidized_health_regime_affiliates['commune_clean'] = (
        df_subsidized_health_regime_affiliates['comuna'].apply(clean_commune_name)
    )

    return code_99_count, total_rows


def _log_scholarship_methodology_decision(total_scholarship_before_filter, total_scholarship_medellin):
    """Logs the methodological decision to exclude scholarships from the territorial analysis, if applicable."""
    if total_scholarship_before_filter <= 0:
        return
    coverage_ratio = total_scholarship_medellin / total_scholarship_before_filter
    if coverage_ratio >= 0.02:
        return
    print(f"[DECISIÓN METODOLÓGICA - BECAS] Solo el "
          f"{coverage_ratio * 100:.2f}% de las filas "
          f"({total_scholarship_medellin} de {total_scholarship_before_filter}) quedó como 'Medellín' "
          f"tras el filtro geográfico por texto en 'MUNICIPIO DE RESIDENCIA'. El dataset es de cobertura "
          f"departamental (Antioquia), y los valores no emparejados corresponden a municipios reales "
          f"(Rionegro, Bello, Apartadó, etc.), no a errores de formato. No se pudo verificar si existe una "
          f"columna alterna de código DANE de municipio con mejor cobertura para Medellín. "
          f"DECISIÓN: dado que N={total_scholarship_medellin} es insuficiente para desagregar de forma "
          f"confiable por las 21 comunas/corregimientos, esta variable se reporta ÚNICAMENTE como métrica "
          f"agregada a nivel de ciudad (total_scholarship_beneficiaries_medellin) y se EXCLUYE del análisis "
          f"territorial por comuna y del modelo predictivo, para no introducir ruido o falsas conclusiones "
          f"por comuna basadas en muestras casi vacías.")


def _build_city_level_metrics(df_utility_subsidy, df_epm_subsidies_contributions, df_subsidy_and_cleaning,
                               total_scholarship_medellin, available_years, cleaning_scope_verified,
                               code_99_count, total_health_rows,
                               cleaning_period_info, utility_period_info, epm_direct_period_info,
                               subsidies_periods_aligned, subsidies_period_max_diff_days,
                               epm_subsidies_confirmed_duplicate, quality_scorecard):
    """Assembles the dictionary of city-wide (non-territorial) metrics."""
    return {
        'total_epm_utility_subsidy_medellin': float(df_utility_subsidy['valor'].sum()),
        'total_epm_direct_subsidy_medellin': float(df_epm_subsidies_contributions['valor'].sum()),
        'epm_valor_es_neto_subsidio_menos_contribucion': True,
        'total_cleaning_subsidy_medellin': float(df_subsidy_and_cleaning['total_subsidio'].sum()),
        'total_cleaning_subscribers_medellin': int(df_subsidy_and_cleaning['suscriptores_subsidiados'].sum()),
        'total_scholarship_beneficiaries_medellin': int(total_scholarship_medellin),
        'investment_data_years': available_years,
        'cleaning_scope_verified': cleaning_scope_verified,
        'subsidized_health_unmatched_pct': float(round(code_99_count / total_health_rows * 100, 1)) if total_health_rows else 0.0,
        'cleaning_subsidy_period_end': cleaning_period_info.get('period_max'),
        'utility_subsidy_period_end': utility_period_info.get('period_max'),
        'epm_direct_subsidy_period_end': epm_direct_period_info.get('period_max'),
        'subsidies_periods_aligned': subsidies_periods_aligned,
        'subsidies_period_max_diff_days': subsidies_period_max_diff_days,
        'epm_subsidies_confirmed_duplicate_source': epm_subsidies_confirmed_duplicate,
        'quality_scorecard': quality_scorecard
    }

def _build_territorial_aggregates(df_investment_multiyear, df_subsidized_health_regime_affiliates,
                                   df_social_inclusion_actions_for_people_with_disabilities):
    """Builds the per-commune (and per-commune-year) aggregated metrics."""
    investment_panel = df_investment_multiyear.groupby(['commune_clean', 'year']).agg(
        total_investment=('investment_value', 'sum')).reset_index()

    investment_display = investment_panel.groupby('commune_clean').agg(
        avg_annual_investment=('total_investment', 'mean'),
        n_years_with_data=('year', 'nunique')).reset_index()

    health_aggregate = df_subsidized_health_regime_affiliates.groupby('commune_clean').agg(
        total_subsidized_health_affiliates=('consecutivo', 'count'),
        mean_health_age=('edad', 'mean')).reset_index()
    health_aggregate['health_affiliates_share'] = (
        health_aggregate['total_subsidized_health_affiliates'] /
        health_aggregate['total_subsidized_health_affiliates'].sum()
    )

    inclusion_aggregate = df_social_inclusion_actions_for_people_with_disabilities.groupby('commune_clean').agg(
        total_disabled_and_inclusion_beneficiaries=('CONDICIÓN DE DISCAPACIDAD', 'count'),
        mean_inclusion_age=('AÑOS CUMPLIDOS AL INGRESO DEL PROGRAMA', 'mean')).reset_index()
    inclusion_aggregate['inclusion_share'] = (
        inclusion_aggregate['total_disabled_and_inclusion_beneficiaries'] /
        inclusion_aggregate['total_disabled_and_inclusion_beneficiaries'].sum()
    )

    # METHODOLOGICAL NOTE (FYI, requires no immediate action):
    # 'mean_utility_stratum' -- one of the 4 actual variables feeding
    # the model, see MODEL_FEATURE_COLUMNS -- is calculated here from
    # 'ESTRATO SOCIOECONÓMICO' within the inclusion and disability dataset
    # (df_social_inclusion_actions_for_people_with_disabilities), which only
    # covers 8,021 rows across the entire city. It is NOT calculated from the
    # EPM dataset (df_utility_subsidy), which has a much larger subscriber
    # base and would theoretically be a more representative source of the
    # "true" stratum per commune.
    #
    # The EPM data is used, but only as a fallback (see reference_global_stratum
    # in process_and_create_master_matrix) for communes with missing inclusion/disability
    # data -- meaning two different sources feed the same concept depending on the case.
    #
    # This is not an error, but it is a known limitation: coming from a
    # small and specific subsample (disability program beneficiaries), the
    # average stratum per commune may be noisy or unrepresentative of the
    # commune as a whole. This is a potential partial explanation for the
    # non-monotonic effect that the PDP diagnosis in model_trainer.py
    # (diagnostic_partial_dependence_stratum) already reports for this variable.
    stratum_aggregate = df_social_inclusion_actions_for_people_with_disabilities.groupby('commune_clean').agg(
        mean_utility_stratum=('ESTRATO SOCIOECONÓMICO', 'mean')).reset_index()

    return investment_panel, investment_display, health_aggregate, inclusion_aggregate, stratum_aggregate


def _assemble_display_matrix(investment_display, health_aggregate, inclusion_aggregate, stratum_aggregate,
                              reference_global_stratum):
    """Builds the 1-row-per-commune matrix used for the dashboard/chatbot."""
    matrix = pd.DataFrame({'commune_clean': MEDELLIN_TERRITORIES})
    matrix = pd.merge(matrix, investment_display, on='commune_clean', how='left')
    matrix = pd.merge(matrix, health_aggregate, on='commune_clean', how='left')
    matrix = pd.merge(matrix, inclusion_aggregate, on='commune_clean', how='left')
    matrix = pd.merge(matrix, stratum_aggregate, on='commune_clean', how='left')

    columns_to_zero_fill = [
        'avg_annual_investment', 'n_years_with_data', 'total_subsidized_health_affiliates', 'mean_health_age',
        'total_disabled_and_inclusion_beneficiaries', 'mean_inclusion_age',
        'health_affiliates_share', 'inclusion_share'
    ]
    matrix[columns_to_zero_fill] = matrix[columns_to_zero_fill].fillna(0)
    matrix['mean_utility_stratum'] = matrix['mean_utility_stratum'].fillna(reference_global_stratum)

    return matrix


def _assemble_panel_matrix(investment_panel, health_aggregate, inclusion_aggregate, stratum_aggregate,
                            available_years, reference_global_stratum):
    """Builds the 1-row-per-commune-per-year matrix used to train the model."""
    panel_index = pd.MultiIndex.from_product(
        [MEDELLIN_TERRITORIES, available_years], names=['commune_clean', 'year']
    ).to_frame(index=False)

    panel = pd.merge(panel_index, investment_panel, on=['commune_clean', 'year'], how='left')
    panel = pd.merge(panel, health_aggregate, on='commune_clean', how='left')
    panel = pd.merge(panel, inclusion_aggregate, on='commune_clean', how='left')
    panel = pd.merge(panel, stratum_aggregate, on='commune_clean', how='left')

    columns_to_zero_fill = [
        'total_investment', 'total_subsidized_health_affiliates', 'mean_health_age',
        'total_disabled_and_inclusion_beneficiaries', 'mean_inclusion_age',
        'health_affiliates_share', 'inclusion_share'
    ]
    panel[columns_to_zero_fill] = panel[columns_to_zero_fill].fillna(0)
    panel['mean_utility_stratum'] = panel['mean_utility_stratum'].fillna(reference_global_stratum)

    return panel


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def process_and_create_master_matrix():
    print("Iniciando la carga de archivos CSV...")

    (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
     df_subsidy_and_cleaning, df_social_inclusion_actions_for_people_with_disabilities,
     df_epm_subsidies_contributions) = load_raw_datasets()

    print("Cargando datasets de inversión multi-año (2015-2018)...")
    df_investment_multiyear, available_years = load_investment_multiyear()

    total_scholarship_before_filter = len(df_scholarship)
    df_scholarship = filter_to_medellin(df_scholarship, 'MUNICIPIO DE RESIDENCIA',
                                        'Becas y créditos educación superior')

    print("Ejecutando purga automática de filas duplicadas y corruptas...")
    _drop_duplicates_in_place([
        df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
        df_subsidy_and_cleaning, df_investment_multiyear,
        df_social_inclusion_actions_for_people_with_disabilities, df_epm_subsidies_contributions,
    ])

    (df_utility_subsidy, df_epm_subsidies_contributions, df_subsidy_and_cleaning,
     cleaning_geo_col, cleaning_scope_verified) = _apply_geographic_filters(
        df_utility_subsidy, df_epm_subsidies_contributions, df_subsidy_and_cleaning)

    print("Procesando y normalizando variables territoriales...")
    df_social_inclusion_actions_for_people_with_disabilities['commune_clean'] = (
        df_social_inclusion_actions_for_people_with_disabilities['COMUNA DE RESIDENCIA'].apply(clean_commune_name)
    )

    diagnostic_unmatched_communes(df_subsidized_health_regime_affiliates, 'comuna', 'Régimen subsidiado (salud)')
    diagnostic_unmatched_communes(df_social_inclusion_actions_for_people_with_disabilities,
                                   'COMUNA DE RESIDENCIA', 'Inclusión y discapacidad')

    print("Limpiando formatos monetarios y variables categóricas...")
    _clean_stratum_columns(df_scholarship, df_utility_subsidy,
                            df_social_inclusion_actions_for_people_with_disabilities)

    (df_subsidy_and_cleaning, df_utility_subsidy, df_epm_subsidies_contributions,
     cleaning_period_info, utility_period_info, epm_direct_period_info) = _dedupe_city_subsidies_by_period(
        df_subsidy_and_cleaning, df_utility_subsidy, df_epm_subsidies_contributions)

    print("Calculando scorecard de calidad de datos (6 dimensiones)...")
    investment_period_end = pd.Timestamp(year=max(available_years), month=12, day=31)
    quality_scorecard = build_quality_scorecard([
        {
            'df': df_investment_multiyear, 'label': 'Inversión multi-año',
            'required_cols': ['commune_clean', 'investment_value', 'year'],
            'key_cols': [],
            'period_end': investment_period_end,
        },
        {
            'df': df_subsidized_health_regime_affiliates, 'label': 'Régimen subsidiado (salud)',
            'required_cols': ['comuna', 'edad'],
            'key_cols': ['consecutivo'],
            'validity_column': 'edad',
            'validity_fn': lambda x: 0 <= x <= 105,
        },
        {
            'df': df_utility_subsidy, 'label': 'Subsidios EPM servicios',
            'required_cols': ['valor', 'estrato'],
            'key_cols': [c for c in
                         ['Tipo de subsidio', 'Departamento', 'Municipio o Sector',
                          '_raw_stratum_category', 'servicio', 'tipo', 'año', 'Mes']
                         if c in df_utility_subsidy.columns],
            'period_end': utility_period_info.get('period_max'),
        },
        {
            'df': df_subsidy_and_cleaning, 'label': 'Subsidios Aseo',
            'required_cols': ['total_subsidio', 'suscriptores_subsidiados'],
            'key_cols': ['prestador'],
            'period_end': cleaning_period_info.get('period_max'),
        },
    ])

    df_subsidy_and_cleaning['suscriptores_subsidiados'] = pd.to_numeric(
        df_subsidy_and_cleaning['suscriptores_subsidiados'], errors='coerce').fillna(0).astype(int)

    diagnostic_outlier_check(
        df_subsidy_and_cleaning,
        'suscriptores_subsidiados',
        'Suscriptores subsidiados aseo',
        id_columns=[cleaning_geo_col] if cleaning_geo_col else None,
        population_reference=CLEANING_SUBSCRIBERS_POPULATION_REFERENCE,
    )

    df_subsidy_and_cleaning['total_subsidio'] = robust_numeric_clean(
        df_subsidy_and_cleaning['total_subsidio'], 'Aseo (total_subsidio)')
    df_utility_subsidy['valor'] = robust_numeric_clean(df_utility_subsidy['valor'], 'EPM servicios (valor)')
    df_epm_subsidies_contributions['valor'] = robust_numeric_clean(
        df_epm_subsidies_contributions['valor'], 'EPM directos (valor)')

    epm_subsidies_confirmed_duplicate = diagnostic_check_duplicate_subsidy_sources(
        df_utility_subsidy, df_epm_subsidies_contributions)

    print("Aplicando restricciones lógicas a variables demográficas...")
    code_99_count, total_health_rows = _restrict_health_affiliates_to_valid_communes(
        df_subsidized_health_regime_affiliates)

    print("Generando agregaciones REALES por comuna (sin fuga de datos ni mezcla geográfica)...")
    (investment_panel, investment_display, health_aggregate,
     inclusion_aggregate, stratum_aggregate) = _build_territorial_aggregates(
        df_investment_multiyear, df_subsidized_health_regime_affiliates,
        df_social_inclusion_actions_for_people_with_disabilities)

    total_scholarship_medellin = len(df_scholarship)

    # See methodological note in _build_territorial_aggregates: this average
    # comes from a different source (EPM) than the one used for the stratum by
    # commune (inclusion/disability). It is used solely as a fallback value
    # for communes with missing data, not as the main source of the feature.
    reference_global_stratum = df_utility_subsidy.loc[df_utility_subsidy['estrato'] > 0, 'estrato'].mean()
    if pd.isna(reference_global_stratum) or reference_global_stratum == 0:
        reference_global_stratum = REFERENCE_STRATUM_FALLBACK

    subsidies_periods_aligned, subsidies_period_max_diff_days = _check_subsidies_temporal_alignment(
        cleaning_period_info, utility_period_info, epm_direct_period_info,
        exclude_epm_direct=epm_subsidies_confirmed_duplicate)

    # Consistency (dimension that was missing in the scorecard, see HU-23): it is
    # integrated here because it depends on signals that do not exist yet when
    # build_quality_scorecard runs above. It reuses the temporal alignment of
    # periods and the duplicate detection between EPM services/directs, instead
    # of inventing a new metric.
    print("Integrando dimensión de Consistencia al scorecard de calidad...")
    cross_source_checks = []
    if subsidies_periods_aligned is not None:
        cross_source_checks.append(subsidies_periods_aligned)
    cross_source_checks.append(epm_subsidies_confirmed_duplicate)
    consistency_score = compute_consistency(cross_source_checks, 'Subsidios de ciudad (EPM + Aseo)')
    for label in ('Subsidios EPM servicios', 'Subsidios Aseo'):
        if label in quality_scorecard:
            quality_scorecard[label]['consistencia'] = consistency_score

    city_level_metrics = _build_city_level_metrics(
        df_utility_subsidy, df_epm_subsidies_contributions, df_subsidy_and_cleaning,
        total_scholarship_medellin, available_years, cleaning_scope_verified,
        code_99_count, total_health_rows,
        cleaning_period_info, utility_period_info, epm_direct_period_info,
        subsidies_periods_aligned, subsidies_period_max_diff_days,
        epm_subsidies_confirmed_duplicate,
        quality_scorecard)
    print(f"[MÉTRICAS DE CIUDAD] {city_level_metrics}")

    _log_scholarship_methodology_decision(total_scholarship_before_filter, total_scholarship_medellin)

    print("Consolidando Matriz Maestra Analítica (Data Mashup Híbrido, sin fuga de datos)...")
    master_matrix = _assemble_display_matrix(
        investment_display, health_aggregate, inclusion_aggregate, stratum_aggregate, reference_global_stratum)
    master_matrix.attrs['city_level_metrics'] = city_level_metrics

    master_matrix_panel = _assemble_panel_matrix(
        investment_panel, health_aggregate, inclusion_aggregate, stratum_aggregate,
        available_years, reference_global_stratum)

    print(f"[PANEL MULTI-AÑO] {len(master_matrix_panel)} filas de entrenamiento "
          f"({len(MEDELLIN_TERRITORIES)} territorios x {len(available_years)} años).")

    diagnostic_correlation_check(master_matrix_panel, label_for_log="Panel multi-año")

    return master_matrix, city_level_metrics, master_matrix_panel