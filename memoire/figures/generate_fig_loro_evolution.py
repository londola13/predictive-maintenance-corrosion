# -*- coding: utf-8 -*-
"""Figure III.5 — Évolution du R² LORO au fil de la campagne : du LORO initial
(couverture nulle, R² très négatif) au LORO actuel (couverture 30 °C établie, R² positif),
puis le léger recul induit par l'ajout d'une morphologie non appariée (run graduel).

Les valeurs proviennent des résultats DÉJÀ établis et rapportés dans le mémoire :
  - série 30 °C seule (couverture nulle)  : R² = -1,77   (§III.3.3, ex-figure III.5 « variantes »)
  - + auxiliaires 30 °C répétés           : R² = +0,29   (Tableau III.2, variante retenue)
  - + run graduel (Run #21 / #22)         : R² ≈ +0,20   (§III.3.3, fourchette +0,18…+0,24)
La métrique est BRUITÉE au vu du faible effectif → bandes = fourchettes inter-graines (jamais une
seule graine). Aucun recalcul ici : la figure visualise des résultats déjà calculés et publiés.
"""
import os
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_iii3_loro_evolution.png")

# --- Étapes (constantes documentées) ---------------------------------------
labels = [
    "Série 30 °C seule\n(couverture nulle)",
    "+ auxiliaires 30 °C\nrépétés (couverture établie)",
    "+ run graduel\n(morphologie ≠ test sprint)",
]
x = [0, 1, 2]
r2 = [-1.77, 0.29, 0.20]
# Fourchettes inter-graines (bornes basses/hautes) — None = valeur unique (catastrophique)
band_lo = [None, 0.25, 0.18]
band_hi = [None, 0.29, 0.24]

fig, ax = plt.subplots(figsize=(9.6, 5.9))

# Zones de lecture : échec (R²<0) vs prédiction fiable (R²>0)
ax.axhspan(-2.0, 0.0, color="#fdecea", alpha=0.7, zorder=0)
ax.axhspan(0.0, 0.7, color="#eaf6ec", alpha=0.7, zorder=0)
ax.axhline(0.0, color="#888888", ls="--", lw=1.2, zorder=2)
ax.text(-0.28, 0.03, "R² = 0 (prédiction naïve)", color="#555555", fontsize=8.2,
        va="bottom", ha="left", family="serif")

# Trajectoire en escalier
ax.plot(x, r2, color="#1f4e79", lw=2.2, marker="o", ms=9, mfc="white",
        mec="#1f4e79", mew=2.2, zorder=5)

# Fourchettes (barres d'incertitude) sur les points positifs
for xi, yi, lo, hi in zip(x, r2, band_lo, band_hi):
    if lo is not None:
        ax.errorbar(xi, yi, yerr=[[yi - lo], [hi - yi]], fmt="none",
                    ecolor="#1f4e79", elinewidth=1.6, capsize=6, capthick=1.6, zorder=4)

# Étiquettes de valeur
val_txt = ["R² = −1,77", "R² = +0,29", "R² ≈ +0,20"]
val_dy = [0.16, 0.085, -0.135]
val_va = ["bottom", "bottom", "top"]
for xi, yi, t, dy, va in zip(x, r2, val_txt, val_dy, val_va):
    ax.annotate(t, xy=(xi, yi), xytext=(xi, yi + dy), ha="center", va=va,
                fontsize=11, fontweight="bold", color="#1f4e79", family="serif")

# Commentaires de transition (placés dans les zones vides, sans flèche qui croise le texte)
ax.text(0.5, -1.12, "Couverture et répétition\ndes conditions 30 °C", color="#2e7d32",
        fontsize=9.2, ha="center", va="center", family="serif",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#2e7d32", lw=1, alpha=0.95))

ax.text(1.5, 0.52, "Morphologie non appariée :\nléger recul, métrique bruitée", color="#9a6a00",
        fontsize=9.2, ha="center", va="center", family="serif",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#b8860b", lw=1, alpha=0.95))

# Repères « LORO initial / actuel »
ax.text(0, -1.92, "LORO initial", ha="center", va="bottom", fontsize=9.5,
        style="italic", color="#b03a2e", family="serif")
ax.text(1, 0.62, "LORO actuel", ha="center", va="top", fontsize=9.5,
        style="italic", color="#2e7d32", family="serif")

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9.6)
ax.set_ylim(-2.0, 0.7)
ax.set_xlim(-0.35, 2.5)
ax.set_ylabel("R² LORO moyen (essais de test sprint : Run #12 et #16)", fontsize=10.5)
ax.set_title("Figure III.5 — Évolution du R² LORO : du LORO initial (couverture nulle)\n"
             "au LORO actuel (couverture établie), puis effet d'une morphologie non appariée",
             fontsize=12, family="serif")
ax.grid(axis="y", alpha=0.25)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"OK -> {OUT}")
