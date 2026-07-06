# app.py

from flask import Flask, render_template, request, jsonify
import pandas as pd
from data_processor import process_and_create_master_matrix, MODEL_FEATURE_COLUMNS
from model_trainer import train_advanced_models
from chatbot_nlp import obtener_respuesta_asistente

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

# Default year for the simulator: the next unobserved year in the data
# (projection), or the latest available year if for some reason none exist.
_available_years = city_level_metrics.get('investment_data_years', [])
DEFAULT_SIMULATION_YEAR = (max(_available_years) + 1) if _available_years else 2024
MIN_SIMULATION_YEAR = min(_available_years) if _available_years else DEFAULT_SIMULATION_YEAR
MAX_SIMULATION_YEAR = DEFAULT_SIMULATION_YEAR


@app.route('/')
def index():
    table_data = df_master.to_dict(orient='records')

    df_sorted = df_master.sort_values(by='total_investment', ascending=False)
    chart_labels = df_sorted['commune_clean'].tolist()
    chart_investment = df_sorted['total_investment'].tolist()

    ai_labels = [
        "Densidad Demográfica Vulnerable (Régimen Subsidiado)",
        "Vulnerabilidad Prioritaria (Acciones de Inclusión Social)",
        "Nivel de Capacidad Socioeconómica Promedio (Estrato)",
        "Año de la Inversión (Tendencia Temporal Multi-Año)",
    ]
    ai_values = [
        float(ai_insights.get('health_affiliates_share', 0)),
        float(ai_insights.get('inclusion_share', 0)),
        float(ai_insights.get('mean_utility_stratum', 0)),
        float(ai_insights.get('anio', 0)),
    ]

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
                           default_simulation_year=DEFAULT_SIMULATION_YEAR)


@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        stratum = float(request.form.get('stratum', 1))
        health_affiliates = float(request.form.get('health_affiliates', 0))
        disability_programs = float(request.form.get('disability_programs', 0))
        anio = float(request.form.get('anio', DEFAULT_SIMULATION_YEAR))

        total_health_reference = df_master['total_subsidized_health_affiliates'].sum()
        total_inclusion_reference = df_master['total_disabled_and_inclusion_beneficiaries'].sum()

        health_share = health_affiliates / total_health_reference if total_health_reference else 0
        inclusion_share = disability_programs / total_inclusion_reference if total_inclusion_reference else 0

        row = {
            'health_affiliates_share': health_share,
            'inclusion_share': inclusion_share,
            'mean_utility_stratum': stratum,
            'anio': anio,
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

        bot_response = obtener_respuesta_asistente(
            user_message, df_master, ai_insights, city_level_metrics
        )

        return jsonify({'success': True, 'response': bot_response})

    except Exception as error:
        print(f"[ERROR CHAT] Excepción detectada durante el procesamiento de tokens: {str(error)}")
        return jsonify({'success': False, 'error': str(error)})


if __name__ == '__main__':
    print("[INICIO SISTEMA] Inicializando el contenedor de Flask en el puerto 5000...")
    app.run(debug=True, use_reloader=False, port=5000)