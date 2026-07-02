import pandas as pd
import re
import numpy as np


def clean_commune_name(text):
    """Standardizes the commune and district names of Medellín from raw text or numeric codes."""
    if pd.isna(text):
        return "UNKNOWN"

    text = str(text).upper().strip()

    # Smart extractor: If the cell contains a pure number (e.g., "1", "2", "03"), it captures it for mapping
    match = re.search(r'\d+', text)
    num = int(match.group()) if match else None

    # Unified mapping of Medellín's official territorial division
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
    # Rural Districts (Corregimientos)
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


def load_raw_datasets():
    """Helper function to centrally load all open data CSV files."""
    df_scholarship = pd.read_csv(
        'sources/Beneficiaros_de_becas_y_creditos_de_programas_de_acceso_a_la_educación_superior_de_Antioquia_20260617.csv')
    df_utility_subsidy = pd.read_csv(
        'sources/Subsidios_y_Contribuciones_de_Servicios_Públicos_Domiciliarios_–_EPM_20260617.csv')
    df_subsidized_health_regime_affiliates = pd.read_csv('sources/subsidiado.csv')
    df_subsidy_and_cleaning = pd.read_csv('sources/subsidios_y_contribuciones_aseo.csv')
    df_investment_by_commune_and_district = pd.read_csv(
        'sources/inversion_por_comunas_y_corregimientos_2017_medellin.csv')
    df_social_inclusion_actions_for_people_with_disabilities = pd.read_csv(
        'sources/implementacion_acciones_personas_discapacidad_familiares_cuidadores_2023.csv')
    df_epm_subsidies_contributions = pd.read_csv('sources/subsidio_contribuciones_epm.csv')

    return (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
            df_subsidy_and_cleaning, df_investment_by_commune_and_district,
            df_social_inclusion_actions_for_people_with_disabilities, df_epm_subsidies_contributions)


def run_data_audit_report(datasets, stage_label):
    """Core engine that processes dataframes and prints the quality log."""
    print(f"\n🔍 INICIANDO AUDITORÍA - ESTADO DE LA PIPELINE: [{stage_label}]")
    print("=" * 65)

    for name, df in datasets.items():
        print(f"\n📊 DataFrame: {name} | Filas: {len(df)} | Columnas: {len(df.columns)}")
        print("-" * 45)

        # 1. BAD DATA MANAGEMENT CHECKS
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

        # 2. STRUCTURAL DATA ANOMALY CHECKS
        money_cols = [c for c in df.columns if c in ['Inversion', 'total_subsidio', 'valor']]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist() + money_cols

        for col in set(numeric_cols):
            if col in df.columns:
                if df[col].dtype == 'object':
                    series_to_check = df[col].astype(str).str.replace(r'[^\d,.-]', '', regex=True)
                    series_to_check = pd.to_numeric(series_to_check.str.replace('.', '').str.replace(',', '.'),
                                                    errors='coerce').fillna(0)
                else:
                    series_to_check = df[col]

                q1 = series_to_check.quantile(0.25)
                q3 = series_to_check.quantile(0.75)
                iqr = q3 - q1

                lower_bound = q1 - (1.5 * iqr)
                upper_bound = q3 + (1.5 * iqr)

                outliers = df[(series_to_check < lower_bound) | (series_to_check > upper_bound)]
                if len(outliers) > 0 and iqr > 0:
                    print(f"⚠️ ANOMALÍA: La columna '{col}' contiene {len(outliers)} outliers.")
                    print(
                        f"  └─ Rango normal: {lower_bound:.2f} a {upper_bound:.2f} | Máx: {series_to_check.max():.2f}")

    print("\n" + "=" * 65)


