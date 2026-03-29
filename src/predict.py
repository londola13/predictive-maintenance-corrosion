"""
predict.py
----------
Charge les modèles entraînés et prédit sur de nouvelles données.
Utilisé par le dashboard Streamlit.
"""

import joblib
import numpy as np
import pandas as pd
from features import add_engineered_features, FEATURES


def load_models():
    reg   = joblib.load('models/model_regression.pkl')
    clf   = joblib.load('models/model_classification.pkl')
    rul   = joblib.load('models/model_rul.pkl')
    scaler_reg = joblib.load('models/scaler_taux_corrosion.pkl')
    scaler_clf = joblib.load('models/scaler_risque.pkl')
    scaler_rul = joblib.load('models/scaler_rul.pkl')
    encoder    = joblib.load('models/encoder_risque.pkl')
    return reg, clf, rul, scaler_reg, scaler_clf, scaler_rul, encoder


def predict_single(input_dict: dict) -> dict:
    """
    Prédit taux de corrosion, risque et RUL pour un jeu de paramètres.
    input_dict : {temperature, pression, pH, vitesse_fluide, pco2,
                  teneur_eau, concentration_cl, age_pipeline,
                  epaisseur_paroi, inhibiteur}
    """
    reg, clf, rul_model, scaler_reg, scaler_clf, scaler_rul, encoder = load_models()

    df = pd.DataFrame([input_dict])
    df = add_engineered_features(df)

    feature_cols = FEATURES + ['co2_severity', 'cl_water_index', 'flow_pressure_ratio']
    feature_cols = [c for c in feature_cols if c in df.columns]
    X = df[feature_cols].values

    taux  = reg.predict(scaler_reg.transform(X))[0]
    risk_encoded = clf.predict(scaler_clf.transform(X))[0]
    risk  = encoder.inverse_transform([risk_encoded])[0]
    rul_v = rul_model.predict(scaler_rul.transform(X))[0]

    return {
        'taux_corrosion': round(float(taux), 4),
        'risque': risk,
        'rul': round(float(rul_v), 2)
    }
