import pandas as pd
import re
import numpy as np
import unicodedata

#   1        -> Data is already in current pesos (COP)
#   1_000     -> Data comes in THOUSANDS of pesos
#   1_000_000 -> Data comes in MILLIONS of pesos
INVESTMENT_UNIT_MULTIPLIER = 1_000_000

# 🆕 Multi-year investment datasets. Note: the 2018 file does NOT have the
# "_medellin" suffix in its name (unlike the others), so the exact name
# as delivered by the user is preserved.
INVESTMENT_FILES_BY_YEAR = {
    2015: 'sources/inversion_por_comunas_y_corregimientos_2015_medellin.csv',
    2016: 'sources/inversion_por_comunas_y_corregimientos_2016_medellin.csv',
    2017: 'sources/inversion_por_comunas_y_corregimientos_2017_medellin.csv',
    2018: 'sources/inversion_por_comunas_y_corregimientos_2018.csv',
}

# Candidate column names in case each year brings a different convention
# (very common among datasets from different years in datos.gov.co).
INVESTMENT_COLUMN_CANDIDATES = {
    'comuna_name': ['Nombre Comuna', 'nombre_comuna', 'NOMBRE_COMUNA', 'NOMBRE COMUNA',
                    'Comuna', 'comuna', 'COMUNA'],
    'comuna_id_for_dropna': ['Comuna', 'comuna', 'COMUNA', 'Codigo Comuna', 'codigo_comuna',
                             'CODIGO_COMUNA'],
    'valor_inversion': ['Inversion', 'inversion', 'INVERSION', 'Valor Inversion',
                        'valor_inversion', 'Valor', 'VALOR', 'Monto', 'monto'],
}

