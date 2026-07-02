# -*- coding: utf-8 -*-
"""Schéma pédagogique (slide) : d'où vient le R² LORO moyen de +0,29.

Mécanique leave-one-run-out sur la série de test 30 °C (protocole retenu,
Tableau III.2) : deux plis, un par essai testé, jamais vu à l'entraînement.
  pli A : test Run #12 -> R² = +0,50    pli B : test Run #16 -> R² = +0,07
  moyenne = (+0,50 + 0,07) / 2 ≈ +0,29
Pas de titre gravé : porté par la slide.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mp

INK, MUTED, RUST, TEAL = "#202B31", "#6B7A82", "#C9601A", "#0A9498"
CHIP = "#E7E4DD"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_loro_mecanique.png")

fig, ax = plt.subplots(figsize=(12.4, 4.2))
ax.set_xlim(0, 12.4); ax.set_ylim(0, 4.2); ax.axis("off")

CW, CH, GAP = 0.92, 0.62, 0.14   # chips


def chip(x, y, label, test=False):
    fc = TEAL if test else CHIP
    tc = "white" if test else INK
    ax.add_patch(mp.FancyBboxPatch((x, y), CW, CH, boxstyle="round,pad=0.045",
                                   fc=fc, ec=(TEAL if test else MUTED), lw=1.2))
    ax.text(x + CW / 2, y + CH / 2, label, ha="center", va="center",
            fontsize=10, color=tc, fontweight="bold")


def fold(y, nom, train, test_lab, r2):
    ax.text(0.25, y + CH / 2, nom, ha="left", va="center", fontsize=11.5,
            color=INK, fontweight="bold")
    x = 1.45
    for lab in train:
        chip(x, y, lab)
        x += CW + GAP
    x += 0.30                       # petit écart avant l'essai testé
    chip(x, y, test_lab, test=True)
    ax.annotate("", xy=(x + CW + 1.05, y + CH / 2), xytext=(x + CW + 0.22, y + CH / 2),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5, mutation_scale=15))
    ax.text(x + CW + 1.25, y + CH / 2, r2, ha="left", va="center",
            fontsize=15, color=INK, fontweight="bold")
    return x  # position du chip test

TRAIN_A = ["#1", "#2", "#3", "#11", "#20", "#16"]
TRAIN_B = ["#1", "#2", "#3", "#11", "#20", "#12"]

xa = fold(2.95, "Pli A", TRAIN_A, "#12", "R² = +0,50")
xb = fold(1.95, "Pli B", TRAIN_B, "#16", "R² = +0,07")

# légende des rôles, au-dessus des chips (texte direct, pas de croisement)
ax.text(1.45, 3.85, "entraînement : les autres essais (+ auxiliaires sous-échantillonnés)",
        ha="left", fontsize=9.3, color=MUTED)
ax.text(xa + CW / 2, 3.85, "essai testé,\njamais vu", ha="center", fontsize=9.3,
        color=TEAL, fontweight="bold", linespacing=1.3)

# moyenne, en bas : la formule reprend les deux valeurs, aucun connecteur
# (pas de trait qui risquerait de croiser les R²)
ax.add_patch(mp.FancyBboxPatch((2.6, 0.30), 7.4, 0.95, boxstyle="round,pad=0.06",
                               fc="#FDF3EA", ec=RUST, lw=1.4))
ax.text(6.3, 0.775, "moyenne  =  ( +0,50  +  0,07 ) / 2  ≈  +0,29",
        ha="center", va="center", fontsize=15.5, color=RUST, fontweight="bold")

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
