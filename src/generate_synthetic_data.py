import numpy as np
import pandas as pd

np.random.seed(42)
N = 5000  # nombre d'échantillons

# Variables physiques pipelines pétroliers
temperature      = np.random.uniform(20, 120, N)      # °C
pression         = np.random.uniform(10, 150, N)      # bar
pH               = np.random.uniform(4.5, 8.5, N)     # pH
vitesse_fluide   = np.random.uniform(0.5, 10, N)      # m/s
pco2             = np.random.uniform(0.1, 10, N)      # bar (pression partielle CO2)
teneur_eau       = np.random.uniform(0, 100, N)       # % water cut
concentration_cl = np.random.uniform(0, 50000, N)    # mg/L chlorures
age_pipeline     = np.random.uniform(0, 30, N)        # années
epaisseur_paroi  = np.random.uniform(6, 25, N)        # mm
inhibiteur       = np.random.randint(0, 2, N)         # 0=sans, 1=avec inhibiteur

# Modèle de de Waard-Milliams (corrosion CO2)
# Taux de corrosion de base (mm/an)
taux_corrosion = (
    0.0315
    * (10 ** (0.67 * np.log10(pco2)))
    * (10 ** (-1710 / (temperature + 273.15) + 5.37))
    * (vitesse_fluide ** 0.146)
    * (1 - 0.7 * inhibiteur)
    + 0.002 * concentration_cl / 10000
    + 0.001 * teneur_eau / 100
    + np.random.normal(0, 0.05, N)  # bruit réaliste
)
taux_corrosion = np.clip(taux_corrosion, 0.01, 5.0)  # mm/an réalistes

# RUL — Remaining Useful Life (années avant perforation)
epaisseur_minimale = 3.0  # mm (seuil sécurité API 579)
rul = (epaisseur_paroi - epaisseur_minimale) / taux_corrosion
rul = np.clip(rul, 0, 50)

# Classification risque
def classify_risk(rate):
    if rate < 0.1:   return 'Faible'
    elif rate < 0.5: return 'Moyen'
    else:            return 'Élevé'

risque = [classify_risk(r) for r in taux_corrosion]

df = pd.DataFrame({
    'temperature': temperature,
    'pression': pression,
    'pH': pH,
    'vitesse_fluide': vitesse_fluide,
    'pco2': pco2,
    'teneur_eau': teneur_eau,
    'concentration_cl': concentration_cl,
    'age_pipeline': age_pipeline,
    'epaisseur_paroi': epaisseur_paroi,
    'inhibiteur': inhibiteur,
    'taux_corrosion': taux_corrosion,
    'rul': rul,
    'risque': risque
})

df.to_csv('data/raw/synthetic_corrosion.csv', index=False)
print(f"Dataset généré : {df.shape}")
print(df.describe())
print(df['risque'].value_counts())
