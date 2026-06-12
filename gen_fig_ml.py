# -*- coding: utf-8 -*-
"""Figure memoire : XGBoost (plafonne) vs extrapolation lineaire (suit) — Run1."""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, matplotlib.pyplot as plt
import xgboost as xgb
from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

RID = "d6e31719-c3fb-4797-aa0b-65c4e605002a"   # Run1 brut
H = 120
raw = fetch_run(RID)
tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
raw.to_csv(tmp, sep=";", index=False); tmp.close()
df = traiter_run(tmp.name).reset_index(drop=True)
r = pd.Series(df["rx_corr"].values); th = df["timestamp_h"].values - df["timestamp_h"].values[0]

d = pd.DataFrame({
    "t_h": th, "r_now": r.values,
    "r_lag1": r.shift(60).values, "r_lag2": r.shift(120).values,
    "pente": r.diff(120).values, "temp": df["temp_lisse"].values,
    "t_imm": df["temps_immersion_h"].values, "y": r.shift(-H).values,
}).dropna().reset_index(drop=True)

n = len(d); cut = int(n * 0.6)
tr, te = d.iloc[:cut], d.iloc[cut:]
feats = ["r_now", "r_lag1", "r_lag2", "pente", "temp", "t_imm"]
m = xgb.XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                     subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1)
m.fit(tr[feats], tr["y"])
pred_xgb = m.predict(te[feats])
pred_lin = (te["r_now"] + te["pente"]).values

plt.figure(figsize=(11, 6))
plt.plot(te["t_h"], te["y"], color="#1a1a1a", linewidth=2.4, label="Résistance réelle (à +1h)")
plt.plot(te["t_h"], pred_lin, color="#27ae60", linewidth=1.8, linestyle="--", label="Extrapolation linéaire (baseline)")
plt.plot(te["t_h"], pred_xgb, color="#c0392b", linewidth=1.8, linestyle=":", label="XGBoost (modèle ML)")
plt.axvspan(te["t_h"].iloc[0], te["t_h"].iloc[-1], color="#f4d03f", alpha=0.08)
plt.xlabel("Temps depuis immersion (heures)", fontsize=12)
plt.ylabel("Résistance prédite à +1h (Ohm)", fontsize=12)
plt.title("Prévision de la dégradation — Essai 1 (HCl brut)\n"
          "XGBoost plafonne (incapacité à extrapoler) ; l'extrapolation linéaire suit la montée",
          fontsize=12, fontweight="bold")
plt.legend(fontsize=11, loc="upper left")
plt.grid(True, alpha=0.3)
plt.tight_layout()
for out in ["plots/fig_ml_vs_baseline.png", "memoire/figures/fig_ml_vs_baseline.png"]:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150)
print("Figure sauvee : plots/fig_ml_vs_baseline.png  et  memoire/figures/")
