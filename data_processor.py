# data_processor.py

import re
import unicodedata
import numpy as np
import pandas as pd

INVESTMENT_UNIT_MULTIPLIER_BY_YEAR = {
    2015: 1_000_000,
    2016: 1_000_000,
    2017: 1_000_000,
    2018: 1_000_000,
}
INVESTMENT_UNIT_MULTIPLIER_DEFAULT = 1_000_000
CLEANING_COLUMN_CANDIDATES = [
    'MUNICIPIO DE RESIDENCIA', 'municipio_de_residencia', 'Municipio de Residencia',
    'municipio_o_sector', 'Municipio o Sector', 'municipio', 'Municipio', 'MUNICIPIO',
]

INVESTMENT_FILES_BY_YEAR = {
    2015: 'sources/inversion_por_comunas_y_corregimientos_2015_medellin.csv',
    2016: 'sources/inversion_por_comunas_y_corregimientos_2016_medellin.csv',
    2017: 'sources/inversion_por_comunas_y_corregimientos_2017_medellin.csv',
    2018: 'sources/inversion_por_comunas_y_corregimientos_2018.csv',
}

INVESTMENT_COLUMN_CANDIDATES = {
    'comuna_name': ['Nombre Comuna', 'nombre_comuna', 'NOMBRE_COMUNA', 'NOMBRE COMUNA',
                    'Comuna', 'comuna', 'COMUNA'],
    'comuna_id_for_dropna': ['Comuna', 'comuna', 'COMUNA', 'Codigo Comuna', 'codigo_comuna',
                             'CODIGO_COMUNA'],
    'valor_inversion': ['Inversion', 'inversion', 'INVERSION', 'Valor Inversion',
                        'valor_inversion', 'Valor', 'VALOR', 'Monto', 'monto'],
}

MODEL_FEATURE_COLUMNS = [
    "health_affiliates_share",
    "inclusion_share",
    "mean_utility_stratum",
    "anio"
]

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

CLEANING_PRESTADORES_MEDELLIN = [
    'Empresas Varias de Medellin',
]


def filter_cleaning_to_medellin_by_prestador(df, label_for_log="Subsidios y Contribuciones Aseo"):
    if 'prestador' not in df.columns:
        print(f"[ALERTA ASEO] No existe la columna 'prestador' en {label_for_log}. No se puede filtrar.")
        return df, False

    mask = df['prestador'].isin(CLEANING_PRESTADORES_MEDELLIN)
    filtered = df[mask].copy()
    prestadores_incluidos = sorted(df.loc[mask, 'prestador'].unique().tolist())
    prestadores_excluidos = sorted(df.loc[~mask, 'prestador'].unique().tolist())

    print(f"[FILTRO GEOGRÁFICO (whitelist prestador)] {label_for_log}: {len(df)} filas -> {len(filtered)} filas. "
          f"Prestadores incluidos: {prestadores_incluidos}. "
          f"Prestadores excluidos ({len(prestadores_excluidos)}): {prestadores_excluidos[:10]}"
          f"{'...' if len(prestadores_excluidos) > 10 else ''}")

    return filtered, True


def map_stratum_category(series):
    """Normalizes and maps string-based stratum descriptions to numbers."""
    normalized = series.astype(str).str.upper().str.strip()
    return normalized.map(STRATUM_CATEGORY_TO_NUMBER)


