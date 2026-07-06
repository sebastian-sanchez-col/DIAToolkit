# model_trainer.py

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from data_processor import MODEL_FEATURE_COLUMNS, diagnostic_correlation_check


def diagnostic_and_fix_zeros(df_analytics):
    """Checks if critical columns are completely zero and warns the user."""
    critical_cols = ["total_investment"]
    for col in critical_cols:
        if df_analytics[col].sum() == 0:
            print(f"[ALERTA] La columna '{col}' está completamente en cero. "
                  f"Verifica las conversiones de texto a número o las llaves de cruce.")
    return df_analytics


def train_advanced_models(df_display, df_panel):
    """
    df_display: Matrix with ONE row per commune/district (21 rows). Used
        for vulnerability clustering and for everything displayed on the
        dashboard/table/chatbot (does not have an 'anio' column).
    df_panel: Matrix with one row per commune x year (higher N). Used
        exclusively to train the Random Forest, as it includes the 'anio' column
        defined in MODEL_FEATURE_COLUMNS.
    """
    print("\n====================================================")
    print("INICIANDO FASE DE INTELIGENCIA ARTIFICIAL AVANZADA")
    print("====================================================")

    df_panel = diagnostic_and_fix_zeros(df_panel)

    # --- 1. VULNERABILITY CLUSTERING (on the 1-row-per-commune matrix) ---
    df_display = df_display.copy()
    df_display['inverse_stratum'] = 7 - df_display['mean_utility_stratum']  # lower stratum = higher vulnerability

    cluster_features = [
        "total_subsidized_health_affiliates",
        "total_disabled_and_inclusion_beneficiaries",
        "inverse_stratum",
    ]

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_display[cluster_features])

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    raw_clusters = kmeans.fit_predict(scaled_data)

    centroid_sums = kmeans.cluster_centers_.sum(axis=1)
    sorted_cluster_indices = np.argsort(centroid_sums)

    cluster_mapping = {
        sorted_cluster_indices[2]: 0,  # Higher vulnerability -> Alto
        sorted_cluster_indices[1]: 1,  # Medio
        sorted_cluster_indices[0]: 2,  # Lower vulnerability -> Bajo
    }
    df_display["vulnerability_cluster"] = np.vectorize(cluster_mapping.get)(raw_clusters)
    df_display.drop(columns=['inverse_stratum'], inplace=True)

    # --- 2. PRESCRIPTIVE MODEL (on the panel matrix, with higher N and 'anio') ---
    X = df_panel[MODEL_FEATURE_COLUMNS]
    y_raw = df_panel["total_investment"]

    print("Entrenando Modelo Prescriptivo de Inversión Territorial "
          f"(target real, sin fuga de datos, N={len(X)}, features={MODEL_FEATURE_COLUMNS})...")

    rf_model = RandomForestRegressor(n_estimators=150, max_depth=5, random_state=42)
    diagnostic_correlation_check(df_panel, label_for_log="Entrenamiento RF (panel)")
    rf_model.fit(X, y_raw)

    pure_importances = rf_model.feature_importances_
    ai_insights = dict(zip(X.columns, pure_importances))

    print("====================================================\n")

    return df_display, ai_insights, rf_model