# -*- coding: utf-8 -*-
"""Modele physique de degradation : 1/R lineaire en t -> predit le temps de rupture.
R = rhoL/(A0 - k.t)  =>  1/R = a - b.t  =>  rupture quand 1/R = 0  =>  t_rup = a/b."""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

RUNS = {
    "Run1 (brut)": "d6e31719-c3fb-4797-aa0b-65c4e605002a",
    "Run2 (1:1)":  "66e66c0a-b4c6-40fd-937b-c25fcc71a56c",
}
FRACTIONS = [0.4, 0.5, 0.6, 0.7, 0.8]   # % de la duree observe avant de predire

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
for ax, (name, rid) in zip(axes, RUNS.items()):
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name).reset_index(drop=True)
    t = df["timestamp_h"].values - df["timestamp_h"].values[0]
    R = df["rx_corr"].values
    invR = 1.0 / R
    t_rup_reel = t[-1]            # rupture = dernier point des donnees nettoyees

    print(f"\n=== {name}  (rupture reelle a {t_rup_reel:.1f}h) ===")
    print(f"  {'Observe':>8} | {'t_rup predit':>13} | {'RUL predite':>12} | {'erreur':>8}")
    t_start = 0.15 * t_rup_reel   # on saute la phase d'induction initiale
    for fr in FRACTIONS:
        t_obs = fr * t_rup_reel
        mask = (t >= t_start) & (t <= t_obs)
        if mask.sum() < 30: continue
        slope, intercept = np.polyfit(t[mask], invR[mask], 1)   # 1/R = intercept + slope*t
        if slope >= 0: continue
        t_rup_pred = -intercept / slope
        rul_pred = t_rup_pred - t_obs
        rul_reel = t_rup_reel - t_obs
        err = (t_rup_pred - t_rup_reel)
        print(f"  {fr*100:6.0f}%  | {t_rup_pred:11.1f}h  | {rul_pred:10.1f}h  | {err:+6.1f}h")

    # Figure : 1/R vs t + droite ajustee sur 60% + croisement zero
    ax.scatter(t, invR, s=4, color="#2980b9", alpha=0.3, label="1/R mesuré")
    mask = (t >= t_start) & (t <= 0.6 * t_rup_reel)
    sl, ic = np.polyfit(t[mask], invR[mask], 1)
    tline = np.linspace(t_start, t_rup_reel * 1.05, 50)
    ax.plot(tline, ic + sl * tline, color="#c0392b", lw=2, label="Droite ajustée (sur 60%)")
    ax.axhline(0, color="grey", lw=0.8, ls=":")
    ax.axvline(-ic / sl, color="#27ae60", lw=1.5, ls="--", label=f"Rupture prédite ({-ic/sl:.1f}h)")
    ax.axvline(t_rup_reel, color="#000", lw=1.5, ls="-", alpha=0.6, label=f"Rupture réelle ({t_rup_reel:.1f}h)")
    ax.set_title(f"{name} — 1/R linéaire prédit la rupture", fontsize=11, fontweight="bold")
    ax.set_xlabel("Temps (h)"); ax.set_ylabel("1 / R  (1/Ohm)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3); ax.set_ylim(bottom=-0.05)

plt.tight_layout()
for out in ["plots/fig_physics_rul.png", "memoire/figures/fig_physics_rul.png"]:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150)
print("\nFigure : memoire/figures/fig_physics_rul.png")