def _strip_accents(text):
    """Removes accents and diacritics from a string."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(ch for ch in nfkd if not unicodedata.combining(ch))


def clean_commune_name(text):
    """Standardizes raw commune names into unified alphanumeric keys."""
    if pd.isna(text):
        return "UNKNOWN"

    text = _strip_accents(str(text).upper().strip())

    match = re.search(r'\d+', text)
    num = int(match.group()) if match else None

    if 'POPULAR' in text or num == 1:
        return '01 - POPULAR'
    elif 'SANTA CRUZ' in text or num == 2:
        return '02 - SANTA CRUZ'
    elif 'MANRIQUE' in text or num == 3:
        return '03 - MANRIQUE'
    elif 'ARANJUEZ' in text or num == 4:
        return '04 - ARANJUEZ'
    elif 'CASTILLA' in text or num == 5:
        return '05 - CASTILLA'
    elif 'DOCE DE OCTUBRE' in text or num == 6:
        return '06 - DOCE DE OCTUBRE'
    elif 'ROBLEDO' in text or num == 7:
        return '07 - ROBLEDO'
    elif 'VILLA HERMOSA' in text or num == 8:
        return '08 - VILLA HERMOSA'
    elif 'BUENOS AIRES' in text or num == 9:
        return '09 - BUENOS AIRES'
    elif 'LA CANDELARIA' in text or num == 10:
        return '10 - LA CANDELARIA'
    elif 'LAURELES' in text or num == 11:
        return '11 - LAURELES ESTADIO'
    elif 'LA AMERICA' in text or num == 12:
        return '12 - LA AMERICA'
    elif 'SAN JAVIER' in text or num == 13:
        return '13 - SAN JAVIER'
    elif 'POBLADO' in text or num == 14:
        return '14 - EL POBLADO'
    elif 'GUAYABAL' in text or num == 15:
        return '15 - GUAYABAL'
    elif 'BELEN' in text or num == 16:
        return '16 - BELEN'
    elif 'PALMITAS' in text or num == 50:
        return '50 - SAN SEBASTIÁN DE PALMITAS'
    elif 'SAN CRISTOBAL' in text or num == 60:
        return '60 - SAN CRISTÓBAL'
    elif 'ALTAVISTA' in text or num == 70:
        return '70 - ALTAVISTA'
    elif 'SAN ANTONIO' in text or 'PRADO' in text or num == 80:
        return '80 - SAN ANTONIO DE PRADO'
    elif 'SANTA ELENA' in text or num == 90:
        return '90 - SANTA ELENA'
    else:
        return 'OTHER_ZONE'


def diagnostic_unmatched_communes(df, raw_column, label_for_log):
    if raw_column not in df.columns:
        print(f"[DIAGNÓSTICO COMUNAS] Columna '{raw_column}' no existe en {label_for_log}.")
        return

    total = len(df)
    mask_other = df[raw_column].apply(clean_commune_name) == 'OTHER_ZONE'
    n_other = mask_other.sum()
    pct_other = (n_other / total * 100) if total else 0

    if n_other > 0:
        top_values = df.loc[mask_other, raw_column].astype(str).value_counts().head(10)
        print(f"[DIAGNÓSTICO COMUNAS] {label_for_log}: {n_other:,} de {total:,} filas "
              f"({pct_other:.1f}%) NO emparejadas a ninguna comuna válida (cayeron en 'OTHER_ZONE').")
        print(f"  └─ Top valores crudos sin match (valor: conteo de filas):")
        for val, cnt in top_values.items():
            print(f"       '{val}': {cnt:,} filas")
        if pct_other > 30:
            print(f"  ⚠️ ALERTA: {pct_other:.1f}% de '{label_for_log}' quedó sin comuna válida. "
                  f"Confirma si esta columna realmente corresponde a comunas de Medellín "
                  f"(1-16, 50-90) o si el dataset cubre otros municipios/categorías que "
                  f"deben excluirse por diseño (en cuyo caso puede ser normal).")
    else:
        print(f"[DIAGNÓSTICO COMUNAS] {label_for_log}: 100% de las {total:,} filas emparejadas correctamente.")


def filter_to_medellin(df, column, label_for_log):
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
        top_no_match = normalized[~mask].value_counts().head(10)
        print(f"  ⚠️ ALERTA: solo el {pct_kept:.2f}% quedó como Medellín en '{column}'. "
              f"Top valores NO emparejados:")
        for val, cnt in top_no_match.items():
            print(f"       '{val}': {cnt} filas")

    return filtered


def _find_column(df, candidates):
    normalized_lookup = {
        _strip_accents(str(col)).upper().strip(): col
        for col in df.columns
    }
    for c in candidates:
        key = _strip_accents(str(c)).upper().strip()
        if key in normalized_lookup:
            return normalized_lookup[key]
    return None

def robust_numeric_clean(series):
    """Cleans numeric formats from strings with diverse decimal/thousands separators."""
    s = series.astype(str).str.replace(r'[^\d,.-]', '', regex=True).str.strip()

    def fix_separators(x):
        if not x:
            return "0"
        if '.' in x and ',' not in x:
            parts = x.split('.')
            if len(parts[-1]) == 3:
                return x.replace('.', '')

        if ',' in x and '.' in x:
            return x.replace('.', '').replace(',', '.')
        elif ',' in x:
            return x.replace(',', '.')

        return x

    s = s.apply(fix_separators)
    return pd.to_numeric(s, errors='coerce').fillna(0.0)


def load_investment_year(path, year):
    """Loads and normalizes raw investment data for a specific year."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        print(f"[ALERTA INVERSIÓN {year}] No se encontró el archivo '{path}'. Se omite ese año.")
        return None

    name_col = _find_column(df, INVESTMENT_COLUMN_CANDIDATES['comuna_name'])
    if name_col is None:
        print(f"[ALERTA INVERSIÓN {year}] No se encontró columna de nombre de comuna en '{path}'. "
              f"Columnas disponibles: {df.columns.tolist()}. Se omite ese año.")
        return None

    dropna_col = _find_column(df, INVESTMENT_COLUMN_CANDIDATES['comuna_id_for_dropna']) or name_col
    df = df.dropna(subset=[dropna_col]).copy()

    val_col = _find_column(df, INVESTMENT_COLUMN_CANDIDATES['valor_inversion'])
    if val_col is None:
        print(f"[ALERTA INVERSIÓN {year}] No se encontró columna de valor de inversión en '{path}'. "
              f"Columnas disponibles: {df.columns.tolist()}. Se omite ese año.")
        return None

    df['commune_clean'] = df[name_col].apply(clean_commune_name)
    diagnostic_unmatched_communes(df, name_col, f'Inversión por comuna {year}')

    multiplier = INVESTMENT_UNIT_MULTIPLIER_BY_YEAR.get(year, INVESTMENT_UNIT_MULTIPLIER_DEFAULT)
    df['Inversion'] = robust_numeric_clean(df[val_col]) * multiplier
    df['anio'] = year

    print(f"[CARGA INVERSIÓN {year}] '{path}': {len(df)} filas cargadas "
          f"(columna comuna='{name_col}', columna valor='{val_col}').")

    return df[['commune_clean', 'Inversion', 'anio']]


