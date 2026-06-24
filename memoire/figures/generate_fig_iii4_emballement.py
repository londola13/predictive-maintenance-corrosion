"""Figure III.7 — Fin d'essai (échelle log) : divergence géométrique R ∝ 1/section pendant
l'amincissement final du fil (emballement), jusqu'à la rupture / saturation. Run #1 (essai propre,
22 h, sans queue parasite). La conduction résiduelle post-rupture (électrolyte + dernier filament)
est décrite dans le texte (§III.4.1 / §III.6.4) — non extrapolée graphiquement.

Requiert SUPABASE_KEY dans l'environnement.
"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

import pandas as pd
import matplotlib.pyplot as plt
from src.etl.fetch_supabase import fetch_run

RUN = "d6e31719-c3fb-4797-aa0b-65c4e605002a"  # Run #1 (HCl brut, 22 h, cycle complet propre)

raw = fetch_run(RUN)
rx = pd.to_numeric(raw["rx_ohm"], errors="coerce")
raw = raw[rx > 0].reset_index(drop=True)
rx = pd.to_numeric(raw["rx_ohm"], errors="coerce").reset_index(drop=True)
th = (raw["timestamp_s"].astype(float) - raw["timestamp_s"].astype(float).min()) / 3600.0

# Tronque au pic (rupture) pour exclure tout point parasite post-saturation
imax = int(rx.idxmax())
thp = th.iloc[:imax + 1].reset_index(drop=True)
rxp = rx.iloc[:imax + 1].reset_index(drop=True)

mx = float(rxp.max())
R0 = float(rxp.iloc[:10].median())


def t_at(thr):
    m = rxp >= thr
    return float(thp.iloc[int(m.idxmax())]) if m.any() else float(thp.iloc[-1])


t_emb = t_at(4 * R0)      # début d'emballement (~4·R0)
t_rupt = float(thp.iloc[-1])
# fraction de section restante au pic : R0/R
sect_fin = 100.0 * R0 / mx

fig, ax = plt.subplots(figsize=(9.4, 5.7))
ax.plot(thp, rxp, color="#1f4e79", lw=1.9, zorder=4)
ax.set_yscale("log")

ax.axvspan(0, t_emb, color="#d8f0d0", alpha=0.55, label="induction + croissance")
ax.axvspan(t_emb, t_rupt, color="#ffe0a8", alpha=0.7,
           label=r"emballement : $R \propto 1/\mathrm{section}$  (fil presque entièrement aminci)")

ax.axhline(R0, color="gray", ls=":", lw=1)
ax.text(0.2, R0 * 1.05, r"$R_0$", color="gray", fontsize=10)

ax.annotate(f"Rupture / saturation\n(section restante ≈ {sect_fin:.0f} % → circuit ouvert)",
            xy=(t_rupt, mx), xytext=(t_rupt - 0.34 * t_rupt, mx * 0.55),
            fontsize=9.4, family="serif", ha="center",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.3))
ax.annotate("Le fil s'amincit : la section chute en $r^2$,\ndonc $R$ s'emballe en $1/r^{3}$",
            xy=(0.65 * t_emb + 0.35 * t_rupt, 8 * R0),
            xytext=(0.2, mx * 0.6), fontsize=9.4, family="serif", ha="left",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.3))

# Encadré : mécanisme post-rupture (décrit, non extrapolé)
ax.text(0.98, 0.04,
        "Au-delà de la rupture mécanique, la conduction résiduelle\n"
        "(électrolyte HCl + dernier filament) maintient une résistance\n"
        "élevée et croissante jusqu'à l'ouverture franche du circuit\n"
        "(§III.4.1, §III.6.4).",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8.3, family="serif",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff3e0", edgecolor="#cc8800", lw=1))

ax.set_xlabel("Temps (h)", fontsize=11)
ax.set_ylabel(r"Résistance mesurée $R(t)$  (Ω, échelle log)", fontsize=11)
ax.set_title("Figure III.7 — Emballement géométrique de R en fin d'essai\n"
             "et rupture par disparition de la section (Run #1)",
             fontsize=12, family="serif")
ax.legend(loc="upper left", fontsize=8.8)
ax.grid(alpha=0.3, which="both")

plt.tight_layout()
plt.savefig("fig_iii4_emballement.png", dpi=200, bbox_inches="tight", facecolor="white")
print(f"OK — R0={R0:.2f} Ω, max={mx:.0f} Ω, section finale≈{sect_fin:.1f}%, t_emb={t_emb:.1f}h, t_rupt={t_rupt:.1f}h, n={len(rxp)}")
