#!/usr/bin/env python

# make sure to install these packages before running:
# pip install pandas
# pip install sodapy

import pandas as pd
from sodapy import Socrata

# Unauthenticated client only works with public data sets. Note 'None'
# in place of application token, and no username or password:
client = Socrata("www.datos.gov.co", None)

# Example authenticated client (needed for non-public datasets):
# client = Socrata(www.datos.gov.co,
#                  MyAppToken,
#                  username="user@example.com",
#                  password="AFakePassword")

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
# Dataset: Beneficiaros de becas y creditos de programas de acceso a la educación superior de Antioquia
results_scholarship = client.get("ya7f-466y", limit=2000)
# Dataset: Subsidios y Contribuciones de Servicios Públicos Domiciliarios – EPM
results_utility_subsidy = client.get("av6t-m6ju", limit=2000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results_scholarship)