def load_investment_multianio():
    """Aggregates multi-year investment records into a single multi-year dataset."""
    dfs = []
    for year, path in sorted(INVESTMENT_FILES_BY_YEAR.items()):
        df_year = load_investment_year(path, year)
        if df_year is not None:
            dfs.append(df_year)

    if not dfs:
        raise RuntimeError("[ERROR INVERSIÓN] No se pudo cargar NINGÚN año de inversión. "
                            "Revisa las rutas en INVESTMENT_FILES_BY_YEAR.")

    df_investment_multianio = pd.concat(dfs, ignore_index=True)
    available_years = sorted(df_investment_multianio['anio'].unique().tolist())
    print(f"[INVERSIÓN MULTI-AÑO] Años cargados exitosamente: {available_years}")
    return df_investment_multianio, available_years


def load_raw_datasets():
    """Reads all raw CSV source files into memory."""
    df_scholarship = pd.read_csv(
        'sources/Beneficiaros_de_becas_y_creditos_de_programas_de_acceso_a_la_educación_superior_de_Antioquia_20260617.csv')
    df_utility_subsidy = pd.read_csv(
        'sources/Subsidios_y_Contribuciones_de_Servicios_Públicos_Domiciliarios_–_EPM_20260617.csv')
    df_subsidized_health_regime_affiliates = pd.read_csv('sources/subsidiado.csv')
    df_subsidy_and_cleaning = pd.read_csv('sources/subsidios_y_contribuciones_aseo.csv')
    df_social_inclusion_actions_for_people_with_disabilities = pd.read_csv(
        'sources/implementacion_acciones_personas_discapacidad_familiares_cuidadores_2023.csv')
    df_epm_subsidies_contributions = pd.read_csv('sources/subsidio_contribuciones_epm.csv')

    return (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
            df_subsidy_and_cleaning, df_social_inclusion_actions_for_people_with_disabilities,
            df_epm_subsidies_contributions)


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
            for col, val in critical_nulls.items():
                print(f"  └─ Columna '{col}': {val} filas faltantes ({val / len(df) * 100:.2f}%)")
        else:
            print("✅ GESTIÓN: Cero celdas nulas o faltantes detectadas.")

        duplicates = df.duplicated().sum()
        if duplicates > 0:
            print(f"❌ MALA GESTIÓN: ¡Se detectaron {duplicates} filas idénticas duplicadas!")
        else:
            print("✅ GESTIÓN: Cero filas duplicadas en este entorno.")

    print("\n" + "=" * 65)


