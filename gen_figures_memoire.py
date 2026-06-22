# -*- coding: utf-8 -*-
"""Génère les figures du Chapitre III du mémoire (effet température).

Figures produites dans memoire/figures/ :
  fig_iii2_runs.png        — R(t) compensé + T(t) des runs retenus (grille)
  fig_iii2_synthese.png    — durées de vie et températures moyennes par run
  fig_iii3_r2_runs.png     — R² LORO par run testé (XGB vs RegLin vs moyenne)
  fig_iii3_r2_plage.png    — R² moyen par plage de température
  fig_iii3_features.png    — importance des variables (XGBoost)
  fig_iii4_contrexemples.png — vitrine vs contre-exemples (#15, #17)

Lecture seule côté données (fetch Supabase). À relancer après chaque nouveau run.
"""
import json
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

OUTDIR = os.path.join("memoire", "figures")
os.makedirs(OUTDIR, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 10,
    "axes.titlesize": 11, "axes.labelsize": 10, "axes.grid": True,
    "grid.alpha": 0.3, "font.family": "DejaVu Sans",
})

BLEU, ORANGE, VERT, ROUGE, GRIS = "#1f4e79", "#e08a1e", "#2e8b57", "#c0392b", "#7f8c8d"

# Runs retenus + métadonnées (cohérent avec data_layer.RUNS_REGISTRY)
RUNS = {
    "Run #1":  ("d6e31719-c3fb-4797-aa0b-65c4e605002a", "Réf. ambiant"),
    "Run #11": ("72d0f7b7-e1ef-40b0-8416-851873c72440", "Ambiant 32,7 °C"),
    "Run #12": ("f5852fd4-8c3f-474e-9c20-a1ac129e018c", "Ambiant 29,5 °C"),
    "Run #14": ("83760a06-b2c8-4730-8368-18babfcae3e1", "Ambiant 31,7 °C"),
    "Run #16": ("cc4b4bec-1f3b-45ba-85d9-9c1db733eeae", "Contrôlé 30 °C"),
}
CONTRE = {
    "Run #15": ("1d0762a0-c008-410c-a366-41411bebdc56", "Régulation dégradée"),
    "Run #17": ("598f3857-6fac-4beb-aebc-57ced8b13e6b", "Acide évaporé"),
}


def couper_plateau(raw):
    if "rx_ohm" not in raw.columns or len(raw) < 50:
        return raw
    raw = raw[pd.to_numeric(raw["rx_ohm"], errors="coerce") > 0].reset_index(drop=True)
    if len(raw) < 50:
        return raw
    rx = pd.to_numeric(raw["rx_ohm"], errors="coerce").reset_index(drop=True)
    mx = float(rx.max())
    for i in range(len(rx)):
        if rx.iloc[i] >= 0.99 * mx and rx.iloc[i:i + 10].median() >= 0.95 * mx:
            return raw.iloc[:i + 1].reset_index(drop=True)
    return raw


def charger(rid):
    raw = couper_plateau(fetch_run(rid))
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df


print("Chargement des runs…")
data = {n: charger(rid) for n, (rid, _) in RUNS.items()}
data_ce = {n: charger(rid) for n, (rid, _) in CONTRE.items()}


# ---------- Figure III.2a : R(t)+T(t) des runs retenus ----------
fig, axes = plt.subplots(2, 3, figsize=(13, 7))
axes = axes.flatten()
for ax, (nom, (rid, sub)) in zip(axes, RUNS.items()):
    df = data[nom]
    t = df["temps_immersion_h"]; r = df["rx_corr"]
    ax.plot(t, r, color=BLEU, lw=1.5)
    ax.set_title(f"{nom} — {sub}")
    ax.set_xlabel("Temps d'immersion (h)"); ax.set_ylabel("R compensée (Ω)", color=BLEU)
    ax2 = ax.twinx()
    ax2.plot(t, df["temp_lisse"], color=ORANGE, lw=0.9, ls="--", alpha=0.8)
    ax2.set_ylabel("T (°C)", color=ORANGE); ax2.grid(False)
    ax2.set_ylim(26, 34)
axes[-1].axis("off")
fig.suptitle("Figure III.2 — Évolution de la résistance compensée R(t) et de la température T(t) par essai",
             fontsize=12, y=1.0)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "fig_iii2_runs.png"), bbox_inches="tight")
plt.close(fig)
print("  fig_iii2_runs.png")


# ---------- Figure III.2b : synthèse durées + températures ----------
noms = list(RUNS.keys())
durees = [float(data[n]["temps_immersion_h"].iloc[-1]) for n in noms]
temps = [float(data[n]["temp_lisse"].mean()) for n in noms]
fig, ax = plt.subplots(figsize=(9, 4.5))
x = np.arange(len(noms))
b = ax.bar(x, durees, color=BLEU, width=0.55)
ax.set_ylabel("Durée de vie (h)", color=BLEU)
ax.set_xticks(x); ax.set_xticklabels(noms)
for rect, d in zip(b, durees):
    ax.text(rect.get_x() + rect.get_width() / 2, d + 0.2, f"{d:.1f} h", ha="center", fontsize=9)
ax2 = ax.twinx()
ax2.plot(x, temps, "o-", color=ORANGE, lw=1.5)
ax2.set_ylabel("Température moyenne (°C)", color=ORANGE); ax2.grid(False); ax2.set_ylim(28, 34)
for xi, ti in zip(x, temps):
    ax2.text(xi, ti + 0.15, f"{ti:.1f}", ha="center", color=ORANGE, fontsize=8)
