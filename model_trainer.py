# model_trainer.py

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import GroupKFold
from sklearn.inspection import partial_dependence

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
    df_display: A matrix with ONE row per commune/district (21 rows total). It is used
        for the vulnerability clustering and for everything displayed on the
        dashboard, tables, or chatbot (it does not contain an 'anio' column).
    df_panel: A matrix with one row per commune x year (larger N). It is used exclusively
        to train the Random Forest model, as it includes the 'anio' column defined
        in MODEL_FEATURE_COLUMNS.
    """
    print("\n====================================================")
    print("INICIANDO FASE DE INTELIGENCIA ARTIFICIAL")
    print("====================================================")

    df_panel = diagnostic_and_fix_zeros(df_panel)

    # --- 1. VULNERABILITY CLUSTERING (on the 1 row per commune matrix) ---
    df_display = df_display.copy()
    df_display['inverse_stratum'] = 7 - df_display['mean_utility_stratum']  # menor estrato = mayor vulnerabilidad

    cluster_features = [
        "health_affiliates_share",
        "inclusion_share",
        "inverse_stratum",
    ]

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_display[cluster_features])

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    raw_clusters = kmeans.fit_predict(scaled_data)

    centroid_sums = kmeans.cluster_centers_.sum(axis=1)
    sorted_cluster_indices = np.argsort(centroid_sums)

    cluster_mapping = {
        sorted_cluster_indices[2]: 0,  # Mayor vulnerabilidad -> Alto
        sorted_cluster_indices[1]: 1,  # Medio
        sorted_cluster_indices[0]: 2,  # Menor vulnerabilidad -> Bajo
    }
    df_display["vulnerability_cluster"] = np.vectorize(cluster_mapping.get)(raw_clusters)
    df_display.drop(columns=['inverse_stratum'], inplace=True)

    # --- 2. PRESCRIPTIVE MODEL (on the panel matrix, with larger N and containing 'anio') ---
    X = df_panel[MODEL_FEATURE_COLUMNS]
    y_raw = df_panel["total_investment"]

    print("Entrenando Modelo Prescriptivo de Inversión Territorial "
          f"(target real, sin fuga de datos, N={len(X)}, features={MODEL_FEATURE_COLUMNS})...")

    diagnostic_correlation_check(df_panel, label_for_log="Entrenamiento RF (panel)")

    # VALIDATION: With an N this low (21 communes x few years), it is easy for the
    # model to simply memorize. A row-by-row train_test_split allows the SAME commune
    # to appear in both train and test (just in different years), which inflates the R²
    # because the model is not predicting on a new territory, but rather on "this same
    # commune, another year." We use GroupKFold grouping by commune (commune_clean) so
    # that each fold leaves ENTIRE communes out of the training, measuring true
    # generalization to unseen territories.
    groups = df_panel["commune_clean"]
    n_communes = groups.nunique()

    if n_communes >= 5:
        n_splits = min(5, n_communes)
        gkf = GroupKFold(n_splits=n_splits)

        fold_r2_scores = []
        fold_mae_scores = []
        fold_n_test = []

        for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, y_raw, groups=groups)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y_raw.iloc[train_idx], y_raw.iloc[test_idx]

            rf_fold = RandomForestRegressor(n_estimators=150, max_depth=5, random_state=42)
            rf_fold.fit(X_train, y_train)
            y_pred = rf_fold.predict(X_test)

            fold_r2_scores.append(r2_score(y_test, y_pred))
            fold_mae_scores.append(mean_absolute_error(y_test, y_pred))
            fold_n_test.append(len(X_test))

        r2_mean = float(np.mean(fold_r2_scores))
        r2_std = float(np.std(fold_r2_scores))
        mae_mean = float(np.mean(fold_mae_scores))

        print(f"[VALIDACIÓN MODELO - GroupKFold por comuna, k={n_splits}] "
              f"R² promedio = {r2_mean:.3f} (± {r2_std:.3f}) | MAE promedio = ${mae_mean:,.2f} COP")
        print(f"  └─ R² por fold: {[round(r, 3) for r in fold_r2_scores]}")
        print(f"  └─ Folds dejan comunas COMPLETAS fuera del entrenamiento (no solo años sueltos), "
              f"midiendo generalización real a territorio no visto.")

        if r2_mean < 0.3:
            print("  ⚠️ ALERTA: R² promedio bajo bajo validación agrupada por comuna. Con este N y "
                  "estas variables, el modelo tiene poder predictivo limitado sobre comunas no vistas. "
                  "Es honesto reportarlo así en la sustentación.")

        model_validation_metrics = {
            'r2_mean_groupkfold': r2_mean,
            'r2_std_groupkfold': r2_std,
            'mae_mean_groupkfold': mae_mean,
            'n_splits': n_splits,
            'validation_method': 'GroupKFold por comuna (commune_clean)',
        }
    else:
        print("[VALIDACIÓN MODELO] Muy pocas comunas distintas para GroupKFold confiable.")
        model_validation_metrics = {
            'r2_mean_groupkfold': None, 'r2_std_groupkfold': None,
            'mae_mean_groupkfold': None, 'n_splits': 0,
            'validation_method': 'GroupKFold por comuna (commune_clean)',
        }

    # Final model: Trained on 100% of the available data (standard practice
    # once it has been validated above that the general approach generalizes reasonably well).
    rf_model = RandomForestRegressor(n_estimators=150, max_depth=5, random_state=42)
    rf_model.fit(X, y_raw)
    diagnostic_partial_dependence_stratum(rf_model, X, feature_name="mean_utility_stratum")

    pure_importances = rf_model.feature_importances_
    ai_insights = dict(zip(X.columns, pure_importances))
    rf_model.validation_metrics_ = model_validation_metrics

    print("====================================================\n")

    return df_display, ai_insights, rf_model


def diagnostic_partial_dependence_stratum(rf_model, X, feature_name="mean_utility_stratum"):
    """
    Verifies whether the effect of 'mean_utility_stratum' on the Random Forest
    prediction is consistent with the observed simple correlation, or if it is
    an artifact of small data / out-of-range extrapolation.

    Calculates partial dependence: For a grid of values of the variable
    (e.g., stratum from 1 to 6), it fixes that variable and averages the
    model's prediction across ALL observed combinations of the other variables.
    This isolates the effect of 'mean_utility_stratum' from the rest.
    """
    if feature_name not in X.columns:
        print(f"[DIAGNÓSTICO PDP] La variable '{feature_name}' no está en las features del modelo.")
        return

    feature_idx = list(X.columns).index(feature_name)

    pdp_result = partial_dependence(
        rf_model, X, features=[feature_idx], kind="average", grid_resolution=20
    )

    grid_values = pdp_result["values"][0] if "values" in pdp_result else pdp_result["grid_values"][0]
    avg_predictions = pdp_result["average"][0]

    print(f"\n[DIAGNÓSTICO PDP - Dependencia Parcial de '{feature_name}']")
    print(f"  Rango real observado en los datos: {X[feature_name].min():.2f} a {X[feature_name].max():.2f}")
    print(f"  └─ Valor de '{feature_name}' -> Predicción promedio de inversión ($ COP):")
    for val, pred in zip(grid_values, avg_predictions):
        print(f"       {val:.2f} -> ${pred:,.2f}")

    # Monotonicity check: Does the effect fluctuate erratically (a sign of
    # noise/overfitting) or is it a clear trend in one direction?
    # 🆕 Minor changes below 1% of the total prediction range are ignored, to
    # avoid confusing numerical noise from the trees (variations of tenths of
    # a percentage) with a true trend reversal.
    pred_range = avg_predictions.max() - avg_predictions.min()
    noise_threshold = pred_range * 0.01

    diffs = np.diff(avg_predictions)
    n_increases = (diffs > noise_threshold).sum()
    n_decreases = (diffs < -noise_threshold).sum()

    if n_increases > 0 and n_decreases > 0:
        print(f"  ⚠️ ALERTA: el efecto de '{feature_name}' NO es monotónico ({n_increases} tramos suben, "
              f"{n_decreases} tramos bajan de forma significativa, ignorando ruido menor al 1% del rango). "
              f"Esto sugiere que el modelo está capturando interacciones complejas con las otras variables, "
              f"o que con N tan bajo el patrón puede ser inestable/poco confiable, más que una relación "
              f"causal clara con el estrato.")
    elif n_increases > 0:
        print(f"  └─ El efecto es consistentemente POSITIVO (a mayor estrato, mayor inversión predicha) "
              f"en todo el rango observado.")
    else:
        print(f"  └─ El efecto es consistentemente NEGATIVO o PLANO (a mayor estrato, menor o igual inversión "
              f"predicha), lo cual SÍ es coherente con la correlación simple negativa (r=-0.158) reportada antes.")

    # 🆕 Separate alert for the starting point, as it contains the only
    # large and suspicious change (possible extrapolation with low N at the
    # extreme of the observed range).
    first_jump_pct = abs(diffs[0]) / avg_predictions[0] * 100 if avg_predictions[0] else 0
    if first_jump_pct > 20:
        print(f"  ⚠️ ALERTA: el primer tramo del rango (valor={grid_values[0]:.2f}) muestra un salto de "
              f"{first_jump_pct:.1f}% respecto al siguiente punto. Es probable que haya muy pocas "
              f"comunas/años observados en ese extremo del estrato; tratar esa zona del modelo con cautela "
              f"y no usarla como base fuerte de conclusiones o del simulador.")