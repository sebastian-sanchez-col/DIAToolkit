# main.py
from data_processor import process_and_create_master_matrix
from model_trainer import train_advanced_models


def main():
    print("====================================================")
    print("SISTEMA DE ANALÍTICA PRESCRIPTIVA - MEDELLÍN")
    print("====================================================\n")

    # 1. Run Data Engineering Pipeline
    df_analytics = process_and_create_master_matrix()

    # 2. Run Advanced AI & Machine Learning Pipeline
    df_final_results, trained_rf = train_advanced_models(df_analytics)

    print("\n[PROCESO GLOBAL COMPLETADO]")
    print("Muestra final con asignación de clúster socio-económico:")
    print(df_final_results[['commune_clean', 'vulnerability_cluster', 'total_combined_subsidies']].head(5))

def df_data_recognizer():
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
    # Subsidios y Contribuciones-EPM - Energía, Gas, Acueducto y Alcantarillado
    # Source: https://www.datos.gov.co/dataset/Subsidios-y-Contribuciones-EPM-Energ-a-Gas-Acueduc/dag3-4sey/about_data
    df_epm_subsidies_contributions = pd.read_csv('sources/subsidio_contribuciones_epm.csv')
    # Implementación de acciones de inclusión social para personas con discapacidad familiares y cuidadores 2023
    # Source: https://www.datos.gov.co/dataset/Implementaci-n-de-acciones-de-inclusi-n-social-par/hdjq-kape/about_data
    df_social_inclusion_actions_for_people_with_disabilities = pd.read_csv(
        'sources/implementacion_acciones_personas_discapacidad_familiares_cuidadores_2023.csv')

    print('Beneficiarios de becas y créditos')
    print(df_scholarship.columns.tolist())
    print('Subsidios y contribuciones de servicios')
    print(df_utility_subsidy.columns.tolist())
    print('Afiliados al regimen subsidiado')
    print(df_subsidized_health_regime_affiliates.columns.tolist())
    print('Subsidios y contribuciones aseo')
    print(df_subsidy_and_cleaning.columns.tolist())
    print('Inversión por comuna y corregimiento Medellín 2017')
    print(df_investment_by_commune_and_district.columns.tolist())
    print('Subsidios y Contribuciones-EPM - Energía, Gas, Acueducto y Alcantarillado')
    print(df_epm_subsidies_contributions.columns.tolist())
    print(
        'Implementación de acciones de inclusión social para personas con discapacidad familiares y cuidadores 2023')
    print(df_social_inclusion_actions_for_people_with_disabilities.columns.tolist())

if __name__ == "__main__":
    main()