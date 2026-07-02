# model_trainer.py

from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


def diagnostic_and_fix_zeros(df_analytics):
    """Checks if critical columns are completely zero and warns the user."""
    critical_cols = ['total_utility_subsidies', 'total_cleaning_subsidies', 'total_combined_subsidies']
    for col in critical_cols:
        if df_analytics[col].sum() == 0:
            print(f"[WARNING] Column '{col}' is entirely zero. Check string-to-numeric conversions or merging keys.")
    return df_analytics


def train_advanced_models(df_analytics):
    print("\n====================================================")
    print("INICIANDO FASE DE INTELIGENCIA ARTIFICIAL AVANZADA")
    print("====================================================")

    # 0. Data Diagnostics
    df_analytics = diagnostic_and_fix_zeros(df_analytics)

    # Define features for the AI models (excluding the geometric text identification)
    feature_columns = [
        'total_investment', 'total_utility_subsidies', 'mean_utility_stratum',
        'total_subsidized_health_affiliates', 'mean_health_age',
        'total_disabled_and_inclusion_beneficiaries', 'mean_inclusion_age',
        'total_scholarship_beneficiaries', 'total_cleaning_subsidies',
        'total_subsidized_cleaning_subscribers', 'investment_per_capita_subsidized',
        'disability_pressure_index', 'total_combined_subsidies'
    ]

    X = df_analytics[feature_columns]

    # 1. DETECCIÓN DE PATRONES COMPLEJOS: Clustering (K-Means)
    print("\n[1/2] Ejecutando Clustering No Supervisado (K-Means)...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # We group communes into 3 socio-territorial categories (High, Medium, Low Vulnerability)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df_analytics['vulnerability_cluster'] = kmeans.fit_predict(X_scaled)

    print("-> Clústeres territoriales creados con éxito.")

    # 2. MODELADO PREDICTIVO ELABORADO: Random Forest Regressor
    print("\n[2/2] Entrenando Random Forest Regressor...")
    # Objective: Predict the combined subsidies load based on social pressure variables
    y_target = df_analytics['total_combined_subsidies']
    X_predictive = df_analytics[[
        'total_investment', 'mean_utility_stratum', 'total_subsidized_health_affiliates',
        'total_disabled_and_inclusion_beneficiaries', 'total_scholarship_beneficiaries'
    ]]

    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_predictive, y_target)

    # Feature Importances extraction
    importances = rf_model.feature_importances_
    print("-> Modelo Random Forest entrenado para simulación prescriptiva.")

    print("\n====================================================")
    print("INSIGHTS ACCIONABLES GENERADOS PARA EL ASISTENTE VIRTUAL")
    print("====================================================")

    # Display results for decision makers
    for i, col in enumerate(X_predictive.columns):
        print(f"Impacto de variable '{col}' en la demanda de subsidios: {importances[i] * 100:.2f}%")

    return df_analytics, rf_model