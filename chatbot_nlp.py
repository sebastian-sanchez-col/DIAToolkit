# chatbot_nlp.py

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from data_processor import FEATURE_TRANSLATION

CONFIDENCE_THRESHOLD = 0.35
UNKNOWN_INTENT = "desconocido"

TRAINING_DATA = {
    "saludo": [
        "hola", "buenos dias", "buenas tardes", "hey", "saludos",
        "que tal", "hola chatbot", "inicio", "comenzar", "hi", "hello"
    ],
    "inversion": [
        "cuanta plata se invirtio", "presupuesto de comunas", "inversion publica",
        "gasto", "dinero", "ejecucion presupuestal", "recursos invertidos",
        "cuanto dinero recibio la comuna", "inversion por territorio", "comuna",
        "territorio", "mayor", "maximo", "menor", "minimo",
        "mayor inversion", "menor inversion"
    ],
    "subsidios": [
        "que subsidios hay", "ayuda de servicios publicos", "aseo y energia",
        "quien recibe subsidio", "fondos globales", "total combinado",
        "ayudas economicas", "subsidio de epm", "subsidio de aseo",
        "corregimiento"
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
    "becas": [
        "cuantos beneficiarios de becas hay", "becas y creditos", "acceso a educacion superior",
        "creditos educativos", "cuantas becas se entregaron", "beca", "educacion superior medellin",
        "programas de becas", "estudiantes beneficiados"
    ]
}

DATA_GOVERNANCE = {
    "inversion": {
        "fuente": "Inversión por comuna y corregimiento Medellín 2015-2018 (datos.gov.co)",
        "fecha_actualizacion": "última carga disponible: 2018",
        "politica_de_uso": "Datos abiertos, uso libre citando la fuente",
    },
    "subsidios": {
        "fuente": "Subsidios y Contribuciones EPM / Aseo (datos.gov.co)",
        "fecha_actualizacion": "ver periodo reportado en cada respuesta",
        "politica_de_uso": "Datos abiertos, uso libre citando la fuente",
    },
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


def _governance_footer(intent):
    meta = DATA_GOVERNANCE.get(intent)
    if not meta:
        return ""
    return (f"\n\n📎 *Fuente: {meta['fuente']} | {meta['fecha_actualizacion']} | "
            f"{meta['politica_de_uso']}*")


def classify_with_confidence(self, text):
    """Devuelve (intent, confidence) en vez de solo el intent, para poder
    exponerle la incertidumbre al usuario en vez de ocultarla."""
    vector = self._vectorizer.transform([text.lower().strip()])
    probabilities = self._model.predict_proba(vector)[0]
    best_idx = np.argmax(probabilities)
    confidence = float(probabilities[best_idx])
    intent = self._model.classes_[best_idx] if confidence >= self._confidence_threshold else UNKNOWN_INTENT
    return intent, confidence


def get_assistant_response(user_text, df_master, ai_insights, city_level_metrics):
    if not user_text or pd.isna(user_text):
        return "Por favor, escribe una pregunta para poder ayudarte."

    intent, confidence = _classifier.classify_with_confidence(str(user_text))
    context = ResponseContext(df_master, ai_insights, city_level_metrics)
    builder = RESPONSE_BUILDERS.get(intent, _build_unknown_response)
    answer = builder(context)

    if intent != UNKNOWN_INTENT and confidence < 0.55:
        answer += ("\n\n⚠️ *No tengo alta certeza de haber entendido tu pregunta "
                   f"(confianza: {confidence*100:.0f}%). Si la respuesta no es lo que "
                   f"buscabas, intenta reformularla.*")

    answer += _governance_footer(intent)
    return answer

def _investment_extremes(df_master):
    if df_master.empty:
        return None, None
    sorted_df = df_master.sort_values(by='avg_annual_investment', ascending=False)
    return sorted_df.iloc[0], sorted_df.iloc[-1]


def _average_investment(df_master):
    return df_master['avg_annual_investment'].mean() if not df_master.empty else 0


def _average_stratum(df_master):
    return df_master['mean_utility_stratum'].mean() if not df_master.empty else 0


def _lowest_stratum_zone(df_master):
    if df_master.empty:
        return "N/A"
    sorted_df = df_master.sort_values(by='mean_utility_stratum', ascending=True)
    return sorted_df.iloc[0]['commune_clean']


def _total_city_subsidies(city_level_metrics):
    total = (city_level_metrics.get('total_epm_utility_subsidy_medellin', 0)
             + city_level_metrics.get('total_cleaning_subsidy_medellin', 0))
    if not city_level_metrics.get('epm_subsidies_confirmed_duplicate_source', False):
        total += city_level_metrics.get('total_epm_direct_subsidy_medellin', 0)
    return total


def _city_subsidy_breakdown(city_level_metrics):
    items = [
        ("EPM servicios públicos", city_level_metrics.get('total_epm_utility_subsidy_medellin', 0),
         city_level_metrics.get('utility_subsidy_period_end')),
    ]
    if not city_level_metrics.get('epm_subsidies_confirmed_duplicate_source', False):
        items.append(("EPM directos", city_level_metrics.get('total_epm_direct_subsidy_medellin', 0),
                      city_level_metrics.get('epm_direct_subsidy_period_end')))
    items.append(("Aseo", city_level_metrics.get('total_cleaning_subsidy_medellin', 0),
                 city_level_metrics.get('cleaning_subsidy_period_end')))
    return items


def _format_period(period_end):
    if period_end is None or pd.isna(period_end):
        return "fecha desconocida"
    return period_end.strftime('%Y-%m')


def _net_subsidy_caveat(city_level_metrics):
    if not city_level_metrics.get('epm_valor_es_neto_subsidio_menos_contribucion', False):
        return ""
    return (" ⚠️ *Nota:* la cifra de EPM es un **neto** (subsidios menos contribuciones), "
            "ya que ambos conceptos comparten la misma columna con signo (negativo = subsidio, "
            "positivo = contribución).")


def _dominant_feature_label(ai_insights):
    if not ai_insights:
        return "N/A"
    dominant_feature = max(ai_insights, key=ai_insights.get)
    return FEATURE_TRANSLATION.get(dominant_feature, dominant_feature)


def _render_subsidies_amount(context):
    """Renders the city-level subsidy figure(s). Never sums mismatched-period
    sources into a single number; if periods don't align, each source is
    shown separately with its own period, and a suspected-duplicate warning
    is surfaced if applicable."""
    if context.periods_aligned:
        return f"el **subsidio combinado total** de la ciudad es de **${context.total_city_subsidies:,.2f} COP**."

    lines = [
        f"**{label}**: ${amount:,.2f} COP (periodo más reciente: {_format_period(period_end)})"
        for label, amount, period_end in context.subsidy_breakdown
    ]
    duplicate_note = (
        " *Nota:* 'EPM directos' no se incluye por separado porque es la misma fuente que 'EPM "
        "servicios públicos' republicada bajo otra ficha de datos.gov.co (confirmado comparando "
        "ambos datasets valor por valor)."
        if context.confirmed_duplicate_source else ""
    )
    return (
        "estos tres subsidios NO corresponden al mismo periodo, así que no se presentan como un "
        "único total combinado, sino por separado:\n"
        + "\n".join(f"- {line}" for line in lines)
        + f"\n{duplicate_note}"
    )


class ResponseContext:
    """Computes, once per request, every value a response builder might need."""

    def __init__(self, df_master, ai_insights, city_level_metrics):
        self.max_investment_row, self.min_investment_row = _investment_extremes(df_master)
        self.average_investment = _average_investment(df_master)
        self.average_stratum = _average_stratum(df_master)
        self.lowest_stratum_zone = _lowest_stratum_zone(df_master)
        self.total_city_subsidies = _total_city_subsidies(city_level_metrics)
        self.periods_aligned = city_level_metrics.get('subsidies_periods_aligned')
        self.subsidy_breakdown = _city_subsidy_breakdown(city_level_metrics)
        self.confirmed_duplicate_source = city_level_metrics.get('epm_subsidies_confirmed_duplicate_source', False)
        self.net_caveat = _net_subsidy_caveat(city_level_metrics)
        self.dominant_feature_label = _dominant_feature_label(ai_insights)
        self.total_scholarship_beneficiaries = city_level_metrics.get('total_scholarship_beneficiaries_medellin', 0)


def _build_greeting_response(context):
    return (
        "¡Hola! Soy tu Asistente de IA para el Reto 7, optimizado con un motor de NLP "
        "estadístico. Puedo ayudarte a analizar la inversión territorial, los subsidios "
        "de la ciudad y el comportamiento de nuestro modelo predictivo. ¿Qué te gustaría "
        "consultar hoy?"
    )


def _build_scholarship_response(context):
    return (
        f"En becas y créditos para educación superior, Medellín registra **"
        f"{context.total_scholarship_beneficiaries} beneficiarios** en la fuente consultada "
        f"(dataset departamental de Antioquia, filtrado por municipio de residencia). "
        f"⚠️ *Nota:* esta cifra es una **métrica agregada de ciudad**, no se desagrega por comuna: "
        f"tras el filtro geográfico la muestra quedó muy pequeña frente al total original, así que "
        f"no forma parte del modelo predictivo ni del análisis territorial por comuna."
    )


def _build_investment_response(context):
    if context.max_investment_row is None:
        return "Aún no se registran datos territoriales cargados."
    return (
        f"Analizando la matriz territorial: la zona con **mayor inversión promedio anual** "
        f"es **{context.max_investment_row['commune_clean']}**, con un monto promedio de "
        f"${context.max_investment_row['avg_annual_investment']:,.2f} COP por año. En el otro extremo, "
        f"la zona con **menor inversión promedio anual** es **{context.min_investment_row['commune_clean']}**, "
        f"con ${context.min_investment_row['avg_annual_investment']:,.2f} COP por año "
        f"(cifras promedio 2015-2018, no un total acumulado)."
    )


def _build_subsidies_response(context):
    return (
        f"Los subsidios (EPM servicios públicos, EPM directos y aseo) están reportados a "
        f"nivel de todo el municipio de Medellín, no por comuna individual, ya que las "
        f"fuentes originales no incluyen esa llave geográfica. {_render_subsidies_amount(context)}"
        f"{context.net_caveat}"
    )


def _build_stratum_response(context):
    return (
        f"Métricas de Estratificación Socioeconómica: El **estrato promedio ponderado** global "
        f"de los territorios analizados es **{context.average_stratum:.2f}**. El territorio con el perfil "
        f"socioeconómico más bajo registrado es **{context.lowest_stratum_zone}**."
    )


def _build_average_response(context):
    return (
        f"Calculando métricas agregadas: la **inversión promedio anual** por comuna/"
        f"corregimiento (promedio 2015-2018) es de **${context.average_investment:,.2f} COP**. A nivel de ciudad, "
        f"{_render_subsidies_amount(context)}{context.net_caveat}"
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
    "becas": _build_scholarship_response,
    UNKNOWN_INTENT: _build_unknown_response,
}


def get_assistant_response(user_text, df_master, ai_insights, city_level_metrics):
    if not user_text or pd.isna(user_text):
        return "Por favor, escribe una pregunta para poder ayudarte."

    intent, confidence = _classifier.classify_with_confidence(str(user_text))
    context = ResponseContext(df_master, ai_insights, city_level_metrics)
    builder = RESPONSE_BUILDERS.get(intent, _build_unknown_response)
    answer = builder(context)

    if intent != UNKNOWN_INTENT and confidence < 0.55:
        answer += ("\n\n⚠️ *No tengo alta certeza de haber entendido tu pregunta "
                   f"(confianza: {confidence*100:.0f}%). Si la respuesta no es lo que "
                   f"buscabas, intenta reformularla.*")

    answer += _governance_footer(intent)
    return answer