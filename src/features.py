"""
features.py
-----------
Feature engineering pour la maintenance prédictive corrosion.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib

FEATURES = [
    'temperature', 'pression', 'pH', 'vitesse_fluide', 'pco2',
    'teneur_eau', 'concentration_cl', 'age_pipeline',
    'epaisseur_paroi', 'inhibiteur'
]


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des features dérivées physiquement pertinentes."""
    df = df.copy()

    # Ratio épaisseur résiduelle (indicateur d'état du pipeline)
    if 'epaisseur_paroi' in df.columns and 'taux_corrosion' in df.columns:
        df['erosion_rate_ratio'] = df['taux_corrosion'] / df['epaisseur_paroi']

    # Index de sévérité CO2 (pco2 × température)
    df['co2_severity'] = df['pco2'] * df['temperature']

    # Index de sévérité chlorure × eau
    df['cl_water_index'] = df['concentration_cl'] * df['teneur_eau'] / 100

    # Vitesse normalisée par pression
    df['flow_pressure_ratio'] = df['vitesse_fluide'] / (df['pression'] + 1)

    return df


def preprocess(df: pd.DataFrame, target: str, test_size=0.2, save_scaler=True):
    """
    Prépare X_train, X_test, y_train, y_test.
    Normalise les features et encode la cible si classification.
    """
    df = add_engineered_features(df)

    feature_cols = FEATURES + ['co2_severity', 'cl_water_index', 'flow_pressure_ratio']
    feature_cols = [c for c in feature_cols if c in df.columns]

    X = df[feature_cols].copy()
    y = df[target].copy()

    # Encoder si classification
    le = None
    if y.dtype == object:
        le = LabelEncoder()
        y = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    if save_scaler:
        joblib.dump(scaler, f'models/scaler_{target}.pkl')
        if le:
            joblib.dump(le, f'models/encoder_{target}.pkl')

    return X_train_scaled, X_test_scaled, y_train, y_test, feature_cols
