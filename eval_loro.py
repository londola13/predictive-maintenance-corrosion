# -*- coding: utf-8 -*-
"""Evaluation leave-one-run-out sur les runs disponibles (cible : CR taux de corrosion)."""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd, numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score

from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run, FEATURES, PARAMS_XGB

RUNS = {
    "Run1  (brut)": "d6e31719-c3fb-4797-aa0b-65c4e605002a",
    "Run11 (brut)": "72d0f7b7-e1ef-40b0-8416-851873c72440",
    "Run12 (brut)": "f5852fd4-8c3f-474e-9c20-a1ac129e018c",
}
# Fraction volumique d'acide par run
CONCENTRATION = {
    "Run1  (brut)": 1.00,
    "Run11 (brut)": 1.00,
    "Run12 (brut)": 1.00,
}

# Features "propres" : on retire celles qui sont quasi la cible (fuite) -> dR/dt, vitesse_CR
FEATURES_PROPRES = ["rx_corr", "temp_lisse", "temp_moy_6h", "temps_immersion_h",
                    "delta_R_absolu", "section_perdue_pct"]

print("=== Chargement et traitement des runs ===")
dfs = {}
for name, rid in RUNS.items():
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name)
    df["run"] = name
    df["concentration"] = CONCENTRATION[name]
    dfs[name] = df
    print(f"  {name}: {len(df)} points traites")

def loro(feature_set, label):
    print(f"\n=== Leave-One-Run-Out — cible CR — {label} ===")
    r2s, maes = [], []
    for test_name in RUNS:
        train = pd.concat([dfs[n] for n in RUNS if n != test_name], ignore_index=True)
        test  = dfs[test_name]
        tr = train.dropna(subset=feature_set + ["CR_lisse"])
        te = test.dropna(subset=feature_set + ["CR_lisse"])
        if len(tr) < 50 or len(te) < 50:
            print(f"  Test sur {test_name}: pas assez de donnees"); continue
        m = xgb.XGBRegressor(**PARAMS_XGB)
        m.fit(tr[feature_set], tr["CR_lisse"])
        pred = m.predict(te[feature_set])
        r2 = r2_score(te["CR_lisse"], pred)
        mae = mean_absolute_error(te["CR_lisse"], pred)
        r2s.append(r2); maes.append(mae)
        print(f"  Train sur les 2 autres -> Test sur {test_name:14s} | R2={r2:7.3f}  MAE={mae:8.3f}")
    if r2s:
        print(f"  >>> MOYENNE  R2={np.mean(r2s):7.3f}  MAE={np.mean(maes):8.3f}")

loro(FEATURES_PROPRES, "features propres (SANS concentration)")
loro(FEATURES_PROPRES + ["concentration"], "features propres + CONCENTRATION")
