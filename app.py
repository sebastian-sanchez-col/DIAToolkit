# app.py

from flask import Flask, render_template, request, jsonify
import pandas as pd
from data_processor import (process_and_create_master_matrix, MODEL_FEATURE_COLUMNS,
                             FEATURE_TRANSLATION, TIMELINESS_STALE_DAYS_WARNING)
from model_trainer import train_advanced_models
from chatbot_nlp import get_assistant_response

app = Flask(__name__)

def run_pipeline():
    print("[INFO PIPELINE] Ejecutando rutinas de agregación de datos reales desde data_processor...")
    # process_and_create_master_matrix() returns 3 values:
    #   - raw_matrix (display, 1 row per commune, for dashboard/chatbot)
    #   - city_level_metrics (aggregated only at city level)
    #   - matrix_panel (1 row per commune x year, to train the model with higher N)
    raw_matrix, city_level_metrics, matrix_panel = process_and_create_master_matrix()

    print("[INFO PIPELINE] Ajustando modelos avanzados de Machine Learning sobre métricas de producción...")
    df_final, ai_insights, rf_model = train_advanced_models(raw_matrix, matrix_panel)

    print("[ÉXITO PIPELINE] Asignación de memoria completa. Pipelines completamente unificados.")
    return df_final, ai_insights, rf_model, city_level_metrics


df_master, ai_insights, trained_rf, city_level_metrics = run_pipeline()

# Simulation year range: MIN is the oldest year with recorded actual investment;
# MAX is the year following the last observed year (the year the model projects).
# DEFAULT starts the slider precisely on that projected year, because that is
# the question the simulator aims to answer ("what would next year's budget look
# like under these conditions?"). They are calculated in this specific order
# on purpose: MAX depends on the data, DEFAULT depends on MAX.
_available_years = city_level_metrics.get('investment_data_years', [])
MIN_SIMULATION_YEAR = min(_available_years) if _available_years else 2024
MAX_SIMULATION_YEAR = (max(_available_years) + 1) if _available_years else MIN_SIMULATION_YEAR
DEFAULT_SIMULATION_YEAR = MAX_SIMULATION_YEAR


@app.route('/')
def index():
    table_data = df_master.to_dict(orient='records')

    quality_scorecard = city_level_metrics.get('quality_scorecard', {})

    df_sorted = df_master.sort_values(by='avg_annual_investment', ascending=False)
    chart_labels = df_sorted['commune_clean'].tolist()
    chart_investment = df_sorted['avg_annual_investment'].tolist()

    ai_labels = [FEATURE_TRANSLATION[col] for col in MODEL_FEATURE_COLUMNS]
    ai_values = [float(ai_insights.get(col, 0)) for col in MODEL_FEATURE_COLUMNS]

    top_commune = df_sorted.iloc[0]['commune_clean'] if not df_sorted.empty else "No Detectada"

    return render_template('dashboard.html',
                           table_data=table_data,
                           chart_labels=chart_labels,
                           chart_investment=chart_investment,
                           ai_labels=ai_labels,
                           ai_values=ai_values,
                           top_commune=top_commune,
                           city_level_metrics=city_level_metrics,
                           min_simulation_year=MIN_SIMULATION_YEAR,
                           max_simulation_year=MAX_SIMULATION_YEAR,
                           default_simulation_year=DEFAULT_SIMULATION_YEAR,
                           quality_scorecard=quality_scorecard,
                           quality_stale_threshold_days=TIMELINESS_STALE_DAYS_WARNING)


@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        stratum = float(request.form.get('stratum', 1))
        health_affiliates = float(request.form.get('health_affiliates', 0))
        disability_programs = float(request.form.get('disability_programs', 0))
        year = float(request.form.get('year', DEFAULT_SIMULATION_YEAR))

        max_trained_year = max(_available_years) if _available_years else None
        if max_trained_year is not None and year > max_trained_year:
            print(f"[ALERTA SIMULADOR] year={year} está fuera del rango de entrenamiento "
                  f"(máximo año observado en los datos: {max_trained_year}). El Random Forest no "
                  f"extrapola tendencias: la predicción para este año equivale, en la práctica, a la "
                  f"del límite superior observado ({max_trained_year}), no a una proyección real de "
                  f"tendencia futura. Tratar este resultado con cautela.")

        total_health_reference = df_master['total_subsidized_health_affiliates'].sum()
        total_inclusion_reference = df_master['total_disabled_and_inclusion_beneficiaries'].sum()

        health_share = health_affiliates / total_health_reference if total_health_reference else 0
        inclusion_share = disability_programs / total_inclusion_reference if total_inclusion_reference else 0

        row = {
            'health_affiliates_share': health_share,
            'inclusion_share': inclusion_share,
            'mean_utility_stratum': stratum,
            'year': year
        }
        input_data = pd.DataFrame([row])[MODEL_FEATURE_COLUMNS]

        prediction = trained_rf.predict(input_data)[0]
        return jsonify({'success': True, 'predicted_investment': float(prediction)})
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)})


@app.route('/chat', methods=['POST'])
def chat():
    print("[HTTP POST] Petición del Chatbot recibida. Enrutando hacia módulo de NLP estadístico...")
    try:
        user_message = request.json.get('message', '')

        bot_response = get_assistant_response(
            user_message, df_master, ai_insights, city_level_metrics
        )

        return jsonify({'success': True, 'response': bot_response})

    except Exception as error:
        print(f"[ERROR CHAT] Excepción detectada durante el procesamiento de tokens: {str(error)}")
        return jsonify({'success': False, 'error': str(error)})


if __name__ == '__main__':
    print("[INICIO SISTEMA] Inicializando el contenedor de Flask en el puerto 5000...")
    app.run(debug=True, use_reloader=False, port=5000)