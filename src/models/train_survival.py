"""
train_survival.py
-----------------
Modèle de survie Weibull AFT (Accelerated Failure Time).
Prédit la durée de vie résiduelle (Remaining Useful Life).

Bibliothèque : lifelines (KaplanMeierFitter + WeibullAFTFitter)
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

try:
    from lifelines import WeibullAFTFitter, KaplanMeierFitter
    LIFELINES_OK = True
except ImportError:
    LIFELINES_OK = False
    print("[WARN] lifelines non installé — pip install lifelines")

MODEL_PATH = Path("models/survival_model.pkl")

# Features utilisées pour le modèle de survie
SURVIVAL_FEATURES = [
    "CR_mesure",       # taux de corrosion (principal driver)
    "T_mean",          # température
    "pCO2_bar",        # agressivité CO2
    "BSW_mean",        # teneur en eau
    "inhibitor_efficiency",  # protection chimique
    "aggressivity_index",    # indice composite
]


def train(df: pd.DataFrame) -> tuple:
    """
    Entraîne le modèle Weibull AFT sur le dataset hybride.

    Args:
        df : dataset avec colonnes CR_mesure, RL_ans, features

    Returns:
        (model, metrics_dict)
    """
    if not LIFELINES_OK:
        raise ImportError("lifelines requis : pip install lifelines")

    # Préparer les données
    df_clean = df.dropna(subset=["RL_ans", "CR_mesure"]).copy()
    df_clean = df_clean[df_clean["CR_mesure"] > 0]
    df_clean = df_clean[df_clean["RL_ans"] > 0]

    # Colonne "event" : RL <= 0 signifie "défaillance atteinte"
    df_clean["event"] = (df_clean["RL_ans"] < 2).astype(int)

    print(f"\n[Survie] Entraînement : {len(df_clean)} lignes")
    print(f"  RL médiane : {df_clean['RL_ans'].median():.1f} ans")
    print(f"  Défaillances dans dataset : {df_clean['event'].sum()}")

    # Sélectionner les features disponibles
    feat_cols = [c for c in SURVIVAL_FEATURES if c in df_clean.columns]
    df_model = df_clean[feat_cols + ["RL_ans", "event"]].dropna()

    # Entraînement WeibullAFT
    model = WeibullAFTFitter(penalizer=0.01)
    model.fit(
        df_model,
        duration_col="RL_ans",
        event_col="event",
        ancillary=True,
    )

    print("\n[Survie] Résumé du modèle :")
    print(model.summary[["coef", "exp(coef)", "p"]].to_string())

    # Métriques
    metrics = {
        "concordance_index": model.concordance_index_,
        "n_observations":    len(df_model),
        "features_used":     feat_cols,
    }

    print(f"\n  Concordance Index : {metrics['concordance_index']:.4f} (objectif > 0.7)")

    # Sauvegarder
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"[Survie] Modèle sauvegardé : {MODEL_PATH}")

    return model, metrics


def predict_rl(conditions: dict, model=None) -> dict:
    """
    Prédit la durée de vie résiduelle pour un CML.

    Args:
        conditions : dict avec les features du CML
        model      : modèle WeibullAFT (chargé si None)

    Returns:
        dict avec median_rl, rl_10pct, rl_90pct (IC 80%)
    """
    if model is None:
        if not MODEL_PATH.exists():
            return _fallback_physique(conditions)
        model = joblib.load(MODEL_PATH)

    df_input = pd.DataFrame([conditions])
    feat_cols = [c for c in SURVIVAL_FEATURES if c in df_input.columns]

    if not feat_cols:
        return _fallback_physique(conditions)

    try:
        # Prédire la médiane de survie
        median_rl = model.predict_median(df_input[feat_cols])
        median_rl = float(np.clip(median_rl.values[0], 0, 50))

        # Intervalles de confiance à 80%
        sf = model.predict_survival_function(df_input[feat_cols])
        times = sf.index.values
        probs = sf.values[:, 0]

        rl_10 = _temps_pour_prob(times, probs, 0.9)  # 10% survivants → P(T > t) = 0.9
        rl_90 = _temps_pour_prob(times, probs, 0.1)  # 90% survivants

        return {
            "median_rl":  round(median_rl, 1),
            "rl_pessimiste": round(float(rl_10), 1),
            "rl_optimiste":  round(float(rl_90), 1),
            "methode": "WeibullAFT",
        }
    except Exception as e:
        print(f"[WARN] Prédiction survie : {e}")
        return _fallback_physique(conditions)


def kaplan_meier_par_risque(df: pd.DataFrame) -> dict:
    """
    Calcule les courbes de survie Kaplan-Meier par niveau de risque.
    Utile pour la page RBI du dashboard.
    """
    if not LIFELINES_OK:
        return {}

    resultats = {}
    niveaux_risque = df.get("risque_NACE", df.get("risque_init", pd.Series())).unique()

    for niveau in niveaux_risque:
        if pd.isna(niveau):
            continue
        sous_df = df[df.get("risque_NACE", df.get("risque_init")) == niveau]
        if len(sous_df) < 5:
            continue
        sous_df = sous_df.copy()
        sous_df["event"] = (sous_df["RL_ans"] < 2).astype(int)

        kmf = KaplanMeierFitter()
        kmf.fit(sous_df["RL_ans"], event_observed=sous_df["event"], label=niveau)

        resultats[niveau] = {
            "timeline":   kmf.survival_function_.index.tolist(),
            "survival":   kmf.survival_function_["KM_estimate"].tolist(),
            "median_rl":  float(kmf.median_survival_time_),
        }

    return resultats


def _temps_pour_prob(times, probs, target_prob) -> float:
    """Interpolation : trouve le temps pour lequel P(survie) = target_prob."""
    try:
        idx = np.searchsorted(-probs, -target_prob)
        return float(times[min(idx, len(times) - 1)])
    except Exception:
        return 0.0


def _fallback_physique(conditions: dict) -> dict:
    """Calcul RL par division simple si le modèle n'est pas disponible."""
    t_mm    = conditions.get("t_mm", 15.9)
    t_min   = conditions.get("t_min_mm", 8.8)
    cr      = conditions.get("CR_mesure", conditions.get("CR_deWaard", 0.1))
    if cr > 0:
        rl = (t_mm - t_min) / cr
    else:
        rl = 50.0
    return {
        "median_rl": round(min(rl, 50), 1),
        "rl_pessimiste": round(min(rl * 0.7, 50), 1),
        "rl_optimiste":  round(min(rl * 1.3, 50), 1),
        "methode": "physique_fallback",
    }
