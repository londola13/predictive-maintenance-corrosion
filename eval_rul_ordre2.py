# -*- coding: utf-8 -*-
"""RUL du 2nd ordre : integre l'acceleration du taux de corrosion (analogie cinematique).
RUL = (-CR + sqrt(CR^2 + 2*a*r)) / a   vs   RUL naive = r/CR."""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

RID = "d6e31719-c3fb-4797-aa0b-65c4e605002a"
r0 = 0.575; WIN = 240
raw = fetch_run(RID)
tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
raw.to_csv(tmp, sep=";", index=False); tmp.close()
df = traiter_run(tmp.name).reset_index(drop=True)
t = df["timestamp_h"].values - df["timestamp_h"].values[0]
R = pd.Series(df["rx_corr"].values).rolling(40, min_periods=1, center=True).median().values
R0 = np.median(R[(t > 0.10*t[-1]) & (t < 0.20*t[-1])]); t_rup = t[-1]

rad = pd.Series(r0 * np.sqrt(R0 / R))                  # rayon mm
CR = (-rad.diff(WIN) / pd.Series(t).diff(WIN))         # mm/h (vitesse)
CR_s = CR.rolling(120, min_periods=1, center=True).mean()
a = (CR_s.diff(WIN) / pd.Series(t).diff(WIN))          # mm/h^2 (acceleration)
a_s = a.rolling(120, min_periods=1, center=True).mean()
rad = rad.values; CR_s = CR_s.values; a_s = a_s.values

def rul_o1(i):
    return rad[i]/CR_s[i] if CR_s[i] > 1e-4 else np.nan
def rul_o2(i):
    c, ac, r = CR_s[i], a_s[i], rad[i]
    if c <= 1e-4: return np.nan
    if ac <= 1e-6: return r/c                          # pas d'accel -> 1er ordre
    disc = c*c + 2*ac*r
    return (-c + np.sqrt(disc))/ac if disc > 0 else np.nan

print(f"=== Run1 — rupture a {t_rup:.1f}h ===")
print(f"  {'t':>6} | {'RUL reelle':>10} | {'RUL 1er ordre':>13} | {'RUL 2nd ordre':>13}")
for inst in [8, 12, 14, 16, 18, 20, 21]:
    j = np.argmin(np.abs(t - inst))
    real = t_rup - t[j]
    o1, o2 = rul_o1(j), rul_o2(j)
    print(f"  {t[j]:5.1f}h | {real:8.1f}h | {o1:11.1f}h | {o2:11.1f}h")

# Figure : instant de rupture predit par chaque methode
dp1 = np.array([t[i] + rul_o1(i) for i in range(len(t))])
dp2 = np.array([t[i] + rul_o2(i) for i in range(len(t))])
plt.figure(figsize=(11, 6))
plt.plot(t, dp1, color="#e67e22", lw=1.6, label="Rupture prédite — 1er ordre (r/CR)")
plt.plot(t, dp2, color="#c0392b", lw=2.0, label="Rupture prédite — 2nd ordre (avec accélération)")
plt.axhline(t_rup, color="#000", lw=1.6, ls="--", label=f"Rupture réelle ({t_rup:.1f}h)")
plt.fill_between(t, t_rup*0.85, t_rup*1.15, color="#27ae60", alpha=0.12, label="± 15 %")
plt.ylim(0, 80); plt.xlabel("Temps (h)"); plt.ylabel("Instant de rupture prédit (h)")
plt.title("Correction de la RUL par l'accélération du taux de corrosion\n"
          "Le 2nd ordre (cinématique) converge plus tôt vers la rupture réelle",
          fontsize=12, fontweight="bold")
plt.legend(fontsize=10); plt.grid(True, alpha=0.3); plt.tight_layout()
for out in ["plots/fig_rul_ordre2.png", "memoire/figures/fig_rul_ordre2.png"]:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150)
print("\nFigure : memoire/figures/fig_rul_ordre2.png")
