from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from data_processor import process_and_create_master_matrix
from model_trainer import train_advanced_models

app = Flask(__name__)


def run_pipeline():
    """
    Triggers the full analytic data architecture sequence and captures the optimized ML model.
    Loads real production information from data.gov.co directly into RAM memory.
    """
    print("[INFO PIPELINE] Ejecutando rutinas de agregación de datos reales desde data_processor...")
    raw_matrix = process_and_create_master_matrix()

    print("[INFO PIPELINE] Ajustando modelos avanzados de Machine Learning sobre métricas de producción...")
    df_final, ai_insights, rf_model = train_advanced_models(raw_matrix)

    print("[ÉXITO PIPELINE] Asignación de memoria completa. Pipelines completamente unificados.")
    return df_final, ai_insights, rf_model


# Global startup execution: Data pipeline and model loading execute exactly once in RAM
df_master, ai_insights, trained_rf = run_pipeline()


@app.route('/')
def index():
    print("[HTTP GET] Cargando las vistas de datos del dashboard maestro...")
    table_data = df_master.to_dict(orient='records')

    # Sort data streams in descending order so visual charts automatically sort from highest to lowest load
    df_sorted = df_master.sort_values(by='total_combined_subsidies', ascending=False)
    chart_labels = df_sorted['commune_clean'].tolist()
    chart_subsidies = df_sorted['total_combined_subsidies'].tolist()

    # Structural labels and values mapped to target the exact UI Chart.js container
    ai_labels = [
        "Densidad Demográfica Vulnerable (Régimen Subsidiado)",
        "Vulnerabilidad Prioritaria (Acciones de Inclusión Social)",
        "Presupuesto de Inversión Territorial Ejecutado (Medellín)",
        "Nivel de Capacidad Socioeconómica Promedio (Estrato)",
        "Acceso a Educación Superior (Beneficiarios de Becas)"
    ]

    ai_values = [
        float(ai_insights.get('total_subsidized_health_affiliates', 0)),
        float(ai_insights.get('total_disabled_and_inclusion_beneficiaries', 0)),
        float(ai_insights.get('total_investment', 0)),
        float(ai_insights.get('mean_utility_stratum', 0)),
        float(ai_insights.get('total_scholarship_beneficiaries', 0))
    ]

    top_commune = df_sorted.iloc[0]['commune_clean'] if not df_sorted.empty else "No Detectada"

    return render_template('dashboard.html',
                           table_data=table_data,
                           chart_labels=chart_labels,
                           chart_subsidies=chart_subsidies,
                           ai_labels=ai_labels,
                           ai_values=ai_values,
                           top_commune=top_commune)


@app.route('/simulate', methods=['POST'])
def simulate():
    """API Endpoint that receives HTML form inputs and predicts via the globally unified AI model."""
    print("[HTTP POST] Escenario de simulación recibido. Iniciando recálculo de inferencia...")
    try:
        investment = float(request.form.get('investment', 0))
        stratum = float(request.form.get('stratum', 1))
        health_affiliates = float(request.form.get('health_affiliates', 0))
        disability_programs = float(request.form.get('disability_programs', 0))
        scholarships = float(request.form.get('scholarships', 0))

        # Build evaluation vector matching the EXACT structure and order trained inside model_trainer.py
        input_data = pd.DataFrame([{
            'total_subsidized_health_affiliates': health_affiliates,
            'total_disabled_and_inclusion_beneficiaries': disability_programs,
            'total_investment': investment,
            'mean_utility_stratum': stratum,
            'total_scholarship_beneficiaries': scholarships
        }])

        prediction = trained_rf.predict(input_data)[0]
        print(f"[ÉXITO SIMULACIÓN] Valor estimado del escenario: ${prediction:,.2f} COP")

        return jsonify({'success': True, 'predicted_subsidies': float(prediction)})

    except Exception as error:
        print(f"[FALLO SIMULACIÓN] Ruptura operativa estructural: {str(error)}")
        return jsonify({'success': False, 'error': str(error)})


