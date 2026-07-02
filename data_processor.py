import pandas as pd
import numpy as np
import re


def clean_commune_name(text):
    """Standardizes the commune and district names of Medellín from raw text or numeric codes."""
    if pd.isna(text):
        return "UNKNOWN"

    text = str(text).upper().strip()

    # Extractor inteligente: Si la celda contiene un número puro (ej: "1", "2", "03"), lo captura para el mapeo
    match = re.search(r'\d+', text)
    num = int(match.group()) if match else None

    # Mapeo unificado de la división territorial oficial de Medellín
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
    # Corregimientos (Distritos Rurales)
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


def process_and_create_master_matrix():
    print("Iniciando la carga de archivos CSV...")

    # 1. Carga de todos los conjuntos de datos usando las columnas confirmadas
    # Beneficiarios de becas y créditos
    # Source: https://www.datos.gov.co/en/Educaci-n/Beneficiaros-de-becas-y-creditos-de-programas-de-a/ya7f-466y/about_data
    df_scholarship = pd.read_csv(
        'sources/Beneficiaros_de_becas_y_creditos_de_programas_de_acceso_a_la_educación_superior_de_Antioquia_20260617.csv')
    # Subsidios y contribuciones de servicios
    # Source: https://www.datos.gov.co/Minas-y-Energ-a/Subsidios-y-Contribuciones-de-Servicios-P-blicos-D/av6t-m6ju/about_data
    df_utility_subsidy = pd.read_csv(
        'sources/Subsidios_y_Contribuciones_de_Servicios_Públicos_Domiciliarios_–_EPM_20260617.csv')
    # Afiliados al regimen subsidiado
    # Source: https://www.datos.gov.co/dataset/Afiliados-al-r-gimen-subsidiado-de-Medell-n/n7qb-ahpa/about_data
    df_subsidized_health_regime_affiliates = pd.read_csv('sources/subsidiado.csv')
    # Subsidios y contribuciones aseo
    # Source: https://www.datos.gov.co/dataset/Subsidios-y-contribuciones-aseo/db2v-e8wa/about_data
    df_subsidy_and_cleaning = pd.read_csv('sources/subsidios_y_contribuciones_aseo.csv')
    # Inversión por comuna y corregimiento Medellín 2017
    # Source: https://www.datos.gov.co/dataset/Inversi-n-por-comuna-y-corregimiento-Medell-n-2017/3e4c-pzjq/about_data
    df_investment_by_commune_and_district = pd.read_csv(
        'sources/inversion_por_comunas_y_corregimientos_2017_medellin.csv')
    # Implementación de acciones de inclusión social para personas con discapacidad familiares y cuidadores 2023
    # Source: https://www.datos.gov.co/dataset/Implementaci-n-de-acciones-de-inclusi-n-social-par/hdjq-kape/about_data
    df_social_inclusion_actions_for_people_with_disabilities = pd.read_csv(
        'sources/implementacion_acciones_personas_discapacidad_familiares_cuidadores_2023.csv')
    # Subsidios y Contribuciones-EPM - Energía, Gas, Acueducto y Alcantarillado
    # Source: https://www.datos.gov.co/dataset/Subsidios-y-Contribuciones-EPM-Energ-a-Gas-Acueduc/dag3-4sey/about_data
    df_epm_subsidies_contributions = pd.read_csv('sources/subsidio_contribuciones_epm.csv')

    print("Procesando y normalizando variables territoriales...")

    # 2. Homologación Geográfica Inteligente
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

    # 3. Casteo de Estratos Socioeconómicos y Suscriptores
    df_scholarship['ESTRATO'] = pd.to_numeric(df_scholarship['ESTRATO'], errors='coerce').fillna(0).astype(int)
    df_utility_subsidy['estrato'] = pd.to_numeric(df_utility_subsidy['estrato'], errors='coerce').fillna(0).astype(int)
    df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'] = pd.to_numeric(
        df_social_inclusion_actions_for_people_with_disabilities['ESTRATO SOCIOECONÓMICO'], errors='coerce').fillna(
        0).astype(int)
    df_subsidy_and_cleaning['suscriptores_subsidiados'] = pd.to_numeric(
        df_subsidy_and_cleaning['suscriptores_subsidiados'], errors='coerce').fillna(0).astype(int)

    # Función unificada para limpiar formatos de moneda de datos abiertos (ej: $1.200.500,00 o floats crudos)
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

    # Aplicación del blindaje financiero a las 4 variables críticas de dinero
    df_investment_by_commune_and_district['Inversion'] = robust_numeric_clean(
        df_investment_by_commune_and_district['Inversion'])
    df_subsidy_and_cleaning['total_subsidio'] = robust_numeric_clean(df_subsidy_and_cleaning['total_subsidio'])
    df_utility_subsidy['valor'] = robust_numeric_clean(df_utility_subsidy['valor'])
    df_epm_subsidies_contributions['valor'] = robust_numeric_clean(df_epm_subsidies_contributions['valor'])

    print("Generando agregaciones por Comuna...")

    # 4. Procesamiento de Agregaciones Sectoriales (Exactamente UNA vez por variable)
    agg_investment = df_investment_by_commune_and_district.groupby('commune_clean').agg(
        total_investment=('Inversion', 'sum')
    ).reset_index()

    agg_health = df_subsidized_health_regime_affiliates.groupby('commune_clean').agg(
        total_subsidized_health_affiliates=('consecutivo', 'count'),
        mean_health_age=('edad', 'mean')
    ).reset_index()

    agg_inclusion = df_social_inclusion_actions_for_people_with_disabilities.groupby('commune_clean').agg(
        total_disabled_and_inclusion_beneficiaries=('CONDICIÓN DE DISCAPACIDAD', 'count'),
        mean_inclusion_age=('AÑOS CUMPLIDOS AL INGRESO DEL PROGRAMA', 'mean')
    ).reset_index()

    agg_scholarships = df_scholarship.groupby('commune_clean').agg(
        total_scholarship_beneficiaries=('CONVOCATORIA', 'count')
    ).reset_index()

    # Cálculo seguro de Totales Globales Municipales
    total_health_affiliates_global = agg_health['total_subsidized_health_affiliates'].sum() + 1

    total_utility_val = df_utility_subsidy['valor'].sum()
    mean_utility_strat = df_utility_subsidy['estrato'].mean()
    total_epm_contrib_val = df_epm_subsidies_contributions['valor'].sum()

    total_cleaning_val = df_subsidy_and_cleaning['total_subsidio'].sum()
    total_cleaning_subs = df_subsidy_and_cleaning['suscriptores_subsidiados'].sum()

    # Distribución Proporcional de Servicios Públicos Basada en Demografía Vulnerable Real
    agg_utilities = agg_health[['commune_clean']].copy()
    agg_utilities['total_utility_subsidies'] = (
            (agg_health['total_subsidized_health_affiliates'] / total_health_affiliates_global) * (
                total_utility_val + total_epm_contrib_val)
    )
    agg_utilities['mean_utility_stratum'] = mean_utility_strat

    # Distribución Proporcional de Subsidio de Aseo
    agg_cleaning = agg_health[['commune_clean']].copy()
    agg_cleaning['total_cleaning_subsidies'] = (
            (agg_health['total_subsidized_health_affiliates'] / total_health_affiliates_global) * total_cleaning_val
    )
    agg_cleaning['total_subsidized_cleaning_subscribers'] = (
            (agg_health['total_subsidized_health_affiliates'] / total_health_affiliates_global) * total_cleaning_subs
    ).astype(int)

    print("Consolidando Matriz Maestra Analítica (Data Mashup)...")

    # 5. Integración mediante Universos Geográficos Completo (Left Joins sobre base integrada)
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

    # Rellenar con 0 de forma segura para comunas que no tengan registros específicos en algún sector
    master_matrix = master_matrix.fillna(0)

    # 6. Feature Engineering Final (Variables Sintéticas)
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
