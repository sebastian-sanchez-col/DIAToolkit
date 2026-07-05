from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from data_processor import process_and_create_master_matrix
from model_trainer import train_advanced_models

app = Flask(__name__)


def run_pipeline():
    """Triggers the full analytic data architecture sequence: Processing -> Machine Learning Model Training."""
    raw_matrix = process_and_create_master_matrix()
    df_final, ai_insights = train_advanced_models(raw_matrix)
    return df_final, ai_insights


# Global initialization: pipeline executes once on server startup
df_master, ai_insights = run_pipeline()


X_predictive = df_master[[
    'total_investment', 'mean_utility_stratum', 'total_subsidized_health_affiliates',
    'total_disabled_and_inclusion_beneficiaries', 'total_scholarship_beneficiaries'
]]
y_target = df_master['total_combined_subsidies']
assistant_rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
assistant_rf_model.fit(X_predictive, y_target)


@app.route('/')
def index():
    table_data = df_master.to_dict(orient='records')
    df_sorted = df_master.sort_values(by='total_combined_subsidies', ascending=False)
    chart_labels = df_sorted['commune_clean'].tolist()
    chart_subsidies = df_sorted['total_combined_subsidies'].tolist()

    ai_labels = list(ai_insights.keys())
    ai_values = list(ai_insights.values())
    top_commune = df_sorted.iloc[0]['commune_clean'] if not df_sorted.empty else "No Detectada"

    return render_template('dashboard.html',
                           table_data=table_data,
                           chart_labels=chart_labels,
                           chart_subsidies=chart_subsidies,
                           ai_labels=ai_labels,
                           ai_values=ai_values,
                           top_commune=top_commune)


@app.route('/assistant_query', methods=['POST'])
def assistant_query():
    """Endpoint processing live user parameters through the trained Machine Learning Assistant."""
    try:
        # Extract features input asynchronously from the citizen-facing interface
        investment = float(request.form.get('investment', 0))
        stratum = float(request.form.get('stratum', 1))
        health_affiliates = float(request.form.get('health_affiliates', 0))
        disability_programs = float(request.form.get('disability_programs', 0))
        scholarships = float(request.form.get('scholarships', 0))

        # Structure the query vector to match the precise Random Forest features
        input_data = pd.DataFrame([{
            'total_investment': investment,
            'mean_utility_stratum': stratum,
            'total_subsidized_health_affiliates': health_affiliates,
            'total_disabled_and_inclusion_beneficiaries': disability_programs,
            'total_scholarship_beneficiaries': scholarships
        }])

        # Generate the live prescription response array
        prediction = assistant_rf_model.predict(input_data)[0]

        return jsonify({'success': True, 'predicted_subsidies': float(prediction)})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)