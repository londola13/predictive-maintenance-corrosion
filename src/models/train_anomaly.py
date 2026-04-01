"""
train_anomaly.py
----------------
Détecteur d'anomalies process via Isolation Forest.
Détecte les conditions opératoires anormales qui vont
accélérer la corrosion (upsets process).

Contamination = 5% (5% des points considérés anormaux a priori).
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_PATH    = Path("models/isolation_forest.pkl")
SCALER_PATH   = Path("models/scaler_anomaly.pkl")

# Tags DCS utilisés pour la détection d'anomalies
# (conditions process — pas les targets de corrosion)
ANOMALY_FEATURES = [
    "T_mean", "P_mean", "CO2_pct", "BSW_mean",
    "sable_ppm", "inhib_mean", "dP_filtre",
    "velocity_ms", "pCO2_bar", "aggressivity_index",
]

# Seuils d'alerte par tag (hors plage normale → upset)
SEUILS_ALERTES = {
    "T_mean":         (35, 65),
    "P_mean":         (65, 100),
    "CO2_pct":        (0.5, 5.0),
    "BSW_mean":       (0.5, 30),
    "inhib_mean":     (20, 80),
    "dP_filtre":      (0, 4.0),
    "velocity_ms":    (0.3, 3.43),   # V_érosive ≈ 3.43 m/s
    "aggressivity_index": (0, 1.0),
}


def train(df: pd.DataFrame, contamination: float = 0.05) -> tuple:
    """
    Entraîne l'Isolation Forest sur les conditions process normales.

    Args:
        df            : dataset process (features DCS)
        contamination : fraction de points considérés anormaux (5%)

    Returns:
        (model, scaler, metrics_dict)
    """
    feat_cols = [c for c in ANOMALY_FEATURES if c in df.columns]
    df_clean = df[feat_cols].dropna()

    print(f"\n[Anomaly] Entraînement : {len(df_clean)} lignes | "
          f"{len(feat_cols)} features")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_clean)

    model = IsolationForest(
        contamination=contamination,
        n_estimators=200,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Évaluer sur le dataset d'entraînement
    scores   = model.decision_function(X_scaled)
    labels   = model.predict(X_scaled)   # -1 anomalie, +1 normal
    n_anom   = (labels == -1).sum()
    pct_anom = 100 * n_anom / len(labels)

    metrics = {
        "n_anomalies_detectees": int(n_anom),
        "pct_anomalies":         round(pct_anom, 2),
        "score_moyen":           round(scores.mean(), 4),
        "features_utilisees":    feat_cols,
    }

    print(f"  Anomalies détectées : {n_anom} ({pct_anom:.1f}%)")

    # Sauvegarder
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"[Anomaly] Modèle sauvegardé : {MODEL_PATH}")

    return model, scaler, metrics


def predict_anomaly(conditions: pd.DataFrame | dict,
                    model=None, scaler=None) -> dict:
    """
    Détecte si les conditions process actuelles sont anormales.

    Args:
        conditions : DataFrame ou dict avec les tags DCS
        model      : Isolation Forest (chargé si None)
        scaler     : StandardScaler (chargé si None)

    Returns:
        dict avec score, label, alertes par tag
    """
    if model is None:
        if not MODEL_PATH.exists():
            return {"label": "Inconnu", "score": 0, "alertes": []}
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)

    if isinstance(conditions, dict):
        conditions = pd.DataFrame([conditions])

    feat_cols = [c for c in ANOMALY_FEATURES if c in conditions.columns]
    if not feat_cols:
        return {"label": "Inconnu", "score": 0, "alertes": []}

    X = conditions[feat_cols].fillna(conditions[feat_cols].median())
    X_scaled = scaler.transform(X)

    score  = float(model.decision_function(X_scaled)[0])
    label  = model.predict(X_scaled)[0]

    # Alertes tag par tag
    alertes = _detecter_alertes_tags(conditions)

    # Score normalisé 0-100 (100 = très anormal)
    score_normalise = max(0, min(100, int((-score + 0.2) / 0.4 * 100)))

    return {
        "label":           "Anormal" if label == -1 else "Normal",
        "is_anomalie":     label == -1,
        "score_brut":      round(score, 4),
        "score_anomalie":  score_normalise,    # 0=normal, 100=très anormal
        "alertes":         alertes,
        "nb_alertes":      len(alertes),
    }


def surveiller_derive(df_recent: pd.DataFrame, df_reference: pd.DataFrame) -> dict:
    """
    Détecte une dérive des conditions process dans le temps.
    Compare les 30 derniers jours vs la distribution de référence.

    Utilisé sur la Page 6 du dashboard (Monitoring modèle).
    """
    feat_cols = [c for c in ANOMALY_FEATURES
                 if c in df_recent.columns and c in df_reference.columns]

    derive = {}
    for col in feat_cols:
        mu_ref = df_reference[col].mean()
        sigma_ref = df_reference[col].std()
        mu_rec = df_recent[col].mean()

        if sigma_ref > 0:
            z_score = abs(mu_rec - mu_ref) / sigma_ref
            derive[col] = {
                "mu_reference": round(mu_ref, 3),
                "mu_recent":    round(mu_rec, 3),
                "z_score":      round(z_score, 2),
                "derive":       z_score > 2.0,
            }

    dérives_detectées = [k for k, v in derive.items() if v.get("derive")]

    return {
        "derive_detectee": len(dérives_detectées) > 0,
        "tags_en_derive":  dérives_detectées,
        "detail":          derive,
    }


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _detecter_alertes_tags(conditions: pd.DataFrame) -> list:
    """Génère des alertes pour chaque tag hors plage normale."""
    alertes = []
    row = conditions.iloc[0]

    for tag, (lo, hi) in SEUILS_ALERTES.items():
        if tag not in row:
            continue
        val = row[tag]
        if pd.isna(val):
            continue
        if val < lo:
            alertes.append({
                "tag": tag, "valeur": round(float(val), 3),
                "seuil": f"< {lo}", "gravite": "ALARME",
            })
        elif val > hi:
            alertes.append({
                "tag": tag, "valeur": round(float(val), 3),
                "seuil": f"> {hi}", "gravite": "ALARME",
            })

    return alertes
