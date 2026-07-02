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

if __name__ == "__main__":
    main()