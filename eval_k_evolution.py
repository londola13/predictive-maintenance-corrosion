# -*- coding: utf-8 -*-
"""Evolution de la vitesse de corrosion k(t) : demontrer l'acceleration terminale.
r(t) = r0 * sqrt(R0/R(t)) ; CR(t) = -dr/dt (vitesse de perte de rayon)."""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

RUNS = {"Run1 (brut)": "d6e31719-c3fb-4797-aa0b-65c4e605002a",
        "Run2 (1:1)":  "66e66c0a-b4c6-40fd-937b-c25fcc71a56c"}
R0_MM = 0.575e-3   # rayon initial en metres (d=1.15mm)
WIN = 120          # fenetre derivee = 1h (120 x 30s)

fig, ax = plt.subplots(figsize=(11, 6))
for name, rid in RUNS.items():
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name).reset_index(drop=True)
    t = df["timestamp_h"].values - df["timestamp_h"].values[0]
    R = pd.Series(df["rx_corr"].values).rolling(20, min_periods=1, center=True).median().values
    R0 = np.median(R[(t > 0.10*t[-1]) & (t < 0.20*t[-1])])   # baseline apres mouillage

    r = R0_MM * np.sqrt(R0 / R)                  # rayon (m) au cours du temps
    r_mm = r * 1000
    dr = pd.Series(r_mm).diff(WIN).values        # variation rayon sur 1h (mm)
    dt_h = pd.Series(t).diff(WIN).values
    CR = -dr / dt_h * 8760.0                     # vitesse de corrosion en mm/an

    # phase lente (20-40%) vs phase terminale (derniers 5%)
    slow = np.nanmean(CR[(t > 0.20*t[-1]) & (t < 0.40*t[-1])])
    term = np.nanmean(CR[t > 0.95*t[-1]])
    print(f"\n=== {name} ===")
    print(f"  R0 baseline          : {R0:.3f} Ohm  -> rayon initial {R0_MM*1000:.3f} mm")
    print(f"  CR phase lente (20-40%) : {slow:7.1f} mm/an")
    print(f"  CR phase terminale (>95%): {term:7.1f} mm/an")
    print(f"  >>> ACCELERATION : x{term/slow:.1f}")

    ax.plot(t, CR, label=f"{name}", linewidth=1.6)

ax.set_xlabel("Temps depuis immersion (h)", fontsize=12)
ax.set_ylabel("Vitesse de corrosion estimée (mm/an)", fontsize=12)
ax.set_title("Évolution de la vitesse de corrosion : accélération terminale\n"
             "La corrosion est lente puis s'emballe avant la rupture (k non constant)",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=11); ax.grid(True, alpha=0.3)
plt.tight_layout()
for out in ["plots/fig_k_evolution.png", "memoire/figures/fig_k_evolution.png"]:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150)
print("\nFigure : memoire/figures/fig_k_evolution.png")
