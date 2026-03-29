"""
train.py
--------
Entraîne les 3 modèles :
  1. Régression  → taux de corrosion (mm/an)
  2. Classification → risque (Faible / Moyen / Élevé)
  3. RUL         → Remaining Useful Life (années)
"""

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                             r2_score, classification_report)
from xgboost import XGBRegressor, XGBClassifier

from data_loader import load_synthetic
from features import preprocess


def train_regression(df):
    print("\n=== Modèle 1 : Régression taux de corrosion ===")
    X_train, X_test, y_train, y_test, cols = preprocess(df, 'taux_corrosion')

    model = XGBRegressor(n_estimators=300, learning_rate=0.05,
                         max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(f"MAE  : {mean_absolute_error(y_test, preds):.4f} mm/an")
    print(f"RMSE : {np.sqrt(mean_squared_error(y_test, preds)):.4f}")
    print(f"R²   : {r2_score(y_test, preds):.4f}")

    joblib.dump(model, 'models/model_regression.pkl')
    print("Modèle sauvegardé → models/model_regression.pkl")
    return model


def train_classification(df):
    print("\n=== Modèle 2 : Classification risque ===")
    X_train, X_test, y_train, y_test, cols = preprocess(df, 'risque')

    model = RandomForestClassifier(n_estimators=200, max_depth=8,
                                   random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds,
                                target_names=['Élevé', 'Faible', 'Moyen']))

    joblib.dump(model, 'models/model_classification.pkl')
    print("Modèle sauvegardé → models/model_classification.pkl")
    return model


def train_rul(df):
    print("\n=== Modèle 3 : RUL (Remaining Useful Life) ===")
    X_train, X_test, y_train, y_test, cols = preprocess(df, 'rul')

    model = XGBRegressor(n_estimators=300, learning_rate=0.05,
                         max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(f"MAE  : {mean_absolute_error(y_test, preds):.4f} ans")
    print(f"RMSE : {np.sqrt(mean_squared_error(y_test, preds)):.4f}")
    print(f"R²   : {r2_score(y_test, preds):.4f}")

    joblib.dump(model, 'models/model_rul.pkl')
    print("Modèle sauvegardé → models/model_rul.pkl")
    return model


if __name__ == '__main__':
    df = load_synthetic()
    train_regression(df)
    train_classification(df)
    train_rul(df)
    print("\n✅ Entraînement terminé. Modèles dans /models/")
