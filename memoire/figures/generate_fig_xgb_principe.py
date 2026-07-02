# -*- coding: utf-8 -*-
"""Schéma pédagogique (slide) : principe du gradient boosting (XGBoost).

Arbres construits en séquence : chaque arbre apprend les ERREURS (résidus) du
cumul précédent ; la prédiction finale est la somme des petites corrections.
Hyperparamètres réels du mémoire (Tableau II.6) : 500 arbres, profondeur 4,
pas d'apprentissage 0,05. Pas de titre gravé : porté par la slide.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mp

INK, MUTED, RUST, TEAL = "#202B31", "#6B7A82", "#C9601A", "#0A9498"
PAPER, CHIP = "#FFFFFF", "#EDEAE3"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_xgb_principe.png")

fig, ax = plt.subplots(figsize=(12.4, 3.8))
ax.set_xlim(0, 12.4); ax.set_ylim(0, 3.75); ax.axis("off")


def rbox(x, y, w, h, fc=PAPER, ec=INK, lw=1.4):
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                   fc=fc, ec=ec, lw=lw))


def tree(cx, cy, col=MUTED, s=0.30):
    """Petit glyphe d'arbre binaire (racine + 2 niveaux)."""
    r = (cx, cy + s)
    n1, n2 = (cx - s, cy), (cx + s, cy)
    leaves = [(cx - 1.5 * s, cy - s), (cx - 0.5 * s, cy - s),
              (cx + 0.5 * s, cy - s), (cx + 1.5 * s, cy - s)]
    for a, b in [(r, n1), (r, n2), (n1, leaves[0]), (n1, leaves[1]),
                 (n2, leaves[2]), (n2, leaves[3])]:
        ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=1.3, zorder=2)
    for p in [r, n1, n2] + leaves:
        ax.plot(*p, "o", color=col, ms=5.5, zorder=3)


def flow(x1, x2, y):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5, mutation_scale=16))


# ── Données (entrée) ─────────────────────────────────────────────
rbox(0.25, 1.55, 2.1, 1.7, fc=CHIP, ec=MUTED)
ax.text(1.30, 2.88, "Données des essais", ha="center", fontsize=10.5,
        color=INK, fontweight="bold")
ax.text(1.30, 2.42, "résistance R(t)\ntempérature T\ntemps d'immersion", ha="center",
        va="center", fontsize=8.8, color=MUTED, linespacing=1.5)
ax.text(1.30, 1.78, "cible : CR mesuré", ha="center", fontsize=8.8, color=TEAL,
        fontweight="bold")

flow(2.50, 3.10, 2.4)

# ── Arbres en séquence ───────────────────────────────────────────
def stage(x, num, note):
    rbox(x, 1.55, 1.85, 1.7)
    ax.text(x + 0.925, 2.95, f"Arbre {num}", ha="center", fontsize=10.5,
            color=INK, fontweight="bold")
    tree(x + 0.925, 2.35)
    ax.text(x + 0.925, 1.78, note, ha="center", fontsize=8.6, color=MUTED)

stage(3.10, 1, "prédiction grossière")
stage(5.85, 2, "petite correction")
stage(8.60, 3, "petite correction")

# flèches entre arbres, avec la mention résidus SOUS la flèche (jamais dessus)
for x1, x2, lab in [(4.95, 5.85, "ses erreurs (résidus)\ndeviennent la cible"),
                    (7.70, 8.60, "idem, sur les erreurs\nrestantes")]:
    flow(x1, x2, 2.4)
    ax.text((x1 + x2) / 2, 1.30, lab, ha="center", va="top", fontsize=8.4,
            color=RUST, linespacing=1.4)

ax.text(10.62, 2.40, "… ×500", ha="center", va="center", fontsize=13,
        color=MUTED, fontweight="bold", style="italic")

# ── Somme finale ─────────────────────────────────────────────────
rbox(0.9, 0.18, 10.6, 0.72, fc="#16252E", ec="#16252E")
ax.text(6.2, 0.54, "CR prédit  =  somme des 500 petites corrections"
        "      (profondeur 4  ·  pas d'apprentissage 0,05)",
        ha="center", va="center", fontsize=11, color="white")
ax.annotate("", xy=(6.2, 0.98), xytext=(6.2, 1.42),
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5, mutation_scale=16))

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
