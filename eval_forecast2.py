# -*- coding: utf-8 -*-
"""Forecasting de la VARIATION future dR (grandeur bornee) au lieu du niveau absolu.
Le ML peut-il capter l'acceleration avant rupture mieux que les baselines ?"""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd, numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score

from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

RUNS = {
    "Run1 (brut)": "d6e31719-c3fb-4797-aa0b-65c4e605002a",
    "Run2 (1:1)":  "66e66c0a-b4c6-40fd-937b-c25fcc71a56c",
    "Run3 (2:1)":  "1a42265f-96a6-4f52-aaff-d7a6d5f27d4c",
}
H = 120   # horizon 1h (30s x 120)
PARAMS = dict(n_estimators=300, max_depth=4, learning_rate=0.05,
              subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1)

print("=== Forecasting de la VARIATION dR a 1h (cible bornee) ===\n")
for name, rid in RUNS.items():
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name).reset_index(drop=True)
    r = pd.Series(df["rx_corr"].values)

    dr_recent = r.diff(H)               # variation derniere heure
    dr_prev   = r.shift(H).diff(H)      # variation heure precedente
    accel     = dr_recent - dr_prev     # acceleration
    y         = r.shift(-H) - r         # CIBLE : variation sur la prochaine heure

    d = pd.DataFrame({
        "r_now": r, "dr_recent": dr_recent, "accel": accel,
        "temp": df["temp_lisse"].values, "t_imm": df["temps_immersion_h"].values,
        "y": y,
    }).dropna().reset_index(drop=True)

    n = len(d); cut = int(n * 0.6)
    tr, te = d.iloc[:cut], d.iloc[cut:]
    feats = ["r_now", "dr_recent", "accel", "temp", "t_imm"]

    m = xgb.XGBRegressor(**PARAMS); m.fit(tr[feats], tr["y"])
    pred_xgb = m.predict(te[feats])
    pred_persist_rate = te["dr_recent"].values    # baseline : le taux continue pareil
    pred_zero = np.zeros(len(te))                 # baseline : pas de changement

    def mm(p): return r2_score(te["y"], p), mean_absolute_error(te["y"], p)
    r2x, mx = mm(pred_xgb); r2p, mp = mm(pred_persist_rate); r2z, mz = mm(pred_zero)

    print(f"--- {name}  ({n} ech., test 40% final, cible = dR sur 1h) ---")
    print(f"  XGBoost            | R2={r2x:7.3f}  MAE={mx:.4f} Ohm")
    print(f"  Baseline taux const| R2={r2p:7.3f}  MAE={mp:.4f} Ohm")
    print(f"  Baseline zero      | R2={r2z:7.3f}  MAE={mz:.4f} Ohm")
    best = min([(mx,"XGBoost"),(mp,"taux const"),(mz,"zero")])
    print(f"  -> Meilleur : {best[1]}\n")
