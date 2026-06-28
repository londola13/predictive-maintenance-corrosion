# -*- coding: utf-8 -*-
"""Figure III.11 — « Prédire-puis-confirmer » : la bande prédictive de durée de vie du jumeau
numérique confrontée à deux essais graduels réels survenus APRÈS la prédiction.

Constantes documentées (mémoire §III.6.5, figure III.10 / bande Run #21) :
  - bande prédictive (P10–P90)        : [13 ; 20,5] h, médiane 16 h
  - Run #21 (graduel) rupture         : 13,1 h  → DANS la bande (borne basse)  = touché
  - Run #22 (graduel) rupture         : 11,95 h → EN DEÇÀ de la bande           = manqué
Run #22 est l'essai le plus rapide de toute la campagne : il tombe sous l'enveloppe des donneurs
(le jumeau interpole entre morphologies observées, il n'extrapole pas au-delà). Bilan honnête : 1/2.
"""
import os
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_iii3_band_scorecard.png")

P10, P50, P90 = 13.0, 16.0, 20.5
RUN21, RUN22 = 13.1, 11.95

fig, ax = plt.subplots(figsize=(9.6, 3.9))

# Bande prédictive P10–P90
ax.axvspan(P10, P90, color="#cfe3f5", alpha=0.85, zorder=1,
           label="Bande prédictive du jumeau (P10–P90)")
ax.axvline(P50, color="#1f4e79", ls="--", lw=1.4, zorder=3)
ax.text(P50, 1.38, "médiane\n16 h", color="#1f4e79", fontsize=8.6, ha="center",
        va="bottom", family="serif")
for xb, lab in [(P10, "P10 = 13 h"), (P90, "P90 = 20,5 h")]:
    ax.text(xb, 0.46, lab, color="#2a5a86", fontsize=8.2, ha="center", va="center",
            rotation=90, family="serif")

# Essais réels (survenus après la prédiction)
ax.scatter([RUN21], [1.0], s=190, marker="o", color="#2e7d32", zorder=5, edgecolor="white", lw=1.5)
ax.annotate("Run #21 — 13,1 h\nTOUCHÉ (dans la bande)", xy=(RUN21, 1.0), xytext=(14.2, 1.72),
            fontsize=9.2, family="serif", color="#1b5e20", ha="left",
            arrowprops=dict(arrowstyle="-|>", color="#2e7d32", lw=1.3))

ax.scatter([RUN22], [1.0], s=210, marker="X", color="#c0392b", zorder=5, edgecolor="white", lw=1.5)
ax.annotate("Run #22 — 11,95 h\nMANQUÉ (en deçà de P10)", xy=(RUN22, 1.0), xytext=(10.05, 1.72),
            fontsize=9.2, family="serif", color="#922b21", ha="left",
            arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=1.3))

# Scorecard
ax.text(0.985, 0.05,
        "Bilan prédire-puis-confirmer : 1 touché / 1 manqué.\n"
        "Run #22 est l'essai le plus rapide de la campagne → sous l'enveloppe des donneurs :\n"
        "le jumeau interpole entre morphologies observées, il n'extrapole pas au-delà.",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8.1, family="serif",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fffdf3", edgecolor="#b8860b", lw=1))

ax.set_xlim(9.8, 22)
ax.set_ylim(0.3, 2.1)
ax.set_yticks([])
ax.set_xlabel("Durée de vie / temps de rupture (h)", fontsize=10.5)
ax.set_title("Figure III.15 — Bande prédictive de durée de vie du jumeau confrontée\n"
             "à deux essais graduels réels (Run #21 touché, Run #22 manqué)",
             fontsize=11.5, family="serif")
ax.legend(loc="upper right", fontsize=8.4, framealpha=0.9)
for s in ("top", "left", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"OK -> {OUT}")