ax.set_title("Figure III.3 — Durée de vie et température moyenne par essai")
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "fig_iii2_synthese.png"), bbox_inches="tight")
plt.close(fig)
print("  fig_iii2_synthese.png")


# ---------- Lecture des résultats ML précalculés ----------
with open(os.path.join("dashboard", "static_results.json"), encoding="utf-8") as f:
    res = json.load(f)
proto = res["protocole_actuel"]
TEMP = {"Run12": 29.5, "Run14": 31.7, "Run16": 30.1}
LBL = {"Run12": "Run #12", "Run14": "Run #14", "Run16": "Run #16"}


# ---------- Figure III.3a : R² LORO par run (3 modèles) ----------
runs_test = list(proto.keys())
modeles = ["XGBoost", "Régression linéaire", "Moyenne constante"]
coul = {"XGBoost": BLEU, "Régression linéaire": ORANGE, "Moyenne constante": GRIS}
fig, ax = plt.subplots(figsize=(9, 4.5))
w = 0.26
for k, m in enumerate(modeles):
    vals = [max(proto[r][m]["r2"], -2.0) for r in runs_test]
    real = [proto[r][m]["r2"] for r in runs_test]
    bars = ax.bar(np.arange(len(runs_test)) + k * w, vals, w, label=m, color=coul[m])
    for rect, v in zip(bars, real):
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.03,
                f"{v:.2f}", ha="center", fontsize=7)
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(np.arange(len(runs_test)) + w)
ax.set_xticklabels([f"{LBL[r]}\n({TEMP[r]} °C)" for r in runs_test])
ax.set_ylabel("R² (test, écrêté à −2)"); ax.set_ylim(-2.2, 1.0)
ax.legend(fontsize=8)
ax.set_title("Figure III.4 — Performance LORO par essai (XGBoost vs références)")
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "fig_iii3_r2_runs.png"), bbox_inches="tight")
plt.close(fig)
print("  fig_iii3_r2_runs.png")


# ---------- Figure III.3b : R² moyen par plage ----------
plage30 = [proto[r]["XGBoost"]["r2"] for r in runs_test if TEMP[r] < 31]
plage32 = [proto[r]["XGBoost"]["r2"] for r in runs_test if TEMP[r] >= 31]
labels = ["~30 °C\n(couverte, %d essais)" % len(plage30), "~32 °C\n(non couverte, %d essai)" % len(plage32)]
vals = [np.mean(plage30), np.mean(plage32)]
fig, ax = plt.subplots(figsize=(6, 4.5))
bars = ax.bar(labels, vals, color=[VERT, ROUGE], width=0.5)
ax.axhline(0, color="black", lw=0.8)
for rect, v in zip(bars, vals):
    ax.text(rect.get_x() + rect.get_width() / 2,
            v + (0.03 if v >= 0 else -0.08), f"{v:+.2f}", ha="center", fontsize=10)
ax.set_ylabel("R² moyen (XGBoost, LORO)")
ax.set_title("Figure III.5 — Performance moyenne par plage de température")
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "fig_iii3_r2_plage.png"), bbox_inches="tight")
plt.close(fig)
print("  fig_iii3_r2_plage.png")


# ---------- Figure III.3c : importance des variables ----------
imp = res["importance_features"]
noms_fr = {
    "rx_corr": "Résistance compensée", "temp_lisse": "Température instantanée",
    "temp_moy_6h": "Température moy. 6 h", "temps_immersion_h": "Temps d'immersion",
    "delta_R_absolu": "ΔR depuis origine", "section_perdue_pct": "Section perdue (%)",
}
s = pd.Series({noms_fr.get(k, k): v for k, v in imp.items()}).sort_values()
fig, ax = plt.subplots(figsize=(8, 4))
cols = [ROUGE if v == s.max() else BLEU for v in s.values]
ax.barh(s.index, s.values, color=cols)
for i, v in enumerate(s.values):
    ax.text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=8)
ax.set_xlabel("Importance relative (XGBoost)")
ax.set_title("Figure III.6 — Importance des variables explicatives")
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "fig_iii3_features.png"), bbox_inches="tight")
plt.close(fig)
print("  fig_iii3_features.png")


# ---------- Figure III.4 : contre-exemples (R(t) vitrine vs dégradés) ----------
fig, ax = plt.subplots(figsize=(9, 4.8))
# référence vitrine : Run #16 (propre)
ref = data["Run #16"]
ax.plot(ref["temps_immersion_h"], ref["rx_corr"], color=VERT, lw=2,
        label="Run #16 — vitrine 30 °C (propre)")
for nom, coul in zip(CONTRE.keys(), [ORANGE, ROUGE]):
    df = data_ce[nom]
    ax.plot(df["temps_immersion_h"], df["rx_corr"], color=coul, lw=1.5, ls="--",
            label=f"{nom} — {CONTRE[nom][1]}")
ax.set_xlabel("Temps d'immersion (h)"); ax.set_ylabel("R compensée (Ω)")
ax.legend(fontsize=8)
ax.set_title("Figure III.7 — Vitrine 30 °C vs contre-exemples (facteur non contrôlé)")
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "fig_iii4_contrexemples.png"), bbox_inches="tight")
plt.close(fig)
print("  fig_iii4_contrexemples.png")

print("\nToutes les figures sont dans", OUTDIR)
