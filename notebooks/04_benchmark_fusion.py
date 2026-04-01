"""
04_benchmark_fusion.py
----------------------
Benchmark comparatif : prouve que la fusion de sources améliore les prédictions.

3 modèles comparés sur le MÊME test set COTCO :
  M0 — Baseline physique (De Waard seul, pas de ML)
  M1 — XGBoost entraîné sur COTCO synthétique uniquement
  M2 — XGBoost entraîné sur fusion pondérée (toutes sources)

Résultat sauvegardé dans models/benchmark_results.json
→ Affiché dans le dashboard Page 6 (Monitoring Modèle)

Usage :
    python notebooks/04_benchmark_fusion.py
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.data.generate_synthetic_cotco import generer_dataset_cotco
from src.features.compute_features import compute_all_features, get_feature_matrix
from src.etl.merge_all_sources import fusionner_toutes_sources

try:
    import xgboost as xgb
    XGB_OK = True
except ImportError:
    print("[ERREUR] pip install xgboost")
    sys.exit(1)


# ── Paramètres ────────────────────────────────────────────────────────────────

N_TOTAL   = 6000   # points total générés
N_TEST    = 1000   # réservés pour test (toujours COTCO)
N_TRAIN   = N_TOTAL - N_TEST
RANDOM_STATE = 42
TARGET = "CR_mesure"


# ── 1. Générer les données ─────────────────────────────────────────────────────

def generer_toutes_sources():
    """
    Génère les données de chaque source avec des caractéristiques distinctes.
    PHMSA = pipelines US (conditions différentes de Kribi).
    """
    print("\n[1] Génération des données...")

    # Source COTCO (Kribi) — conditions tropicales, pétrole Doba
    df_cotco = generer_dataset_cotco(n_points=N_TOTAL, seed=RANDOM_STATE)
    df_cotco = compute_all_features(df_cotco)
    print(f"  COTCO synthétique : {len(df_cotco)} points | CR moy = {df_cotco[TARGET].mean():.4f}")

    # Source PHMSA — pipelines US : températures plus basses, pressions différentes
    # On simule des conditions différentes pour représenter la diversité
    df_phmsa = _generer_phmsa_like(n_points=2000, seed=RANDOM_STATE + 1)
    df_phmsa = compute_all_features(df_phmsa)
    df_phmsa["source"] = "PHMSA_public"
    df_phmsa["poids"]  = 1.0
    print(f"  PHMSA simulé      : {len(df_phmsa)} points | CR moy = {df_phmsa[TARGET].mean():.4f}")

    # Source De Waard pure (simulation complémentaire, seed différent)
    df_sim = generer_dataset_cotco(n_points=2000, seed=RANDOM_STATE + 2)
    df_sim = compute_all_features(df_sim)
    df_sim["source"] = "simulation_DeWaard"
    df_sim["poids"]  = 0.5
    print(f"  Simulation De Waard : {len(df_sim)} points | CR moy = {df_sim[TARGET].mean():.4f}")

    return df_cotco, df_phmsa, df_sim


def _generer_phmsa_like(n_points: int, seed: int) -> pd.DataFrame:
    """
    Simule des données style PHMSA (pipelines US).
    Conditions différentes de Kribi : températures plus basses, moins de BSW.
    CR calculé avec De Waard adapté + facteurs US.
    """
    rng = np.random.default_rng(seed)

    T       = rng.uniform(10, 50, n_points)       # plus froid qu'en Afrique
    P       = rng.uniform(30, 80, n_points)        # pressions différentes
    CO2_pct = rng.uniform(0.1, 3.0, n_points)
    BSW     = rng.uniform(0.1, 15, n_points)       # moins d'eau qu'à Kribi
    vitesse = rng.uniform(0.5, 8.0, n_points)
    inhib   = np.clip(rng.normal(35, 15, n_points), 0, 100)
    sable   = rng.uniform(0, 100, n_points)
    H2S     = rng.uniform(0, 200, n_points)
    T_aval  = T - rng.uniform(3, 20, n_points)
    dP_filtre = rng.uniform(0, 4, n_points)
    debit_vol = rng.uniform(100, 600, n_points)

    # CR De Waard adapté conditions US
    pCO2 = P * CO2_pct / 100
    T_K  = T + 273.15
    CR_dw = 10 ** (5.8 - 1710 / T_K + 0.67 * np.log10(pCO2.clip(0.001)))

    # Facteurs correctifs US (pipelines mieux maintenus en moyenne)
    f_inhib = 1 - 0.80 * (inhib / 40).clip(0, 1)
    f_field = rng.uniform(0.05, 0.20, n_points)   # mitigation meilleure
    f_BSW   = 1 + 0.15 * (BSW / 15)

    CR_mesure = (CR_dw * f_inhib * f_field * f_BSW
                 * rng.lognormal(0, 0.08, n_points)).clip(0.001, 0.8)

    # RUL
    t_nom = rng.uniform(10, 20, n_points)
    t_min = t_nom * rng.uniform(0.40, 0.55, n_points)
    RL_ans = ((t_nom - t_min) / CR_mesure).clip(0, 50)

    def clf(cr):
        if cr < 0.025: return "Acceptable"
        if cr < 0.050: return "Faible"
        if cr < 0.125: return "Modéré"
        if cr < 0.250: return "Élevé"
        if cr < 0.500: return "Sévère"
        return "Critique"

    return pd.DataFrame({
        "T_mean": T, "T_aval": T_aval, "P_mean": P, "P_aval": P * 0.12,
        "dP_filtre": dP_filtre, "CO2_pct": CO2_pct, "H2S_ppm": H2S,
        "BSW_mean": BSW, "sable_ppm": sable, "debit_vol": debit_vol,
        "debit_masse": debit_vol * 820 / 1000,
        "inhib_mean": inhib, "CP_mV": rng.uniform(-1050, -850, n_points),
        "t_nominal_mm": t_nom, "t_min_mm": t_min,
        "CR_mesure": CR_mesure, "RL_ans": RL_ans,
        "risque_NACE": [clf(r) for r in CR_mesure],
        "source": "PHMSA_public", "poids": 1.0,
    })


# ── 2. Préparer train/test ────────────────────────────────────────────────────

def preparer_splits(df_cotco, df_phmsa, df_sim):
    """
    Test set = toujours COTCO uniquement (derniers N_TEST points).
    Train sets différents selon le modèle testé.
    """
    # Test set : COTCO uniquement (conditions réelles Kribi)
    df_test  = df_cotco.tail(N_TEST).copy()
    df_train_cotco = df_cotco.head(N_TRAIN).copy()

    print(f"\n[2] Splits :")
    print(f"  Test set (COTCO) : {len(df_test)} points")
    print(f"  Train M1 (COTCO seul) : {len(df_train_cotco)} points")

    # Dataset fusion pour M2
    df_train_fusion = fusionner_toutes_sources(
        df_cotco=df_train_cotco,
        df_phmsa=df_phmsa,
        df_simulation=df_sim,
    )
    print(f"  Train M2 (fusion) : {len(df_train_fusion)} points")

    return df_test, df_train_cotco, df_train_fusion


# ── 3. Entraîner et évaluer ───────────────────────────────────────────────────

def entrainer_xgboost(df_train: pd.DataFrame) -> "xgb.XGBRegressor":
    X, feat_names = get_feature_matrix(df_train)
    y = df_train[TARGET].values
    poids = df_train["poids"].values if "poids" in df_train.columns else np.ones(len(df_train))

    model = xgb.XGBRegressor(
        n_estimators=500, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        random_state=RANDOM_STATE, verbosity=0,
    )
    model.fit(X, y, sample_weight=poids)
    return model, feat_names


def evaluer(y_true, y_pred, nom: str) -> dict:
    mae  = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    r2   = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-6))) * 100)

    print(f"\n  [{nom}]")
    print(f"    MAE  : {mae:.4f} mm/an")
    print(f"    RMSE : {rmse:.4f}")
    print(f"    R²   : {r2:.4f}")
    print(f"    MAPE : {mape:.1f}%")

    return {"nom": nom, "mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


# ── 4. Pipeline complet ───────────────────────────────────────────────────────

def run():
    print("\n" + "="*60)
    print("  BENCHMARK — FUSION VS SOURCE UNIQUE")
    print("="*60)

    # Générer données
    df_cotco, df_phmsa, df_sim = generer_toutes_sources()

    # Splits
    df_test, df_train_cotco, df_train_fusion = preparer_splits(df_cotco, df_phmsa, df_sim)

    # Test set features
    X_test, _ = get_feature_matrix(df_test)
    y_test = df_test[TARGET].values

    resultats = []

    # ── M0 : Baseline De Waard (pas de ML) ───────────────────────────────────
    print("\n[3] Évaluation des modèles...")
    if "CR_deWaard" in df_test.columns:
        y_dw = df_test["CR_deWaard"].values
        res_m0 = evaluer(y_test, y_dw, "M0 — De Waard (baseline physique)")
        resultats.append(res_m0)

    # ── M1 : XGBoost COTCO seul ───────────────────────────────────────────────
    print("\n  Entraînement M1 (COTCO seul)...")
    model_m1, _ = entrainer_xgboost(df_train_cotco)
    y_m1 = np.clip(model_m1.predict(X_test), 0.001, 5.0)
    res_m1 = evaluer(y_test, y_m1, "M1 — XGBoost (COTCO seul)")
    resultats.append(res_m1)

    # ── M2 : XGBoost Fusion ───────────────────────────────────────────────────
    print("\n  Entraînement M2 (fusion)...")
    model_m2, _ = entrainer_xgboost(df_train_fusion)
    y_m2 = np.clip(model_m2.predict(X_test), 0.001, 5.0)
    res_m2 = evaluer(y_test, y_m2, "M2 — XGBoost (fusion pondérée)")
    resultats.append(res_m2)

    # ── Rapport final ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  RÉSULTATS BENCHMARK")
    print("="*60)
    print(f"  {'Modèle':<35} {'MAE':>8} {'R²':>8} {'MAPE':>8}")
    print(f"  {'-'*59}")
    for r in resultats:
        print(f"  {r['nom']:<35} {r['mae']:>8.4f} {r['r2']:>8.4f} {r['mape']:>7.1f}%")

    # Calcul amélioration fusion vs source unique
    if len(resultats) >= 3:
        mae_m1 = resultats[1]["mae"]
        mae_m2 = resultats[2]["mae"]
        amelioration = (mae_m1 - mae_m2) / mae_m1 * 100
        print(f"\n  Amélioration Fusion vs COTCO seul : {amelioration:+.1f}% MAE")
        label = "[OK] Fusion justifiee" if amelioration > 0 else "[INFO] Fusion non benefique sur synthetique (attendu)"
        print(f"  {label}")

    # Sauvegarder pour dashboard
    output = {
        "benchmark": resultats,
        "n_test": int(len(df_test)),
        "note": "Test set = COTCO uniquement. Fusion bénéfique si MAE M2 < MAE M1.",
    }
    out_path = ROOT / "models/benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n[Benchmark] Résultats sauvegardés : {out_path}")
    print("[Benchmark] Visible dans le dashboard — Page 6 Monitoring Modèle")

    return output


if __name__ == "__main__":
    run()
