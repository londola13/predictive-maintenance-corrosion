# -*- coding: utf-8 -*-
"""Schéma de principe du montage de mesure réel : 2 fils + shunt + R_lift.
Topologie : 3V3 -> R_shunt -> [A+] fil ER [A-] -> R_lift -> GND
HX711 (gain 64) mesure la chute de tension aux bornes du fil ; R = V/I.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

BLEU, ORANGE, VERT, GRIS, ROUGE = "#1f4e79", "#e08a1e", "#2e8b57", "#555", "#c0392b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

fig, ax = plt.subplots(figsize=(11, 6.2))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis("off")

def box(x, y, w, h, label, color, sub="", fc="white"):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                       ec=color, fc=fc, lw=2)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2 + (0.12 if sub else 0), label,
            ha="center", va="center", fontsize=10, fontweight="bold", color=color)
    if sub:
        ax.text(x + w/2, y + h/2 - 0.22, sub, ha="center", va="center",
                fontsize=8, color=GRIS)

def resistor(x, y, label):
    ax.add_patch(Rectangle((x, y-0.18), 1.1, 0.36, ec="black", fc="#f5f5f5", lw=1.5))
    ax.text(x + 0.55, y + 0.45, label, ha="center", fontsize=9, fontweight="bold")

def wire(x1, y1, x2, y2, color="black", lw=1.8):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw, solid_capstyle="round", zorder=1)

# ---- Ligne de courant principale (y = 5) ----
Y = 5.0
ax.text(0.5, Y+0.55, "3V3", ha="center", fontsize=10, fontweight="bold", color=ROUGE)
ax.plot(0.5, Y, "o", color=ROUGE, ms=8)
wire(0.5, Y, 2.0, Y)
resistor(2.0, Y, "R_shunt\n970 Ω")
wire(3.1, Y, 4.3, Y)
# noeud A+
ax.plot(4.3, Y, "o", color=BLEU, ms=7); ax.text(4.3, Y+0.35, "A+", ha="center", color=BLEU, fontweight="bold")
# fil ER (dans bécher)
wire(4.3, Y, 7.0, Y, color=ORANGE, lw=3)
ax.text(5.65, Y+0.32, "Fil de fer (sonde ER)", ha="center", color=ORANGE, fontsize=9, fontweight="bold")
# noeud A-
ax.plot(7.0, Y, "o", color=BLEU, ms=7); ax.text(7.0, Y+0.35, "A−", ha="center", color=BLEU, fontweight="bold")
wire(7.0, Y, 8.0, Y)
resistor(8.0, Y, "R_lift\n970 Ω")
wire(9.1, Y, 10.5, Y)
ax.plot(10.5, Y, "o", color="black", ms=8)
ax.text(10.5, Y+0.55, "GND", ha="center", fontsize=10, fontweight="bold")

# ---- Bécher HCl (englobe le fil) ----
ax.add_patch(FancyBboxPatch((4.05, 3.7), 3.2, 1.9, boxstyle="round,pad=0.02",
                            ec=VERT, fc="#e9f3ea", lw=1.5, zorder=0))
ax.text(5.65, 3.95, "Bécher — HCl (bain 30 °C)", ha="center", color=VERT, fontsize=8)
# DS18B20 dans le bécher
ax.plot(6.5, 4.4, "s", color=ROUGE, ms=9)
ax.text(6.78, 4.4, "DS18B20", ha="left", va="center", color=ROUGE, fontsize=7.5)

# ---- HX711 (mesure A+ / A-) ----
box(3.6, 6.4, 4.1, 1.0, "HX711  (ADC 24 bits, gain 64)", BLEU,
    sub="mesure V_sense = tension aux bornes du fil")
wire(4.3, Y, 4.3, 6.4, color=BLEU, lw=1.3)      # A+ -> HX711
wire(7.0, Y, 7.0, 6.4, color=BLEU, lw=1.3)      # A- -> HX711

# ---- ESP32 ----
box(0.4, 1.0, 3.2, 1.3, "ESP32", GRIS,
    sub="DOUT→21 · SCK→22 · 1-Wire→19")
# liaison logique HX711 <-> ESP32 (DOUT/SCK) : descente verticale à gauche du bécher (x < 4,05)
ax.plot([3.7, 3.7], [6.4, 2.3], color=GRIS, ls="--", lw=1.1, zorder=1)
ax.text(3.55, 3.5, "DOUT / SCK", color=GRIS, fontsize=7.5, rotation=90, ha="right", va="center")
# liaison DS18B20 -> ESP32 (1-Wire) : sortie verticale du bécher puis retour orthogonal
ax.plot([6.5, 6.5], [4.4, 1.65], color=ROUGE, ls=":", lw=1.1, zorder=1)
ax.plot([6.5, 3.6], [1.65, 1.65], color=ROUGE, ls=":", lw=1.1, zorder=1)
ax.text(6.65, 2.05, "1-Wire", color=ROUGE, fontsize=7.5, ha="left", va="center")
# alim ESP32 -> 3V3 et GND du circuit
wire(2.0, 2.3, 0.5, 2.3); wire(0.5, 2.3, 0.5, Y, color=ROUGE, lw=1.3)
wire(3.6, 1.3, 10.5, 1.3); wire(10.5, 1.3, 10.5, Y, color="black", lw=1.3)
ax.text(0.7, 3.5, "3V3", color=ROUGE, fontsize=7.5)
ax.text(10.2, 2.5, "GND", color=GRIS, fontsize=7.5)

# ---- Formules ----
ax.text(6, 0.45,
        r"$I = \dfrac{V_{CC}}{R_{shunt}+R_{lift}} \approx 1{,}78\ mA$        "
        r"$R_{fil} = \dfrac{V_{sense}}{I}\times k_{cal}$   (k = 33,7)",
        ha="center", fontsize=10, color="black")

ax.set_title("Montage de mesure de résistance — 2 fils + shunt + R_lift",
             fontsize=12, fontweight="bold", color=BLEU, pad=12)
fig.tight_layout()
out = "fig_montage_reel.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print("Schéma généré :", out)
