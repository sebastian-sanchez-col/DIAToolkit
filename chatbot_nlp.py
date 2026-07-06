# chatbot_nlp.py
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

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

FEATURE_TRANSLATION = {
    'total_subsidized_health_affiliates': 'Densidad Demográfica Vulnerable (Régimen Subsidiado)',
    'total_disabled_and_inclusion_beneficiaries': 'Vulnerabilidad Prioritaria (Inclusión Social)',
    'total_investment': 'Presupuesto de Inversión Territorial Ejecutado',
    'mean_utility_stratum': 'Nivel de Capacidad Socioeconómica Promedio (Estrato Real)',
    'total_scholarship_beneficiaries': 'Acceso a Educación Superior (Becas)',
    'anio': 'Año de la Inversión (Tendencia Temporal Multi-Año)',
}


def obtener_respuesta_asistente(user_text, df_master, ai_insights, city_level_metrics):
    if not user_text or pd.isna(user_text):
        return "Por favor, escribe una pregunta para poder ayudarte."

    clean_input = str(user_text).lower().strip()
    text_vec = vectorizer.transform([clean_input])

    probabilities = classifier.predict_proba(text_vec)[0]
    max_intent_idx = np.argmax(probabilities)
    confidence = probabilities[max_intent_idx]
    predicted_intent = classifier.classes_[max_intent_idx]

    if confidence < 0.35:
        predicted_intent = "desconocido"

    df_sorted = df_master.sort_values(by='total_investment', ascending=False)
    max_inv_row = df_sorted.iloc[0] if not df_sorted.empty else None
    min_inv_row = df_sorted.iloc[-1] if not df_sorted.empty else None
    avg_investment = df_master['total_investment'].mean() if not df_master.empty else 0

    avg_stratum = df_master['mean_utility_stratum'].mean() if not df_master.empty else 0
    df_stratum_sorted = df_master.sort_values(by='mean_utility_stratum', ascending=True)
    lowest_stratum_zone = df_stratum_sorted.iloc[0]['commune_clean'] if not df_stratum_sorted.empty else "N/A"

    total_subsidies_city = (
        city_level_metrics.get('total_epm_utility_subsidy_medellin', 0)
        + city_level_metrics.get('total_epm_direct_subsidy_medellin', 0)
        + city_level_metrics.get('total_cleaning_subsidy_medellin', 0)
    )

    if ai_insights:
        dominant_feature = max(ai_insights, key=ai_insights.get)
    else:
        dominant_feature = None
    translated_feature = FEATURE_TRANSLATION.get(dominant_feature, dominant_feature or "N/A")

    responses = {
        "saludo": (
            "¡Hola! Soy tu Asistente de IA para el Reto 7, optimizado con un motor de NLP "
            "estadístico. Puedo ayudarte a analizar la inversión territorial, los subsidios "
            "de la ciudad y el comportamiento de nuestro modelo predictivo. ¿Qué te gustaría "
            "consultar hoy?"
        ),
        "inversion": (
            f"Analizando la matriz territorial, la zona con **mayor inversión real ejecutada** "
            f"es **{max_inv_row['commune_clean']}** con un monto estimado de "
            f"${max_inv_row['total_investment']:,.2f} COP."
            if max_inv_row is not None else "Aún no se registran datos territoriales cargados."
        ),
        "subsidios": (
            f"Los subsidios (EPM servicios públicos, EPM directos y aseo) están reportados a "
            f"nivel de todo el municipio de Medellín, no por comuna individual, ya que las "
            f"fuentes originales no incluyen esa llave geográfica. El **total combinado de "
            f"subsidios de la ciudad** es de **${total_subsidies_city:,.2f} COP**. "
            f"Adicionalmente, la comuna con **menor inversión territorial** registrada es "
            f"**{min_inv_row['commune_clean']}** con ${min_inv_row['total_investment']:,.2f} COP."
            if min_inv_row is not None else "Aún no se registran datos territoriales cargados."
        ),
        "estrato": (
            f"Métricas de Estratificación Socioeconómica: El **estrato promedio ponderado** global "
            f"de los territorios analizados es **{avg_stratum:.2f}**. El territorio con el perfil "
            f"socioeconómico más bajo registrado es **{lowest_stratum_zone}**."
        ),
        "promedio": (
            f"Calculando métricas agregadas: la **inversión territorial promedio** por comuna/"
            f"corregimiento es de **${avg_investment:,.2f} COP**. A nivel de ciudad, el subsidio "
            f"combinado total (EPM + aseo) asciende a **${total_subsidies_city:,.2f} COP**."
        ),
        "modelo_ml": (
            "De acuerdo con las ganancias de información matemáticas de nuestro Random Forest "
            f"Regressor, la variable con **mayor peso predictivo** en la ecuación actual es: "
            f"**{translated_feature}**. Ella es la encargada de guiar la mayor parte de las "
            "divisiones en los árboles de decisión."
        ),
        "desconocido": (
            "Disculpa, no logré procesar esa consulta exacta con el modelo NLP. Intenta preguntándome algo como:\n"
            "- *¿Cuál es el estrato promedio de las comunas?*\n"
            "- *¿Cuál es la comuna con mayor inversión?*\n"
            "- *¿Qué variable es la más importante para la IA?*"
        )
    }

    return responses[predicted_intent]