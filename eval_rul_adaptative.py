# -*- coding: utf-8 -*-
"""RUL ADAPTATIVE : recalculee en continu avec le taux de corrosion INSTANTANE.
RUL(t) = rayon_restant(t) / CR_instantane(t).  Converge-t-elle vers la vraie rupture ?"""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

RID = "d6e31719-c3fb-4797-aa0b-65c4e605002a"  # Run1
r0 = 0.575      # mm
WIN = 240       # fenetre CR = 2h (lissage)

raw = fetch_run(RID)
tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
raw.to_csv(tmp, sep=";", index=False); tmp.close()
df = traiter_run(tmp.name).reset_index(drop=True)
t = df["timestamp_h"].values - df["timestamp_h"].values[0]
R = pd.Series(df["rx_corr"].values).rolling(40, min_periods=1, center=True).median().values
R0 = np.median(R[(t > 0.10*t[-1]) & (t < 0.20*t[-1])])
t_rup = t[-1]

rad = r0 * np.sqrt(R0 / R)                       # rayon (mm)
dr = pd.Series(rad).diff(WIN).values
dth = pd.Series(t).diff(WIN).values
CR_h = -dr / dth                                 # mm/h (instantane, lisse sur 2h)

RUL_pred = np.full_like(t, np.nan)
date_pred = np.full_like(t, np.nan)
for i in range(len(t)):
    if not np.isnan(CR_h[i]) and CR_h[i] > 1e-4:
        RUL_pred[i] = rad[i] / CR_h[i]           # heures restantes
        date_pred[i] = t[i] + RUL_pred[i]

print(f"=== Run1 — rupture reelle a {t_rup:.1f}h ===")
print(f"  {'Instant':>8} | {'CR instant':>11} | {'RUL predite':>11} | {'Rupture predite':>15} | {'erreur':>8}")
for inst in [4, 8, 12, 16, 18, 20, 21]:
    j = np.argmin(np.abs(t - inst))
    if not np.isnan(date_pred[j]):
        print(f"  {t[j]:6.1f}h | {CR_h[j]*8760:8.0f} mm/an | {RUL_pred[j]:8.1f}h  | {date_pred[j]:13.1f}h  | {date_pred[j]-t_rup:+6.1f}h")

# Figure
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
a1.plot(t, date_pred, color="#c0392b", lw=1.8, label="Rupture prédite (RUL adaptative)")
a1.axhline(t_rup, color="#000", lw=1.6, ls="--", label=f"Rupture réelle ({t_rup:.1f}h)")
a1.fill_between(t, t_rup*0.85, t_rup*1.15, color="#27ae60", alpha=0.12, label="± 15 %")
a1.set_ylabel("Instant de rupture prédit (h)"); a1.set_ylim(0, 80)
a1.set_title("RUL adaptative — la prédiction converge vers la rupture réelle\n"
             "à mesure que le taux de corrosion s'emballe", fontsize=12, fontweight="bold")
a1.legend(fontsize=10); a1.grid(True, alpha=0.3)

a2.plot(t, CR_h*8760, color="#2980b9", lw=1.6, label="Taux de corrosion instantané")
a2.set_xlabel("Temps depuis immersion (h)"); a2.set_ylabel("CR (mm/an)")
a2.legend(fontsize=10); a2.grid(True, alpha=0.3)
plt.tight_layout()
for out in ["plots/fig_rul_adaptative.png", "memoire/figures/fig_rul_adaptative.png"]:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150)
print("\nFigure : memoire/figures/fig_rul_adaptative.png")
