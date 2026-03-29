"""
data_loader.py
--------------
Chargeur de données générique.
Supporte : données synthétiques, PHMSA, NASA CMAPSS, et données entreprise (plug-and-play).
"""

import pandas as pd
import os

FEATURES = [
    'temperature', 'pression', 'pH', 'vitesse_fluide', 'pco2',
    'teneur_eau', 'concentration_cl', 'age_pipeline',
    'epaisseur_paroi', 'inhibiteur'
]

TARGET_REGRESSION   = 'taux_corrosion'
TARGET_RUL          = 'rul'
TARGET_CLASSIFICATION = 'risque'


def load_synthetic(path='data/raw/synthetic_corrosion.csv') -> pd.DataFrame:
    """Charge les données synthétiques générées par generate_synthetic_data.py"""
    df = pd.read_csv(path)
    print(f"[synthetic] Chargé : {df.shape} | colonnes : {list(df.columns)}")
    return df


def load_enterprise(path='data/enterprise/') -> pd.DataFrame:
    """
    Charge les données entreprise depuis le dossier data/enterprise/.
    Supporte : CSV, Excel.
    Les colonnes doivent correspondre aux FEATURES définis ci-dessus.
    Si les noms diffèrent, utiliser le paramètre column_mapping.
    """
    files = [f for f in os.listdir(path) if f.endswith(('.csv', '.xlsx', '.xls'))]
    if not files:
        raise FileNotFoundError(f"Aucun fichier trouvé dans {path}")

    dfs = []
    for f in files:
        filepath = os.path.join(path, f)
        if f.endswith('.csv'):
            dfs.append(pd.read_csv(filepath))
        else:
            dfs.append(pd.read_excel(filepath))
        print(f"[enterprise] Chargé : {f}")

    df = pd.concat(dfs, ignore_index=True)
    print(f"[enterprise] Total : {df.shape}")
    return df


def validate_columns(df: pd.DataFrame, required: list = FEATURES) -> bool:
    """Vérifie que toutes les colonnes requises sont présentes."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[WARN] Colonnes manquantes : {missing}")
        return False
    return True
