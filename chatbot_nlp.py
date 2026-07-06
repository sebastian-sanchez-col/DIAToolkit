# chatbot_nlp.py
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# =====================================================================
# 1. TRAINING CORPUS (Differentiated intents for Stratum and Averages)
# =====================================================================
TRAINING_DATA = {
    "saludo": [
        "hola", "buenos dias", "buenas tardes", "hey", "saludos",
        "que tal", "hola chatbot", "inicio", "comenzar", "hi", "hello"
    ],
    "inversion": [
        "cuanta plata se invirtio", "presupuesto de comunas", "inversion publica",
        "gasto", "dinero", "ejecucion presupuestal", "recursos invertidos",
        "cuanto dinero recibio la comuna", "inversion por territorio", "comuna",
        "territorio", "mayor", "maximo"
    ],
    "subsidios": [
        "que subsidios hay", "ayuda de servicios publicos", "aseo y energia",
        "quien recibe subsidio", "fondos globales", "total combinado",
        "ayudas economicas", "subsidio de epm", "subsidio de aseo", "menor",
        "minimo", "corregimiento"
    ],
    "estrato": [
        "cual es el estrato promedio", "nivel socioeconomico", "estratificacion de medellin",
        "capacidad socioeconomica", "estratos por comuna", "cual es el estrato real",
        "que estrato tiene la zona", "estrato mas bajo", "estrato socioeconomico"
    ],
    "promedio": [
        "promedio general", "media de subsidios", "cuanto es el promedio",
        "total promedio", "promedio global asignado", "media"
    ],
    "modelo_ml": [
        "como funciona el modelo", "que predictor es el mas importante",
        "random forest", "importancia de caracteristicas", "feature importance",
        "que variable pondera mas", "prediccion", "variable", "importancia", "ia"
    ]
}

# =====================================================================
# 2. NLP STATISTICAL TRAINING ENGINE
# =====================================================================
X_train = []
y_train = []

for intent, phrases in TRAINING_DATA.items():
    for phrase in phrases:
        X_train.append(phrase.lower().strip())
        y_train.append(intent)

vectorizer = TfidfVectorizer(ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)

classifier = LogisticRegression(C=1.0)
classifier.fit(X_train_vec, y_train)


# =====================================================================
# 3. PUBLIC INTERACTION INTERFACE
# =====================================================================
def obtener_respuesta_asistente(texto_usuario, df_master, trained_rf):
    """
    Processes raw user text using TF-IDF and maps it probabilistically to an
    intent, dynamically generating responses based on the live master dataframe state.
    """
    if not texto_usuario or pd.isna(texto_usuario):
        return "Por favor, escribe una pregunta para poder ayudarte."

    entrada_limpia = str(texto_usuario).lower().strip()
    texto_vec = vectorizer.transform([entrada_limpia])

    probabilidades = classifier.predict_proba(texto_vec)[0]
    max_idx_intent = np.argmax(probabilidades)
    confianza = probabilidades[max_idx_intent]
    intent_predicho = classifier.classes_[max_idx_intent]

    if confianza < 0.35:
        intent_predicho = "desconocido"

    # Dynamic calculation over the live dataframe streams
    df_sorted = df_master.sort_values(by='total_combined_subsidies', ascending=False)
    max_sub_row = df_sorted.iloc[0] if not df_sorted.empty else None
    min_sub_row = df_sorted.iloc[-1] if not df_sorted.empty else None
    avg_subsidies = df_master['total_combined_subsidies'].mean() if not df_master.empty else 0

    # Stratum metrics calculation for accurate response
    avg_stratum = df_master['mean_utility_stratum'].mean() if not df_master.empty else 0
    df_stratum_sorted = df_master.sort_values(by='mean_utility_stratum', ascending=True)
    lowest_stratum_zone = df_stratum_sorted.iloc[0]['commune_clean'] if not df_stratum_sorted.empty else "N/A"

    # Extract dynamic feature importances from Random Forest
    features_keys = [
        'total_subsidized_health_affiliates',
        'total_disabled_and_inclusion_beneficiaries',
        'total_investment',
        'mean_utility_stratum',
        'total_scholarship_beneficiaries'
    ]
    importance_scores = trained_rf.feature_importances_
    max_feat_idx = np.argmax(importance_scores)
    dominant_feature = features_keys[max_feat_idx]

    feature_translation = {
        'total_subsidized_health_affiliates': 'Densidad Demográfica Vulnerable (Régimen Subsidiado)',
        'total_disabled_and_inclusion_beneficiaries': 'Vulnerabilidad Prioritaria (Inclusión Social)',
        'total_investment': 'Presupuesto de Inversión Territorial Ejecutado',
        'mean_utility_stratum': 'Nivel de Capacidad Socioeconómica Promedio (Estrato Real)',
        'total_scholarship_beneficiaries': 'Acceso a Educación Superior (Becas)'
    }
    translated_feature = feature_translation.get(dominant_feature, dominant_feature)

    # Dictionary mapping for dynamic generation of response payloads
    respuestas = {
        "saludo": (
            "¡Hola! Soy tu Asistente de IA para el Reto 7, optimizado con un motor de NLP "
            "estadístico. Puedo ayudarte a analizar la asignación de subsidios y el "
            "comportamiento de nuestro modelo predictivo. ¿Qué te gustaría consultar hoy?"
        ),
        "inversion": (
            f"Analizando la matriz territorial, la zona con **mayor asignación presupuestal** proyectada "
            f"es **{max_sub_row['commune_clean']}** con un monto estimado de ${max_sub_row['total_combined_subsidies']:,.2f} COP."
            if max_sub_row is not None else "Aún no se registran datos territoriales cargados."
        ),
        "subsidios": (
            f"Consultando los registros históricos filtrados, la zona con **menor asignación** proyectada "
            f"corresponde a **{min_sub_row['commune_clean']}** con un monto estimado de ${min_sub_row['total_combined_subsidies']:,.2f} COP."
            if min_sub_row is not None else "Aún no se registran datos territoriales cargados."
        ),
        "estrato": (
            f"Métricas de Estratificación Socioeconómica: El **estrato promedio ponderado** global "
            f"de los territorios analizados es **{avg_stratum:.2f}**. El territorio con el perfil "
            f"socioeconómico más bajo registrado es **{lowest_stratum_zone}**."
        ),
        "promedio": (
            f"Calculando métricas agregadas globales: El **presupuesto de subsidio combinado promedio** "
            f"para las comunas y corregimientos analizados se sitúa en **${avg_subsidies:,.2f} COP**."
        ),
        "modelo_ml": (
            "De acuerdo con las ganancias de información matemáticas de nuestro Random Forest Regressor, "
            f"la variable con **mayor peso predictivo** en la ecuación actual es: **{translated_feature}**. "
            "Ella es la encargada de guiar la mayor parte de las divisiones en los árboles de decisión."
        ),
        "desconocido": (
            "Disculpa, no logré procesar esa consulta exacta con el modelo NLP. Intenta preguntándome algo como:\n"
            "- *¿Cuál es el estrato promedio de las comunas?*\n"
            "- *¿Cuál es la comuna con mayor presupuesto?*\n"
            "- *¿Qué variable es la más importante para la IA?*"
        )
    }

    return respuestas[intent_predicho]