@app.route('/chat', methods=['POST'])
def chat():
    """
    Conversational interface routing engine.
    Looks up live metadata inside the uncopied memory stream of df_master.
    """
    print("[HTTP POST] Petición del Chatbot recibida. Analizando patrones de intención...")
    try:
        user_message = request.json.get('message', '').lower().strip()

        # Calculate dynamic insights directly on top of the live un-burned dataframe streams
        df_sorted = df_master.sort_values(by='total_combined_subsidies', ascending=False)
        max_sub_row = df_sorted.iloc[0] if not df_sorted.empty else None
        min_sub_row = df_sorted.iloc[-1] if not df_sorted.empty else None
        avg_subsidies = df_master['total_combined_subsidies'].mean() if not df_master.empty else 0

        # Features map array matching the sequence inside the training matrix parameters
        features_keys = [
            'total_subsidized_health_affiliates',
            'total_disabled_and_inclusion_beneficiaries',
            'total_investment',
            'mean_utility_stratum',
            'total_scholarship_beneficiaries'
        ]

        # Dynamically lookup the dominant factor calculated by the loaded RandomForest instance
        importance_scores = trained_rf.feature_importances_
        max_idx = np.argmax(importance_scores)
        dominant_feature = features_keys[max_idx]

        feature_translation = {
            'total_subsidized_health_affiliates': 'Densidad Demográfica Vulnerable (Régimen Subsidiado)',
            'total_disabled_and_inclusion_beneficiaries': 'Vulnerabilidad Prioritaria (Inclusión Social)',
            'total_investment': 'Presupuesto de Inversión Territorial Ejecutado',
            'mean_utility_stratum': 'Nivel de Capacidad Socioeconómica Promedio (Estrato)',
            'total_scholarship_beneficiaries': 'Acceso a Educación Superior (Becas)'
        }
        translated_feature = feature_translation.get(dominant_feature, dominant_feature)

        # Localized chat logic loops handling contextual responses
        if 'hola' in user_message or 'buenos' in user_message or 'tardes' in user_message:
            bot_response = (
                "¡Hola! Soy tu Asistente de IA para el Reto 7. Puedo ayudarte a analizar "
                "la asignación de subsidios y el comportamiento del modelo predictivo en Medellín. "
                "¿Qué te gustaría consultar hoy?"
            )
        elif 'comuna' in user_message or 'territorio' in user_message or 'mayor' in user_message or 'máximo' in user_message:
            if max_sub_row is not None:
                bot_response = (
                    "Analizando la matriz territorial, la zona con **mayor asignación presupuestal** proyectada "
                    f"es **{max_sub_row['commune_clean']}** con un monto estimado de "
                    f"${max_sub_row['total_combined_subsidies']:,.2f} COP."
                )
            else:
                bot_response = "Aún no se registran datos territoriales cargados."
        elif 'menor' in user_message or 'mínimo' in user_message or 'corregimiento' in user_message:
            if min_sub_row is not None:
                bot_response = (
                    "Consultando los registros históricos filtrados, la zona con **menor asignación** proyectada "
                    f"corresponde a **{min_sub_row['commune_clean']}** con un monto estimado de "
                    f"${min_sub_row['total_combined_subsidies']:,.2f} COP."
                )
            else:
                bot_response = "Aún no se registran datos territoriales cargados."
        elif 'variable' in user_message or 'importancia' in user_message or 'modelo' in user_message or 'ia' in user_message:
            bot_response = (
                "De acuerdo con las ganancias de información matemáticas de nuestro Random Forest Regressor, "
                f"la variable con **mayor peso predictivo** en la ecuación actual es: **{translated_feature}**. "
                "Ella es la encargada de guiar la mayor parte de las divisiones en los árboles de decisión."
            )
        elif 'promedio' in user_message or 'media' in user_message or 'total' in user_message:
            bot_response = (
                "Calculando métricas agregadas globales: El **presupuesto promedio proyectado** "
                f"para las comunas y corregimientos analizados se sitúa en **${avg_subsidies:,.2f} COP**."
            )
        else:
            bot_response = (
                "Disculpa, no logré procesar esa consulta exacta. Intenta preguntándome algo como:\n"
                "- *¿Cuál es la comuna con mayor presupuesto?*\n"
                "- *¿Qué variable es la más importante para la IA?*\n"
                "- *¿Cuál es el promedio de subsidios asignados?*"
            )

        return jsonify({'success': True, 'response': bot_response})

    except Exception as error:
        print(f"[ERROR CHAT] Excepción detectada durante el procesamiento de tokens: {str(error)}")
        return jsonify({'success': False, 'error': str(error)})


if __name__ == '__main__':
    print("[INICIO SISTEMA] Inicializando el contenedor de Flask en el puerto 5000...")
    app.run(debug=True, use_reloader=False, port=5000)