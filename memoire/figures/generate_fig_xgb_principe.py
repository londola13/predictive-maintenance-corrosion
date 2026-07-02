# -*- coding: utf-8 -*-
"""Schéma pédagogique (slide) : le gradient boosting montré sur UN INSTANT RÉEL.

Point choisi : Run #12 (base Supabase), t ≈ 12,3 h, T = 27,7 °C, R = 2,03 Ω,
section perdue ≈ 40 %, CR mesuré ≈ 389 µm/an. Le script recharge le modèle réel
(models/xgb_cr.pkl) et rejoue sa construction : prédiction cumulée après
1, 2, 3, 10, 50 puis 500 arbres (iteration_range). Rien n'est inventé :
chaque barre est la sortie du modèle entraîné. Requiert SUPABASE_KEY.
Pas de titre gravé : porté par la slide.
"""
import os
import pickle
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

import numpy as np
import matplotlib.pyplot as plt
from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run

INK, MUTED, RUST, TEAL = "#202B31", "#6B7A82", "#C9601A", "#0A9498"
CHIP = "#EDEAE3"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_xgb_principe.png")
RUN12 = "f5852fd4-8c3f-474e-9c20-a1ac129e018c"
ETAPES = [1, 2, 3, 10, 50, 500]

# ── calcul réel : prédiction cumulée arbre par arbre sur l'instant choisi ────
model = pickle.load(open(os.path.join(ROOT, "models", "xgb_cr.pkl"), "rb"))
feats = list(model.feature_names_in_)
raw = fetch_run(RUN12)
tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
raw.to_csv(tmp, sep=";", index=False); tmp.close()
d = traiter_run(tmp.name)
os.unlink(tmp.name)
d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=feats + ["CR_lisse"]).reset_index(drop=True)

# instant t ≈ 12,3 h (début d'emballement, bien expliqué par le modèle)
cand = d[(d["temps_immersion_h"].between(12.25, 12.40)) & (d["CR_lisse"] > 380)]
row = cand.iloc[0]
X = row[feats].to_frame().T.astype(float)
cr_meas = float(row["CR_lisse"])
preds = [float(model.predict(X, iteration_range=(0, k))[0]) for k in ETAPES]
print("instant :", f"t={row['temps_immersion_h']:.1f}h T={row['temp_lisse']:.1f}C "
      f"R={row['rx_corr']:.2f} sect={row['section_perdue_pct']:.0f}% CR={cr_meas:.0f}")
print("preds   :", [round(p) for p in preds])

# ── figure ───────────────────────────────────────────────────────────────────
fig, (axL, ax) = plt.subplots(1, 2, figsize=(12.6, 4.3),
                              gridspec_kw={"width_ratios": [1, 2.55], "wspace": 0.14})

def fr(v, nd=1):
    return f"{v:.{nd}f}".replace(".", ",")

# panneau gauche : l'instant réel (carte)
axL.set_xlim(0, 1); axL.set_ylim(0, 1); axL.axis("off")
axL.add_patch(plt.Rectangle((0.02, 0.04), 0.96, 0.92, fc=CHIP, ec=MUTED, lw=1.2))
axL.text(0.5, 0.84, "Un instant réel\nde l'essai n°12", ha="center", va="center",
         fontsize=11.5, color=INK, fontweight="bold", linespacing=1.4)
axL.text(0.5, 0.55, f"t = {fr(row['temps_immersion_h'])} h\n"
                    f"T = {fr(row['temp_lisse'])} °C\n"
                    f"R = {fr(row['rx_corr'], 2)} Ω\n"
                    f"section perdue ≈ {row['section_perdue_pct']:.0f} %",
         ha="center", va="center", fontsize=10.5, color=INK, linespacing=1.8)
axL.text(0.5, 0.24, "le modèle doit prédire :", ha="center", fontsize=9.5, color=MUTED)
axL.text(0.5, 0.13, f"CR mesuré = {cr_meas:.0f} µm/an", ha="center", fontsize=12,
         color=TEAL, fontweight="bold")

# panneau droit : la prédiction se construit arbre après arbre
xs = np.arange(len(ETAPES))
bars = ax.bar(xs, preds, width=0.58, color=["#9AA6AC"] * (len(ETAPES) - 1) + [RUST],
              edgecolor="white", linewidth=1.2, zorder=3)
ax.axhline(cr_meas, color=TEAL, ls="--", lw=1.8, zorder=2)
ax.text(0.62, cr_meas + 14, f"CR mesuré : {cr_meas:.0f}",
        ha="left", fontsize=10.5, color=TEAL, fontweight="bold")

for x, p in zip(xs, preds):
    ax.text(x, p + 12, f"{p:.0f}", ha="center", fontsize=10.5, color=INK,
            fontweight="bold", zorder=4)

# erreurs : première et dernière barre (récit du boosting)
ax.annotate(f"erreur : {preds[0]-cr_meas:+.0f}", xy=(0, preds[0]),
            xytext=(0, preds[0] + 105), ha="center", fontsize=9.5, color=RUST,
            arrowprops=dict(arrowstyle="-|>", color=RUST, lw=1.2))
ax.text(len(ETAPES) - 1, preds[-1] / 2, f"erreur : {preds[-1]-cr_meas:+.0f}",
        ha="center", va="center", fontsize=9.5, color="white", fontweight="bold",
        rotation=90, zorder=5)

ax.set_xticks(xs)
ax.set_xticklabels(["1 arbre", "2 arbres", "3 arbres", "10 arbres", "50 arbres", "500 arbres"],
                   fontsize=10)
ax.set_xlim(-0.65, len(ETAPES) - 0.30)
ax.set_ylabel("CR prédit (µm/an)", fontsize=10.5)
ax.set_ylim(0, max(cr_meas, max(preds)) * 1.30)
ax.grid(axis="y", alpha=0.25)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.text(0.02, -0.24, "prédiction cumulée : chaque arbre supplémentaire ajoute une petite "
        "correction apprise sur les erreurs restantes",
        transform=ax.transAxes, fontsize=9.5, color=MUTED, style="italic")

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
