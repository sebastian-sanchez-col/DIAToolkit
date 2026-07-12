# datos_gov_api.py

import pandas as pd
import requests
import os

SOCRATA_BASE_URL = "https://www.datos.gov.co/resource/{dataset_id}.json"
DEFAULT_PAGE_SIZE = 5000
REQUEST_TIMEOUT_SECONDS = 15

SOCRATA_APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN")

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DIAToolkit/1.0; +https://github.com/sebastian-sanchez-col/DIAToolkit)",
}

if SOCRATA_APP_TOKEN:
    REQUEST_HEADERS["X-App-Token"] = SOCRATA_APP_TOKEN

def fetch_dataset_from_api(dataset_id, params=None, max_records=50_000):
    url = SOCRATA_BASE_URL.format(dataset_id=dataset_id)
    all_rows = []
    offset = 0

    while offset < max_records:
        query_params = {"$limit": DEFAULT_PAGE_SIZE, "$offset": offset, **(params or {})}
        try:
            response = requests.get(url, params=query_params,
                                     headers=REQUEST_HEADERS,
                                     timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"[ALERTA API] Falló la consulta a {url} (offset={offset}): {error}. "
                  f"Se usará el respaldo local en CSV si está disponible.")
            break

        page = response.json()
        if not page:
            break
        all_rows.extend(page)
        offset += DEFAULT_PAGE_SIZE

    if not all_rows:
        return None

    print(f"[API] {dataset_id}: {len(all_rows)} filas obtenidas vía API REST (JSON, "
          f"paginado $limit/$offset).")
    return pd.DataFrame(all_rows)


def load_investment_year_with_api_fallback(dataset_id, local_csv_path, year):
    """Tries the API first (most up-to-date data); if it fails, uses the local CSV."""
    df = fetch_dataset_from_api(dataset_id)
    if df is not None:
        return df, "api"
    try:
        return pd.read_csv(local_csv_path), "csv_local_fallback"
    except FileNotFoundError:
        return None, "no_disponible"
