# -*- coding: utf-8 -*-
"""Forecasting court terme intra-run : predire R dans 1h a partir du passe recent.
Compare XGBoost a 2 baselines naives (persistance, extrapolation lineaire)."""
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
H = 120          # horizon de prediction : 120 pts x 30s = 1 heure
LAG1, LAG2 = 60, 120   # historique : -30 min, -1h

PARAMS = dict(n_estimators=300, max_depth=4, learning_rate=0.05,
              subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1)

print("=== Forecasting intra-run : predire R(t+1h) ===\n")
for name, rid in RUNS.items():
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name).reset_index(drop=True)
    r = df["rx_corr"].values

    d = pd.DataFrame({
        "r_now":  r,
        "r_lag1": pd.Series(r).shift(LAG1),
        "r_lag2": pd.Series(r).shift(LAG2),
        "pente":  pd.Series(r).diff(LAG2),          # variation sur la derniere heure
        "temp":   df["temp_lisse"].values,
        "t_imm":  df["temps_immersion_h"].values,
        "y":      pd.Series(r).shift(-H),            # cible : R dans 1h
    }).dropna().reset_index(drop=True)

    n = len(d); cut = int(n * 0.6)
    tr, te = d.iloc[:cut], d.iloc[cut:]
    feats = ["r_now", "r_lag1", "r_lag2", "pente", "temp", "t_imm"]

    m = xgb.XGBRegressor(**PARAMS)
    m.fit(tr[feats], tr["y"])
    pred_xgb = m.predict(te[feats])

    pred_persist = te["r_now"].values                       # baseline 1 : R(t+1h)=R(t)
    pred_lin = (te["r_now"] + te["pente"]).values           # baseline 2 : extrapolation lineaire

    def m2(p): return r2_score(te["y"], p), mean_absolute_error(te["y"], p)
    r2x, mx = m2(pred_xgb); r2p, mp = m2(pred_persist); r2l, ml = m2(pred_lin)

    print(f"--- {name}  ({n} echantillons, test sur 40% final) ---")
    print(f"  XGBoost          | R2={r2x:6.3f}  MAE={mx:.4f} Ohm")
    print(f"  Baseline persist.| R2={r2p:6.3f}  MAE={mp:.4f} Ohm")
    print(f"  Baseline lineaire| R2={r2l:6.3f}  MAE={ml:.4f} Ohm")
    gain = (mp - mx) / mp * 100 if mp > 0 else 0
    print(f"  -> XGBoost ameliore la persistance de {gain:.0f}% sur le MAE\n")