def extract_leading_number(series):
    """Extracts numeric values located at the beginning of parsed strings."""
    extracted = series.astype(str).str.extract(r'(\d+)')[0]
    return pd.to_numeric(extracted, errors='coerce')


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
    Shows the rows with the highest values of column_name to detect
    if an aggregated total is being inflated by one or a few outliers
    (e.g., a mistyped value, a row accumulated by mistake, etc.).
    population_reference: if passed, it compares each individual value against that
    number (e.g., the population of Medellín) and alerts if a single row already exceeds it.
    """
    if column_name not in df.columns:
        print(f"[DIAGNÓSTICO OUTLIERS] Columna '{column_name}' no existe en {label_for_log}.")
        return

    id_columns = [c for c in (id_columns or []) if c in df.columns]
    cols_to_show = id_columns + [column_name]

    top_rows = df.sort_values(by=column_name, ascending=False).head(top_n)
    total = df[column_name].sum()

    print(f"[DIAGNÓSTICO OUTLIERS] {label_for_log}: total sumado de '{column_name}' = {total:,.2f}")
    print(f"  └─ Top {top_n} filas con mayor valor individual:")
    for _, row in top_rows.iterrows():
        detalle = ", ".join(f"{c}={row[c]}" for c in cols_to_show)
        pct_del_total = (row[column_name] / total * 100) if total else 0
        print(f"       {detalle}  ({pct_del_total:.1f}% del total)")

    if population_reference is not None:
        max_valor = df[column_name].max()
        if max_valor > population_reference:
            print(f"  ⚠️ ALERTA: el valor máximo individual ({max_valor:,.0f}) ya supera la "
                  f"referencia de población ({population_reference:,.0f}). Revisar esa fila "
                  f"antes de confiar en el total agregado.")


def diagnostic_correlation_check(df_analytics, label_for_log="Panel"):
    """Evaluates mathematical correlations against the core investment metric."""
    print(f"\n[DIAGNÓSTICO CORRELACIÓN - {label_for_log}] Relación entre variables y total_investment "
          f"(N={len(df_analytics)}):")
    for col in ["total_subsidized_health_affiliates", "total_disabled_and_inclusion_beneficiaries",
                "mean_utility_stratum"]:
        if col in df_analytics.columns:
            corr = df_analytics[col].corr(df_analytics["total_investment"])
            signo = "POSITIVA (a más X, más inversión)" if corr > 0 else "NEGATIVA (a más X, menos inversión)"
            print(f"  └─ {col}: r = {corr:.3f} -> {signo}")


def process_and_create_master_matrix():
    print("Iniciando la carga de archivos CSV...")

    (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
     df_subsidy_and_cleaning, df_social_inclusion_actions_for_people_with_disabilities,
     df_epm_subsidies_contributions) = load_raw_datasets()

    print("Cargando datasets de inversión multi-año (2015-2018)...")
    df_investment_multianio, available_years = load_investment_multianio()

    total_scholarship_before_filter = len(df_scholarship)

    df_scholarship = filter_to_medellin(df_scholarship, 'MUNICIPIO DE RESIDENCIA',
                                        'Becas y créditos educación superior')

    print("Ejecutando purga automática de filas duplicadas y corruptas...")
    df_scholarship.drop_duplicates(inplace=True)
    df_utility_subsidy.drop_duplicates(inplace=True)
    df_subsidized_health_regime_affiliates.drop_duplicates(inplace=True)
    df_subsidy_and_cleaning.drop_duplicates(inplace=True)
    df_investment_multianio.drop_duplicates(inplace=True)
    df_social_inclusion_actions_for_people_with_disabilities.drop_duplicates(inplace=True)
    df_epm_subsidies_contributions.drop_duplicates(inplace=True)

    df_utility_subsidy['Municipio o Sector'] = df_utility_subsidy['Municipio o Sector'].fillna('UNKNOWN')
    df_epm_subsidies_contributions['municipio_o_sector'] = df_epm_subsidies_contributions['municipio_o_sector'].fillna('UNKNOWN')

    df_utility_subsidy = filter_to_medellin(df_utility_subsidy, 'Municipio o Sector', 'Subsidios y Contribuciones EPM (servicios)')
    df_epm_subsidies_contributions = filter_to_medellin(df_epm_subsidies_contributions, 'municipio_o_sector', 'Subsidios y Contribuciones EPM (directos)')

    cleaning_geo_col = _find_column(df_subsidy_and_cleaning, CLEANING_COLUMN_CANDIDATES)
    if cleaning_geo_col is not None:
        df_subsidy_and_cleaning = filter_to_medellin(
            df_subsidy_and_cleaning, cleaning_geo_col, 'Subsidios y Contribuciones Aseo')
        cleaning_scope_verified = True
    else:
        # No real geographic column; uses the verified provider whitelist.
        df_subsidy_and_cleaning, cleaning_scope_verified = filter_cleaning_to_medellin_by_prestador(
            df_subsidy_and_cleaning)

    print("Procesando y normalizando variables territoriales...")
    df_subsidized_health_regime_affiliates['commune_clean'] = df_subsidized_health_regime_affiliates['comuna'].apply(clean_commune_name)
    df_social_inclusion_actions_for_people_with_disabilities['commune_clean'] = \
        df_social_inclusion_actions_for_people_with_disabilities['COMUNA DE RESIDENCIA'].apply(clean_commune_name)

    diagnostic_unmatched_communes(df_subsidized_health_regime_affiliates, 'comuna', 'Régimen subsidiado (salud)')
    diagnostic_unmatched_communes(df_social_inclusion_actions_for_people_with_disabilities,
                                   'COMUNA DE RESIDENCIA', 'Inclusión y discapacidad')

    print("Limpiando formatos monetarios y variables categóricas...")
    _raw_estrato_scholarship = df_scholarship['ESTRATO'].copy()
    df_scholarship['ESTRATO'] = extract_leading_number(df_scholarship['ESTRATO']).fillna(0).astype(int)
    diagnostic_zero_after_conversion(_raw_estrato_scholarship, df_scholarship['ESTRATO'], 'ESTRATO', 'Becas')

    _raw_estrato_utility = df_utility_subsidy['estrato'].copy()
    df_utility_subsidy['estrato'] = extract_leading_number(df_utility_subsidy['estrato']).fillna(0).astype(int)
    diagnostic_zero_after_conversion(_raw_estrato_utility, df_utility_subsidy['estrato'], 'estrato',
                                     'Subsidios EPM servicios')

    _raw_estrato_inclusion = df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'].copy()
    df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'] = map_stratum_category(
        df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO']
    )
    diagnostic_zero_after_conversion(_raw_estrato_inclusion,
                                     df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'],
                                     'ESTRATO SOCIOECONÓMICO', 'Inclusión y discapacidad')
    periodo_col = _find_column(df_subsidy_and_cleaning, ['periodo', 'Periodo', 'PERIODO', 'fecha', 'Fecha', 'FECHA'])
    if periodo_col is not None:
        df_subsidy_and_cleaning[periodo_col] = pd.to_datetime(
            df_subsidy_and_cleaning[periodo_col], dayfirst=True, errors='coerce')

        key_cols = [c for c in ['prestador', 'Prestador'] if c in df_subsidy_and_cleaning.columns]
        if key_cols:
            n_periodos_por_prestador = df_subsidy_and_cleaning.groupby(key_cols[0])[periodo_col].nunique()
            print(f"[DIAGNÓSTICO PERIODOS] Aseo: columna de periodo = '{periodo_col}'. "
                  f"Rango {df_subsidy_and_cleaning[periodo_col].min()} -> {df_subsidy_and_cleaning[periodo_col].max()}. "
                  f"Promedio de {n_periodos_por_prestador.mean():.1f} periodos distintos por prestador "
                  f"(máx {n_periodos_por_prestador.max()}).")

            filas_antes = len(df_subsidy_and_cleaning)
            df_subsidy_and_cleaning = (
                df_subsidy_and_cleaning
                .sort_values(periodo_col)
                .drop_duplicates(subset=key_cols, keep='last')
            )
            print(f"[DEDUPLICACIÓN PERIODOS] Aseo: {filas_antes} filas -> {len(df_subsidy_and_cleaning)} filas "
                  f"(quedándose solo con el periodo más reciente por prestador, para no sumar meses duplicados).")
        else:
            print(f"[ALERTA PERIODOS] Aseo: se detectó columna de periodo ('{periodo_col}') pero no hay "
                  "columna de prestador para deduplicar por entidad; revisar manualmente si hay doble conteo.")
    else:
        print("[DIAGNÓSTICO PERIODOS] Aseo: no se encontró columna de periodo/fecha reconocida "
              "(se buscaron: periodo, fecha). Si el archivo es mensual, esto puede causar doble conteo al sumar.")
    df_subsidy_and_cleaning['suscriptores_subsidiados'] = pd.to_numeric(
        df_subsidy_and_cleaning['suscriptores_subsidiados'], errors='coerce').fillna(0).astype(int)

    # 🆕 Outlier check before relying on the total sum of subscribers
    diagnostic_outlier_check(
        df_subsidy_and_cleaning,
        'suscriptores_subsidiados',
        'Suscriptores subsidiados aseo',
        id_columns=[cleaning_geo_col] if cleaning_geo_col else None,
        population_reference=2_600_000,  # población aprox. de Medellín
    )

    df_subsidy_and_cleaning['total_subsidio'] = robust_numeric_clean(df_subsidy_and_cleaning['total_subsidio'])
    df_utility_subsidy['valor'] = robust_numeric_clean(df_utility_subsidy['valor'])
    df_epm_subsidies_contributions['valor'] = robust_numeric_clean(df_epm_subsidies_contributions['valor'])

    print("Aplicando restricciones lógicas a variables demográficas...")
    codigo_99_count = (df_subsidized_health_regime_affiliates['comuna'] == 99).sum()
    total_filas = len(df_subsidized_health_regime_affiliates)
    print(f"[DIAGNÓSTICO CÓDIGO 99] Régimen subsidiado: {codigo_99_count:,} de {total_filas:,} filas "
          f"({codigo_99_count / total_filas * 100:.1f}%) tienen comuna=99. La ficha técnica oficial del "
          f"dataset (diccionario de datos) NO define un valor 99 para el campo 'Comuna' (solo describe "
          f"'Número de Comuna', sin tabla de códigos como sí existe para 'Grupo_Poblacional'). Por lo tanto "
          f"NO se puede confirmar si 99 significa 'sin dato geográfico', 'zona rural' u otra categoría. "
          f"Se documenta como limitación conocida: estas filas se excluyen del análisis territorial por "
          f"comuna, pero sí están incluidas en cualquier métrica agregada a nivel de ciudad.")

    df_subsidized_health_regime_affiliates['edad'] = df_subsidized_health_regime_affiliates['edad'].clip(lower=0,
                                                                                                         upper=105)
    valid_communes = list(range(1, 17)) + [50, 60, 70, 80, 90]
    df_subsidized_health_regime_affiliates.loc[
        ~df_subsidized_health_regime_affiliates['comuna'].isin(valid_communes), 'comuna'] = np.nan
    df_subsidized_health_regime_affiliates['commune_clean'] = df_subsidized_health_regime_affiliates['comuna'].apply(
        clean_commune_name)

    print("Generando agregaciones REALES por comuna (sin fuga de datos ni mezcla geográfica)...")

    agg_investment_panel = df_investment_multianio.groupby(['commune_clean', 'anio']).agg(
        total_investment=('Inversion', 'sum')).reset_index()

    agg_investment_display = agg_investment_panel.groupby('commune_clean').agg(
        total_investment=('total_investment', 'mean'),
        n_years_with_data=('anio', 'nunique')).reset_index()

    agg_health = df_subsidized_health_regime_affiliates.groupby('commune_clean').agg(
        total_subsidized_health_affiliates=('consecutivo', 'count'),
        mean_health_age=('edad', 'mean')).reset_index()

    agg_inclusion = df_social_inclusion_actions_for_people_with_disabilities.groupby('commune_clean').agg(
        total_disabled_and_inclusion_beneficiaries=('CONDICIÓN DE DISCAPACIDAD', 'count'),
        mean_inclusion_age=('AÑOS CUMPLIDOS AL INGRESO DEL PROGRAMA', 'mean')).reset_index()



    total_scholarship_medellin = len(df_scholarship)

    reference_global_stratum = df_utility_subsidy['estrato'].mean()
    if pd.isna(reference_global_stratum) or reference_global_stratum == 0:
        reference_global_stratum = 2.4

    agg_stratum = df_social_inclusion_actions_for_people_with_disabilities.groupby('commune_clean').agg(
        mean_utility_stratum=('ESTRATO SOCIOECONÓMICO', 'mean')).reset_index()

    city_level_metrics = {
        'total_epm_utility_subsidy_medellin': float(df_utility_subsidy['valor'].sum()),
        'total_epm_direct_subsidy_medellin': float(df_epm_subsidies_contributions['valor'].sum()),
        'total_cleaning_subsidy_medellin': float(df_subsidy_and_cleaning['total_subsidio'].sum()),
        'total_cleaning_subscribers_medellin': int(df_subsidy_and_cleaning['suscriptores_subsidiados'].sum()),
        'total_scholarship_beneficiaries_medellin': int(total_scholarship_medellin),
        'investment_data_years': available_years,
        'cleaning_scope_verified': cleaning_scope_verified,
        # 🆕 Documented limitation: 12.6% of subsidized regime affiliates have
        # commune=99, a code with no official definition in the source's data dictionary.
        # They are excluded from the territorial analysis by commune.
        'subsidized_health_unmatched_pct': round(codigo_99_count / total_filas * 100, 1) if total_filas else 0.0,
    }
    print(f"[MÉTRICAS DE CIUDAD] {city_level_metrics}")

    if total_scholarship_before_filter > 0 and total_scholarship_medellin / total_scholarship_before_filter < 0.02:
        print(f"[DECISIÓN METODOLÓGICA - BECAS] Solo el "
              f"{total_scholarship_medellin / total_scholarship_before_filter * 100:.2f}% de las filas "
              f"({total_scholarship_medellin} de {total_scholarship_before_filter}) quedó como 'Medellín' "
              f"tras el filtro geográfico por texto en 'MUNICIPIO DE RESIDENCIA'. El dataset es de cobertura "
              f"departamental (Antioquia), y los valores no emparejados corresponden a municipios reales "
              f"(Rionegro, Bello, Apartadó, etc.), no a errores de formato. No se pudo verificar si existe una "
              f"columna alterna de código DANE de municipio con mejor cobertura para Medellín. "
              f"DECISIÓN: dado que N=33 es insuficiente para desagregar de forma confiable por las 21 "
              f"comunas/corregimientos, esta variable se reporta ÚNICAMENTE como métrica agregada a nivel "
              f"de ciudad (total_scholarship_beneficiaries_medellin) y se EXCLUYE del análisis territorial "
              f"por comuna y del modelo predictivo, para no introducir ruido o falsas conclusiones por comuna "
              f"basadas en muestras casi vacías.")

    print("Consolidando Matriz Maestra Analítica (Data Mashup Híbrido, sin fuga de datos)...")
    medellin_territories = [
        '01 - POPULAR', '02 - SANTA CRUZ', '03 - MANRIQUE', '04 - ARANJUEZ',
        '05 - CASTILLA', '06 - DOCE DE OCTUBRE', '07 - ROBLEDO', '08 - VILLA HERMOSA',
        '09 - BUENOS AIRES', '10 - LA CANDELARIA', '11 - LAURELES ESTADIO', '12 - LA AMERICA',
        '13 - SAN JAVIER', '14 - EL POBLADO', '15 - GUAYABAL', '16 - BELEN',
        '50 - SAN SEBASTIÁN DE PALMITAS', '60 - SAN CRISTÓBAL', '70 - ALTAVISTA',
        '80 - SAN ANTONIO DE PRADO', '90 - SANTA ELENA'
    ]

    agg_health['health_affiliates_share'] = (
            agg_health['total_subsidized_health_affiliates'] /
            agg_health['total_subsidized_health_affiliates'].sum()
    )
    agg_inclusion['inclusion_share'] = (
            agg_inclusion['total_disabled_and_inclusion_beneficiaries'] /
            agg_inclusion['total_disabled_and_inclusion_beneficiaries'].sum()
    )

    master_matrix = pd.DataFrame({'commune_clean': medellin_territories})
    master_matrix = pd.merge(master_matrix, agg_investment_display, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_health, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_inclusion, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_stratum, on='commune_clean', how='left')

    columns_to_zero = [
        'total_investment', 'n_years_with_data', 'total_subsidized_health_affiliates', 'mean_health_age',
        'total_disabled_and_inclusion_beneficiaries', 'mean_inclusion_age',
        'health_affiliates_share', 'inclusion_share'
    ]
    master_matrix[columns_to_zero] = master_matrix[columns_to_zero].fillna(0)
    master_matrix['mean_utility_stratum'] = master_matrix['mean_utility_stratum'].fillna(reference_global_stratum)

    master_matrix['disability_pressure_index'] = master_matrix['total_disabled_and_inclusion_beneficiaries'] / (
            master_matrix['total_subsidized_health_affiliates'] + 1)

    master_matrix.attrs['city_level_metrics'] = city_level_metrics

    panel_index = pd.MultiIndex.from_product(
        [medellin_territories, available_years], names=['commune_clean', 'anio']
    ).to_frame(index=False)

    master_matrix_panel = pd.merge(panel_index, agg_investment_panel, on=['commune_clean', 'anio'], how='left')
    master_matrix_panel = pd.merge(master_matrix_panel, agg_health, on='commune_clean', how='left')
    master_matrix_panel = pd.merge(master_matrix_panel, agg_inclusion, on='commune_clean', how='left')
    master_matrix_panel = pd.merge(master_matrix_panel, agg_stratum, on='commune_clean', how='left')

    panel_columns_to_zero = [
        'total_investment', 'total_subsidized_health_affiliates', 'mean_health_age',
        'total_disabled_and_inclusion_beneficiaries', 'mean_inclusion_age',
        'health_affiliates_share', 'inclusion_share'
    ]
    master_matrix_panel[panel_columns_to_zero] = master_matrix_panel[panel_columns_to_zero].fillna(0)
    master_matrix_panel['mean_utility_stratum'] = master_matrix_panel['mean_utility_stratum'].fillna(reference_global_stratum)

    print(f"[PANEL MULTI-AÑO] {len(master_matrix_panel)} filas de entrenamiento "
          f"({len(medellin_territories)} territorios x {len(available_years)} años).")

    diagnostic_correlation_check(master_matrix_panel, label_for_log="Panel multi-año")

    return master_matrix, city_level_metrics, master_matrix_panel


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