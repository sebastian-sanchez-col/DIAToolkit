# chatbot_nlp.py

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

CONFIDENCE_THRESHOLD = 0.35
UNKNOWN_INTENT = "desconocido"

# Spanish training phrases: this is training data for a Spanish-speaking
# citizen assistant, not source code, so it stays in Spanish.
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
    ],
}

# User-facing labels (Spanish). 'total_scholarship_beneficiaries' is not an
# active model feature (not in MODEL_FEATURE_COLUMNS); kept only as a fallback
# translation in case free text ever references it.
FEATURE_TRANSLATION = {
    'health_affiliates_share': 'Densidad Demográfica Vulnerable (Participación Relativa, Régimen Subsidiado)',
    'inclusion_share': 'Vulnerabilidad Prioritaria (Participación Relativa, Inclusión Social)',
    'total_investment': 'Presupuesto de Inversión Territorial Ejecutado',
    'mean_utility_stratum': 'Nivel de Capacidad Socioeconómica Promedio (Estrato Real)',
    'total_scholarship_beneficiaries': 'Acceso a Educación Superior (Becas) — Solo Métrica de Ciudad, No Territorial',
    'anio': 'Año de la Inversión (Tendencia Temporal Multi-Año)',
}


class IntentClassifier:
    """Single responsibility: map raw user text to an intent label."""

    def __init__(self, training_data, confidence_threshold=CONFIDENCE_THRESHOLD):
        self._confidence_threshold = confidence_threshold
        texts, labels = self._flatten(training_data)
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        vectors = self._vectorizer.fit_transform(texts)
        self._model = LogisticRegression(C=1.0)
        self._model.fit(vectors, labels)

    @staticmethod
    def _flatten(training_data):
        texts, labels = [], []
        for intent, phrases in training_data.items():
            for phrase in phrases:
                texts.append(phrase.lower().strip())
                labels.append(intent)
        return texts, labels

    def classify(self, text):
        vector = self._vectorizer.transform([text.lower().strip()])
        probabilities = self._model.predict_proba(vector)[0]
        best_idx = np.argmax(probabilities)
        confidence = probabilities[best_idx]
        if confidence < self._confidence_threshold:
            return UNKNOWN_INTENT
        return self._model.classes_[best_idx]


_classifier = IntentClassifier(TRAINING_DATA)


# ---------------------------------------------------------------------------
# Stat helpers: each computes exactly one derived value from the inputs.
# ---------------------------------------------------------------------------

def _investment_extremes(df_master):
    if df_master.empty:
        return None, None
    sorted_df = df_master.sort_values(by='total_investment', ascending=False)
    return sorted_df.iloc[0], sorted_df.iloc[-1]


def _average_investment(df_master):
    return df_master['total_investment'].mean() if not df_master.empty else 0


def _average_stratum(df_master):
    return df_master['mean_utility_stratum'].mean() if not df_master.empty else 0


def _lowest_stratum_zone(df_master):
    if df_master.empty:
        return "N/A"
    sorted_df = df_master.sort_values(by='mean_utility_stratum', ascending=True)
    return sorted_df.iloc[0]['commune_clean']


def _total_city_subsidies(city_level_metrics):
    return (
        city_level_metrics.get('total_epm_utility_subsidy_medellin', 0)
        + city_level_metrics.get('total_epm_direct_subsidy_medellin', 0)
        + city_level_metrics.get('total_cleaning_subsidy_medellin', 0)
    )


def _period_alignment_caveat(city_level_metrics):
    aligned = city_level_metrics.get('subsidies_periods_aligned')
    if aligned is False:
        return (" ⚠️ *Nota:* estos tres subsidios no están midiendo la misma ventana de tiempo, "
                "así que esta suma es referencial y no debe leerse como un total estrictamente comparable.")
    if aligned is None:
        return (" ⚠️ *Nota:* no fue posible verificar si los tres subsidios corresponden al mismo "
                "periodo, por lo que esta cifra debe tomarse como una aproximación.")
    return ""


def _net_subsidy_caveat(city_level_metrics):
    if not city_level_metrics.get('epm_valor_es_neto_subsidio_menos_contribucion', False):
        return ""
    return (" ⚠️ *Nota:* esta cifra de EPM es un **neto** (subsidios menos contribuciones), "
            "ya que ambos conceptos comparten la misma columna con signo (negativo = subsidio, "
            "positivo = contribución).")


def _dominant_feature_label(ai_insights):
    if not ai_insights:
        return "N/A"
    dominant_feature = max(ai_insights, key=ai_insights.get)
    return FEATURE_TRANSLATION.get(dominant_feature, dominant_feature)