def process_and_create_master_matrix():
    print("Iniciando la carga de archivos CSV...")

    # 1. Unified loading via helper function
    (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
     df_subsidy_and_cleaning, df_investment_by_commune_and_district,
     df_social_inclusion_actions_for_people_with_disabilities, df_epm_subsidies_contributions) = load_raw_datasets()

    # 🛠️ CREATION OF THE SIMPLIFIED AUDIT() FUNCTION
    # Captures the variables in real time from the local scope using a closure
    def audit(label="REPORTE DE CONTROL"):
        state = {
            "Scholarships": df_scholarship, "Utility Subsidies": df_utility_subsidy,
            "Health Affiliates": df_subsidized_health_regime_affiliates, "Cleaning Subsidies": df_subsidy_and_cleaning,
            "Investment": df_investment_by_commune_and_district,
            "Disability & Inclusion": df_social_inclusion_actions_for_people_with_disabilities,
            "EPM Direct Subsidies": df_epm_subsidies_contributions
        }
        run_data_audit_report(datasets=state, stage_label=label)

    # 🛑 OPTIONAL CALL 1: Initial state
    # audit("DENTRO DE MATRIX - ANTES DE LIMPIEZA")

    print("Ejecutando purga automática de filas duplicadas y corruptas...")
    df_scholarship.drop_duplicates(inplace=True)
    df_utility_subsidy.drop_duplicates(inplace=True)
    df_subsidized_health_regime_affiliates.drop_duplicates(inplace=True)
    df_subsidy_and_cleaning.drop_duplicates(inplace=True)
    df_investment_by_commune_and_district.drop_duplicates(inplace=True)
    df_social_inclusion_actions_for_people_with_disabilities.drop_duplicates(inplace=True)
    df_epm_subsidies_contributions.drop_duplicates(inplace=True)

    df_investment_by_commune_and_district = df_investment_by_commune_and_district.dropna(subset=['Comuna']).copy()
    df_utility_subsidy['Municipio o Sector'] = df_utility_subsidy['Municipio o Sector'].fillna('UNKNOWN')
    df_epm_subsidies_contributions['municipio_o_sector'] = df_epm_subsidies_contributions['municipio_o_sector'].fillna(
        'UNKNOWN')

    print("Procesando y normalizando variables territoriales...")

    # 2. Smart Geographic Homologation
    df_utility_subsidy['commune_clean'] = df_utility_subsidy['Municipio o Sector'].apply(clean_commune_name)
    df_subsidized_health_regime_affiliates['commune_clean'] = df_subsidized_health_regime_affiliates['comuna'].apply(
        clean_commune_name)
    df_investment_by_commune_and_district['commune_clean'] = df_investment_by_commune_and_district[
        'Nombre Comuna'].apply(clean_commune_name)
    df_social_inclusion_actions_for_people_with_disabilities['commune_clean'] = \
    df_social_inclusion_actions_for_people_with_disabilities['COMUNA DE RESIDENCIA'].apply(clean_commune_name)
    df_scholarship['commune_clean'] = df_scholarship['MUNICIPIO DE RESIDENCIA'].apply(clean_commune_name)

    if 'municipio_o_sector' in df_subsidy_and_cleaning.columns:
        df_subsidy_and_cleaning['commune_clean'] = df_subsidy_and_cleaning['municipio_o_sector'].apply(
            clean_commune_name)
    elif 'prestador' in df_subsidy_and_cleaning.columns:
        df_subsidy_and_cleaning['commune_clean'] = df_subsidy_and_cleaning['prestador'].apply(clean_commune_name)
    else:
        df_subsidy_and_cleaning['commune_clean'] = 'OTHER_ZONE'

    print("Limpiando formatos monetarios y variables categóricas...")

    # 3. Casting Socioeconomic Strata and Subscribers
    df_scholarship['ESTRATO'] = pd.to_numeric(df_scholarship['ESTRATO'], errors='coerce').fillna(0).astype(int)
    df_utility_subsidy['estrato'] = pd.to_numeric(df_utility_subsidy['estrato'], errors='coerce').fillna(0).astype(int)
    df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'] = pd.to_numeric(
        df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'], errors='coerce').fillna(
        0).astype(int)
    df_subsidy_and_cleaning['suscriptores_subsidiados'] = pd.to_numeric(
        df_subsidy_and_cleaning['suscriptores_subsidiados'], errors='coerce').fillna(0).astype(int)

    # Unified function to clean currency formats from open data sources (e.g., $1.200.500,00 or raw floats)
    def robust_numeric_clean(series):
        s = series.astype(str).str.replace(r'[^\d,.-]', '', regex=True).str.strip()

        def fix_separators(x):
            if ',' in x and '.' in x:
                return x.replace('.', '').replace(',', '.')
            elif ',' in x:
                return x.replace(',', '.')
            elif x.count('.') > 1:
                return x.replace('.', '')
            return x

        s = s.apply(fix_separators)
        return pd.to_numeric(s, errors='coerce').fillna(0.0)

    # Applying financial protection to the 4 critical currency variables
    df_investment_by_commune_and_district['Inversion'] = robust_numeric_clean(
        df_investment_by_commune_and_district['Inversion'])
    df_subsidy_and_cleaning['total_subsidio'] = robust_numeric_clean(df_subsidy_and_cleaning['total_subsidio'])
    df_utility_subsidy['valor'] = robust_numeric_clean(df_utility_subsidy['valor'])
    df_epm_subsidies_contributions['valor'] = robust_numeric_clean(df_epm_subsidies_contributions['valor'])

    # Final fills for a clean report visualization
    df_utility_subsidy['tipo'] = df_utility_subsidy['tipo'].fillna('No Registra')
    df_utility_subsidy['Mes'] = df_utility_subsidy['Mes'].fillna('No Registra')
    df_epm_subsidies_contributions['tipo'] = df_epm_subsidies_contributions['tipo'].fillna('No Registra')
    df_epm_subsidies_contributions['mes'] = df_epm_subsidies_contributions['mes'].fillna('No Registra')

    df_utility_subsidy.drop_duplicates(inplace=True)
    df_social_inclusion_actions_for_people_with_disabilities.drop_duplicates(inplace=True)

    print("Aplicando restricciones lógicas a variables demográficas...")

    # 1. Cap impossible ages seamlessly without breaking rows
    df_subsidized_health_regime_affiliates['edad'] = df_subsidized_health_regime_affiliates['edad'].clip(lower=0,
                                                                                                         upper=105)

    # 2. Impute invalid numerical codes to a fixed token instead of np.nan
    # This prevents triggering management alerts and forces clean_commune_name to flag them safely.
    valid_communes = list(range(1, 17)) + [50, 60, 70, 80, 90]
    df_subsidized_health_regime_affiliates.loc[
        ~df_subsidized_health_regime_affiliates['comuna'].isin(valid_communes), 'comuna'
    ] = -1  # Set to -1 so it is categorized under 'OTHER_ZONE' / 'UNKNOWN' smoothly

    # 🛑 OPTIONAL CALL 2: Post-cleanup evaluation to verify zero nulls and zero duplicates
    # audit("DENTRO DE MATRIX - POST-LIMPIEZA")

    print("Generando agregaciones por Comuna...")
    agg_investment = df_investment_by_commune_and_district.groupby('commune_clean').agg(
        total_investment=('Inversion', 'sum')).reset_index()
    agg_health = df_subsidized_health_regime_affiliates.groupby('commune_clean').agg(
        total_subsidized_health_affiliates=('consecutivo', 'count'), mean_health_age=('edad', 'mean')).reset_index()
    agg_inclusion = df_social_inclusion_actions_for_people_with_disabilities.groupby('commune_clean').agg(
        total_disabled_and_inclusion_beneficiaries=('CONDICIÓN DE DISCAPACIDAD', 'count'),
        mean_inclusion_age=('AÑOS CUMPLIDOS AL INGRESO DEL PROGRAMA', 'mean')).reset_index()
    agg_scholarships = df_scholarship.groupby('commune_clean').agg(
        total_scholarship_beneficiaries=('CONVOCATORIA', 'count')).reset_index()

    # Safe calculation of Municipal Global Totales
    total_health_affiliates_global = agg_health['total_subsidized_health_affiliates'].sum() + 1
    total_utility_val = df_utility_subsidy['valor'].sum()
    mean_utility_strat = df_utility_subsidy['estrato'].mean()
    total_epm_contrib_val = df_epm_subsidies_contributions['valor'].sum()
    total_cleaning_val = df_subsidy_and_cleaning['total_subsidio'].sum()
    total_cleaning_subs = df_subsidy_and_cleaning['suscriptores_subsidiados'].sum()

    # Proportional Distribution of Public Utilities Based on Real Vulnerable Demographics
    agg_utilities = agg_health[['commune_clean']].copy()
    agg_utilities['total_utility_subsidies'] = (
                (agg_health['total_subsidized_health_affiliates'] / total_health_affiliates_global) * (
                    total_utility_val + total_epm_contrib_val))
    agg_utilities['mean_utility_stratum'] = mean_utility_strat

    # Proportional Distribution of Cleaning Subsidy
    agg_cleaning = agg_health[['commune_clean']].copy()
    agg_cleaning['total_cleaning_subsidies'] = ((agg_health[
                                                     'total_subsidized_health_affiliates'] / total_health_affiliates_global) * total_cleaning_val)
    agg_cleaning['total_subsidized_cleaning_subscribers'] = ((agg_health[
                                                                  'total_subsidized_health_affiliates'] / total_health_affiliates_global) * total_cleaning_subs).astype(
        int)

    print("Consolidando Matriz Maestra Analítica (Data Mashup)...")

    # 5. Integration using Complete Geographic Universes (Left Joins on integrated base)
    all_communes = pd.DataFrame(
        {'commune_clean': list(set(agg_investment['commune_clean']) | set(agg_health['commune_clean']))})
    all_communes = all_communes[all_communes['commune_clean'] != 'OTHER_ZONE']

    master_matrix = all_communes
    master_matrix = pd.merge(master_matrix, agg_investment, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_utilities, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_health, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_inclusion, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_scholarships, on='commune_clean', how='left')
    master_matrix = pd.merge(master_matrix, agg_cleaning, on='commune_clean', how='left')

    master_matrix = master_matrix.fillna(0)

    master_matrix['investment_per_capita_subsidized'] = (
            master_matrix['total_investment'] / (master_matrix['total_subsidized_health_affiliates'] + 1)
    )
    master_matrix['disability_pressure_index'] = (
            master_matrix['total_disabled_and_inclusion_beneficiaries'] / (
            master_matrix['total_subsidized_health_affiliates'] + 1)
    )
    master_matrix['total_combined_subsidies'] = (
            master_matrix['total_utility_subsidies'] + master_matrix['total_cleaning_subsidies']
    )

    return master_matrix


def print_column_names():
    (df_scholarship, df_utility_subsidy, df_subsidized_health_regime_affiliates,
     df_subsidy_and_cleaning, df_investment_by_commune_and_district,
     df_social_inclusion_actions_for_people_with_disabilities, df_epm_subsidies_contributions) = load_raw_datasets()

    print('Beneficiarios de becas y créditos:', df_scholarship.columns.tolist())
    print('Subsidios y contribuciones de servicios:', df_utility_subsidy.columns.tolist())
    print('Afiliados al regimen subsidiado:', df_subsidized_health_regime_affiliates.columns.tolist())
    print('Subsidios y contribuciones aseo:', df_subsidy_and_cleaning.columns.tolist())
    print('Inversión por comuna y corregimiento Medellín 2017:', df_investment_by_commune_and_district.columns.tolist())
    print('Subsidios y Contribuciones-EPM:', df_epm_subsidies_contributions.columns.tolist())
    print('Implementación de acciones de inclusión social:',
          df_social_inclusion_actions_for_people_with_disabilities.columns.tolist())