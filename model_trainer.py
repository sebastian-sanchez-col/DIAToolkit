# model_trainer.py

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


def diagnostic_and_fix_zeros(df_analytics):
    """Checks if critical columns are completely zero and warns the user."""
    critical_cols = [
        "total_utility_subsidies",
        "total_cleaning_subsidies",
        "total_combined_subsidies",
    ]
    for col in critical_cols:
        if df_analytics[col].sum() == 0:
            print(
                f"[ALERTA] La columna '{col}' está completamente en cero. Verifica las conversiones de texto a número o las llaves de cruce."
            )
    return df_analytics


def train_advanced_models(df_analytics):
    print("\n====================================================")
    print("INICIANDO FASE DE INTELIGENCIA ARTIFICIAL AVANZADA")
    print("====================================================")

    # 0. Data Diagnostics
    df_analytics = diagnostic_and_fix_zeros(df_analytics)

    # --- 1. GEOGRAPHIC VULNERABILITY CLUSTERING (K-MEANS) ---
    # We group territories into 3 social vulnerability layers (High, Medium, Low)
    cluster_features = [
        "total_subsidized_health_affiliates",
        "total_disabled_and_inclusion_beneficiaries",
        "total_combined_subsidies",
    ]

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_analytics[cluster_features])

    # Fit K-Means with 3 concrete target clusters
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    raw_clusters = kmeans.fit_predict(scaled_data)

    # Dynamically sort clusters based on true centroid magnitudes
    # We sum the raw centroids coordinates to establish a consistent mathematical ranking.
    # Higher centroid coordinate sums indicate higher density of vulnerability factors.
    centroid_sums = kmeans.cluster_centers_.sum(axis=1)

    # Create a deterministic mapping array:
    # argsort sorts from lowest to highest magnitude.
    sorted_cluster_indices = np.argsort(centroid_sums)

    # Invert mapping for user-facing alignment:
    # 0 -> High Vulnerability (Highest centroid sum)
    # 1 -> Medium Vulnerability
    # 2 -> Low Vulnerability (Lowest centroid sum)
    cluster_mapping = {
        sorted_cluster_indices[2]: 0,  # Highest becomes 0 (Alto)
        sorted_cluster_indices[1]: 1,  # Intermediate becomes 1 (Medio)
        sorted_cluster_indices[0]: 2  # Lowest becomes 2 (Bajo)
    }

    # Map the arbitrary algorithm tags into consistent semantic categories
    df_analytics["vulnerability_cluster"] = np.vectorize(cluster_mapping.get)(raw_clusters)

    # --- 2. PRESCRIPTIVE SCENARIO MODELING (RANDOM FOREST) ---
    # Isolate training features using the clean parameters passed into the pipeline
    X = df_analytics[
        [
            "total_subsidized_health_affiliates",
            "total_disabled_and_inclusion_beneficiaries",
            "total_investment",
            "mean_utility_stratum",
            "total_scholarship_beneficiaries",
        ]
    ]

    # Target variable to predict
    y_raw = df_analytics["total_combined_subsidies"]

    print("Entrenando Modelo Prescriptivo de Escenarios Territoriales...")

    # Enforcing data integrity by training strictly on the genuine target variable.
    rf_model = RandomForestRegressor(n_estimators=150, max_depth=5, random_state=42)
    rf_model.fit(X, y_raw)

    # Extracting pure mathematical feature importances straight from the split nodes.
    pure_importances = rf_model.feature_importances_

    # Build the dictionary that app.py reads via ai_insights using raw metrics
    ai_insights = dict(zip(X.columns, pure_importances))

    print("====================================================\n")

    return df_analytics, ai_insights, rf_model