class ResponseContext:
    """Computes, once per request, every value a response builder might need."""

    def __init__(self, df_master, ai_insights, city_level_metrics):
        self.max_investment_row, self.min_investment_row = _investment_extremes(df_master)
        self.average_investment = _average_investment(df_master)
        self.average_stratum = _average_stratum(df_master)
        self.lowest_stratum_zone = _lowest_stratum_zone(df_master)
        self.total_city_subsidies = _total_city_subsidies(city_level_metrics)
        self.period_caveat = _period_alignment_caveat(city_level_metrics)
        self.net_caveat = _net_subsidy_caveat(city_level_metrics)
        self.dominant_feature_label = _dominant_feature_label(ai_insights)


# ---------------------------------------------------------------------------
# Response builders: one function per intent. Adding a new intent means
# adding one function here and one entry in RESPONSE_BUILDERS below — nothing
# else changes (open/closed).
# ---------------------------------------------------------------------------

def _build_greeting_response(context):
    return (
        "¡Hola! Soy tu Asistente de IA para el Reto 7, optimizado con un motor de NLP "
        "estadístico. Puedo ayudarte a analizar la inversión territorial, los subsidios "
        "de la ciudad y el comportamiento de nuestro modelo predictivo. ¿Qué te gustaría "
        "consultar hoy?"
    )


def _build_investment_response(context):
    if context.max_investment_row is None:
        return "Aún no se registran datos territoriales cargados."
    return (
        f"Analizando la matriz territorial, la zona con **mayor inversión real ejecutada** "
        f"es **{context.max_investment_row['commune_clean']}** con un monto estimado de "
        f"${context.max_investment_row['total_investment']:,.2f} COP."
    )


def _build_subsidies_response(context):
    if context.min_investment_row is None:
        return "Aún no se registran datos territoriales cargados."
    return (
        f"Los subsidios (EPM servicios públicos, EPM directos y aseo) están reportados a "
        f"nivel de todo el municipio de Medellín, no por comuna individual, ya que las "
        f"fuentes originales no incluyen esa llave geográfica. El **total combinado de "
        f"subsidios de la ciudad** es de **${context.total_city_subsidies:,.2f} COP**."
        f"{context.period_caveat}{context.net_caveat} "
        f"Adicionalmente, la comuna con **menor inversión territorial** registrada es "
        f"**{context.min_investment_row['commune_clean']}** con "
        f"${context.min_investment_row['total_investment']:,.2f} COP."
    )


def _build_stratum_response(context):
    return (
        f"Métricas de Estratificación Socioeconómica: El **estrato promedio ponderado** global "
        f"de los territorios analizados es **{context.average_stratum:.2f}**. El territorio con el perfil "
        f"socioeconómico más bajo registrado es **{context.lowest_stratum_zone}**."
    )


def _build_average_response(context):
    return (
        f"Calculando métricas agregadas: la **inversión territorial promedio** por comuna/"
        f"corregimiento es de **${context.average_investment:,.2f} COP**. A nivel de ciudad, el subsidio "
        f"combinado total (EPM + aseo) asciende a **${context.total_city_subsidies:,.2f} COP**."
        f"{context.period_caveat}{context.net_caveat}"
    )


def _build_model_response(context):
    return (
        "De acuerdo con las ganancias de información matemáticas de nuestro Random Forest "
        f"Regressor, la variable con **mayor peso predictivo** en la ecuación actual es: "
        f"**{context.dominant_feature_label}**. Ella es la encargada de guiar la mayor parte de las "
        "divisiones en los árboles de decisión."
    )


def _build_unknown_response(context):
    return (
        "Disculpa, no logré procesar esa consulta exacta con el modelo NLP. Intenta preguntándome algo como:\n"
        "- *¿Cuál es el estrato promedio de las comunas?*\n"
        "- *¿Cuál es la comuna con mayor inversión?*\n"
        "- *¿Qué variable es la más importante para la IA?*"
    )


RESPONSE_BUILDERS = {
    "saludo": _build_greeting_response,
    "inversion": _build_investment_response,
    "subsidios": _build_subsidies_response,
    "estrato": _build_stratum_response,
    "promedio": _build_average_response,
    "modelo_ml": _build_model_response,
    UNKNOWN_INTENT: _build_unknown_response,
}


def obtener_respuesta_asistente(user_text, df_master, ai_insights, city_level_metrics):
    """Public entry point. Name kept in Spanish because app.py imports it as-is."""
    if not user_text or pd.isna(user_text):
        return "Por favor, escribe una pregunta para poder ayudarte."

    intent = _classifier.classify(str(user_text))
    context = ResponseContext(df_master, ai_insights, city_level_metrics)
    builder = RESPONSE_BUILDERS.get(intent, _build_unknown_response)
    return builder(context)