# 🆕 Model columns, in a single place so data_processor.py,
# model_trainer.py, and app.py stay synchronized without guessing the order.
MODEL_FEATURE_COLUMNS = [
    "total_subsidized_health_affiliates",
    "total_disabled_and_inclusion_beneficiaries",
    "mean_utility_stratum",
    "anio",
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


def map_stratum_category(series):
    normalized = series.astype(str).str.upper().str.strip()
    return normalized.map(STRATUM_CATEGORY_TO_NUMBER)


def _strip_accents(text):
    """Removes accents/diacritics so that name matching is
    insensitive to accents (e.g., 'BELÉN' and 'BELEN' should match)."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(ch for ch in nfkd if not unicodedata.combining(ch))


def clean_commune_name(text):
    """Standardizes the commune and district names of Medellín from raw text or numeric codes."""
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

    mask_other = df[raw_column].apply(clean_commune_name) == 'OTHER_ZONE'
    n_other = mask_other.sum()

    if n_other > 0:
        valores_sin_match = df.loc[mask_other, raw_column].astype(str).unique().tolist()
        print(f"[DIAGNÓSTICO COMUNAS] {label_for_log}: {n_other} filas NO emparejadas "
              f"a ninguna comuna válida (cayeron en 'OTHER_ZONE').")
        print(f"  └─ Valores crudos sin match: {valores_sin_match}")
    else:
        print(f"[DIAGNÓSTICO COMUNAS] {label_for_log}: 100% de las filas emparejadas correctamente.")


def filter_to_medellin(df, column, label_for_log):
    if column not in df.columns:
        print(f"[ALERTA FILTRO] La columna '{column}' no existe en {label_for_log}. No se aplicó filtro geográfico.")
        return df

    normalized = df[column].astype(str).str.upper().str.strip()
    mask = normalized.str.contains('MEDELL', na=False)  # Covers "MEDELLÍN" / "MEDELLIN"
    filtered = df[mask].copy()

    print(f"[FILTRO GEOGRÁFICO] {label_for_log}: {len(df)} filas totales -> {len(filtered)} filas de Medellín "
          f"({len(df) - len(filtered)} filas de otros municipios/regiones descartadas).")

    return filtered


def _find_column(df, candidates):
    """Returns the first column name from `candidates` that exists in df, or None."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def robust_numeric_clean(series):
    """Cleans monetary text (mixed thousands/decimal separators) and
    converts to numeric. Module-level function (previously lived as an
    internal closure) to allow reuse from the multi-year loader."""
    s = series.astype(str).str.replace(r'[^\d,.-]', '', regex=True).str.strip()

    def fix_separators(x):
        if not x:
            return "0"
        if '.' in x and ',' not in x:
            partes = x.split('.')
            if len(partes[-1]) == 3:
                return x.replace('.', '')

        if ',' in x and '.' in x:
            return x.replace('.', '').replace(',', '.')
        elif ',' in x:
            return x.replace(',', '.')

        return x

    s = s.apply(fix_separators)
    return pd.to_numeric(s, errors='coerce').fillna(0.0)


def load_investment_year(path, year):
    """
    Loads an investment file for a specific year, automatically detecting
    column names (which may vary between years), and returns a standardized
    DataFrame with ['commune_clean', 'Inversion', 'anio'].

    If the file does not exist or required columns cannot be detected,
    it prints a clear diagnosis and returns None (does not break the rest of
    the pipeline if a year is missing).
    """
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

    df['Inversion'] = robust_numeric_clean(df[val_col]) * INVESTMENT_UNIT_MULTIPLIER
    df['anio'] = year

    print(f"[CARGA INVERSIÓN {year}] '{path}': {len(df)} filas cargadas "
          f"(columna comuna='{name_col}', columna valor='{val_col}').")

    return df[['commune_clean', 'Inversion', 'anio']]


def load_investment_multiyear():
    """Loads and concatenates all available years in INVESTMENT_FILES_BY_YEAR."""
    dfs = []
    for year, path in sorted(INVESTMENT_FILES_BY_YEAR.items()):
        df_year = load_investment_year(path, year)
        if df_year is not None:
            dfs.append(df_year)

    if not dfs:
        raise RuntimeError("[ERROR INVERSIÓN] No se pudo cargar NINGÚN año de inversión. "
                            "Revisa las rutas en INVESTMENT_FILES_BY_YEAR.")

    df_investment_multiyear = pd.concat(dfs, ignore_index=True)
    available_years = sorted(df_investment_multiyear['anio'].unique().tolist())
    print(f"[INVERSIÓN MULTI-AÑO] Años cargados exitosamente: {available_years}")
    return df_investment_multiyear, available_years


def load_raw_datasets():
    """Helper function to centrally load all open data CSV files (except investment,
    which is now loaded separately because it is multi-year)."""
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
    """Core engine that processes dataframes and prints the quality log."""
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
    extracted = series.astype(str).str.extract(r'(\d+)')[0]
    return pd.to_numeric(extracted, errors='coerce')


def diagnostic_zero_after_conversion(series_before, series_after, column_name, label_for_log):
    n_zero = (series_after == 0).sum()
    pct_zero = n_zero / len(series_after) * 100 if len(series_after) else 0
    if pct_zero > 50:
        examples = series_before.astype(str).unique()[:5].tolist()
        print(f"[ALERTA CONVERSIÓN] {label_for_log}: {pct_zero:.1f}% de '{column_name}' quedó en 0 "
              f"tras convertir a numérico. Ejemplos de valores crudos: {examples}")


def diagnostic_correlation_check(df_analytics, label_for_log="Panel"):
    """
    Displays the real (Pearson) correlation between each predictor variable and
    investment. Useful to confirm if a relationship (positive or negative)
    is a genuine pattern in the data, or just noise from a small sample.
    """
    print(f"\n[DIAGNÓSTICO CORRELACIÓN - {label_for_log}] Relación entre variables and total_investment "
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
    df_investment_multiyear, available_years = load_investment_multiyear()

    print("Ejecutando purga automática de filas duplicadas y corruptas...")
    df_scholarship.drop_duplicates(inplace=True)
    df_utility_subsidy.drop_duplicates(inplace=True)
    df_subsidized_health_regime_affiliates.drop_duplicates(inplace=True)
    df_subsidy_and_cleaning.drop_duplicates(inplace=True)
    df_investment_multiyear.drop_duplicates(inplace=True)
    df_social_inclusion_actions_for_people_with_disabilities.drop_duplicates(inplace=True)
    df_epm_subsidies_contributions.drop_duplicates(inplace=True)

    df_utility_subsidy['Municipio o Sector'] = df_utility_subsidy['Municipio o Sector'].fillna('UNKNOWN')
    df_epm_subsidies_contributions['municipio_o_sector'] = df_epm_subsidies_contributions['municipio_o_sector'].fillna('UNKNOWN')

    df_utility_subsidy = filter_to_medellin(df_utility_subsidy, 'Municipio o Sector', 'Subsidios y Contribuciones EPM (servicios)')
    df_epm_subsidies_contributions = filter_to_medellin(df_epm_subsidies_contributions, 'municipio_o_sector', 'Subsidios y Contribuciones EPM (directos)')
    df_scholarship = filter_to_medellin(df_scholarship, 'MUNICIPIO DE RESIDENCIA', 'Becas y créditos educación superior')

    print("Procesando y normalizando variables territoriales...")
    df_subsidized_health_regime_affiliates['commune_clean'] = df_subsidized_health_regime_affiliates['comuna'].apply(clean_commune_name)
    df_social_inclusion_actions_for_people_with_disabilities['commune_clean'] = \
        df_social_inclusion_actions_for_people_with_disabilities['COMUNA DE RESIDENCIA'].apply(clean_commune_name)

    diagnostic_unmatched_communes(df_subsidized_health_regime_affiliates, 'comuna', 'Régimen subsidiado (salud)')
    diagnostic_unmatched_communes(df_social_inclusion_actions_for_people_with_disabilities,
                                   'COMUNA DE RESIDENCIA', 'Inclusión y discapacidad')

    print("Limpiando formatos monetarios y variables categóricas...")
    raw_stratum_scholarship = df_scholarship['ESTRATO'].copy()
    df_scholarship['ESTRATO'] = extract_leading_number(df_scholarship['ESTRATO']).fillna(0).astype(int)
    diagnostic_zero_after_conversion(raw_stratum_scholarship, df_scholarship['ESTRATO'], 'ESTRATO', 'Becas')

    raw_stratum_utility = df_utility_subsidy['estrato'].copy()
    df_utility_subsidy['estrato'] = extract_leading_number(df_utility_subsidy['estrato']).fillna(0).astype(int)
    diagnostic_zero_after_conversion(raw_stratum_utility, df_utility_subsidy['estrato'], 'estrato',
                                     'Subsidios EPM servicios')

    raw_stratum_inclusion = df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'].copy()
    df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'] = map_stratum_category(
        df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO']
    )
    diagnostic_zero_after_conversion(raw_stratum_inclusion,
                                     df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'],
                                     'ESTRATO SOCIOECONÓMICO', 'Inclusión y discapacidad')
    df_subsidy_and_cleaning['suscriptores_subsidiados'] = pd.to_numeric(
        df_subsidy_and_cleaning['suscriptores_subsidiados'], errors='coerce').fillna(0).astype(int)

    df_subsidy_and_cleaning['total_subsidio'] = robust_numeric_clean(df_subsidy_and_cleaning['total_subsidio'])
    df_utility_subsidy['valor'] = robust_numeric_clean(df_utility_subsidy['valor'])
    df_epm_subsidies_contributions['valor'] = robust_numeric_clean(df_epm_subsidies_contributions['valor'])

    print("Autorizando restricciones lógicas a variables demográficas...")
    df_subsidized_health_regime_affiliates['edad'] = df_subsidized_health_regime_affiliates['edad'].clip(lower=0, upper=105)
    valid_communes = list(range(1, 17)) + [50, 60, 70, 80, 90]
    df_subsidized_health_regime_affiliates.loc[
        ~df_subsidized_health_regime_affiliates['comuna'].isin(valid_communes), 'comuna'] = np.nan
    df_subsidized_health_regime_affiliates['commune_clean'] = df_subsidized_health_regime_affiliates['comuna'].apply(
        clean_commune_name)

    print("Generando agregaciones REALES por comuna (sin fuga de datos ni mezcla geográfica)...")

    # 🆕 Investment is now aggregated by commune AND by year (panel), not just by commune.
    agg_investment_panel = df_investment_multiyear.groupby(['commune_clean', 'anio']).agg(
        total_investment=('Inversion', 'sum')).reset_index()

    # 🆕 "Display" view (one row per commune): annual average investment among
    # the available years, plus how many years actually have data for that commune.
    # The mean is used (instead of an arbitrary year) because it is more representative
    # than taking only the last year, avoiding dashboard ranking bias towards a particular year.
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
        'investment_data_years': available_years,  # 🆕
    }
    print(f"[MÉTRICAS DE CIUDAD] {city_level_metrics}")

    print("Consolidando Matriz Maestra Analítica (Data Mashup Híbrido, sin fuga de datos)...")
    medellin_territories = [
        '01 - POPULAR', '02 - SANTA CRUZ', '03 - MANRIQUE', '04 - ARANJUEZ',
        '05 - CASTILLA', '06 - DOCE DE OCTUBRE', '07 - ROBLEDO', '08 - VILLA HERMOSA',
        '09 - BUENOS AIRES', '10 - LA CANDELARIA', '11 - LAURELES ESTADIO', '12 - LA AMERICA',
        '13 - SAN JAVIER', '14 - EL POBLADO', '15 - GUAYABAL', '16 - BELEN',
        '50 - SAN SEBASTIÁN DE PALMITAS', '60 - SAN CRISTÓBAL', '70 - ALTAVISTA',
        '80 - SAN ANTONIO DE PRADO', '90 - SANTA ELENA'
    ]

    # ---- DISPLAY Matrix: one row per commune (for dashboard/table) ----
    master_matrix = pd.DataFrame({'commune_clean': medellin_territories})
    master_matrix = pd.merge(master_matrix, agg_investment_display, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_health, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_inclusion, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_stratum, on='commune_clean', how='left')

    columns_to_zero = [
        'total_investment', 'n_years_with_data', 'total_subsidized_health_affiliates', 'mean_health_age',
        'total_disabled_and_inclusion_beneficiaries', 'mean_inclusion_age',
    ]
    master_matrix[columns_to_zero] = master_matrix[columns_to_zero].fillna(0)
    master_matrix['mean_utility_stratum'] = master_matrix['mean_utility_stratum'].fillna(reference_global_stratum)

    master_matrix['disability_pressure_index'] = master_matrix['total_disabled_and_inclusion_beneficiaries'] / (
            master_matrix['total_subsidized_health_affiliates'] + 1)

    master_matrix.attrs['city_level_metrics'] = city_level_metrics

    # ---- PANEL Matrix: one row per commune x year (to train model with higher N) ----
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
    ]
    master_matrix_panel[panel_columns_to_zero] = master_matrix_panel[panel_columns_to_zero].fillna(0)
    master_matrix_panel['mean_utility_stratum'] = master_matrix_panel['mean_utility_stratum'].fillna(reference_global_stratum)

    print(f"[PANEL MULTI-AÑO] {len(master_matrix_panel)} filas de entrenamiento "
          f"({len(medellin_territories)} territorios x {len(available_years)} años).")

    diagnostic_correlation_check(master_matrix_panel, label_for_log="Panel multi-año")

    return master_matrix, city_level_metrics, master_matrix_panel


def print_column_names():
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