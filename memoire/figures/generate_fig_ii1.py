"""Génère Figure II.1 — Architecture boucle intégrée Sonde → Supabase → Streamlit → CMMS."""
import matplotlib.pyplot as plt
import matplotlib.patches as mp

fig, ax = plt.subplots(figsize=(9, 11))
ax.set_xlim(0, 10); ax.set_ylim(0, 14)
ax.axis('off')

def box(x, y, w, h, text, color):
    r = mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                          linewidth=1.6, edgecolor='black', facecolor=color)
    ax.add_patch(r)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=10.5, family='serif')

def arrow(x1, y1, x2, y2, label=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='-|>', color='black', lw=1.6,
                                mutation_scale=18))
    if label:
        ax.text((x1+x2)/2 + 0.15, (y1+y2)/2, label, fontsize=9.5,
                family='serif', style='italic')

# --- Boîtes ---
box(0.5, 11.6, 3.2, 1.6,
    "ESP32\n(sonde ER + HX711 + DS18B20)", "#FFE8B0")

box(6.0, 11.6, 3.5, 1.6,
    "Base de données\nSupabase (PostgreSQL)", "#CDE8FF")

box(3.0, 7.8, 4.0, 2.4,
    "Application Streamlit\n(frontend + dashboard)\n\nPipeline ML\n(XGBoost · SHAP · diagnostic)", "#D8F0D0")

box(3.0, 4.4, 4.0, 1.8,
    "GLPI (CMMS open-source)\nTickets · Work Orders · KPIs",
    "#FFD6CC")

box(3.0, 1.2, 4.0, 1.4,
    "Technicien (web / mobile)", "#EADBFF")

# --- Flèches ---
arrow(2.1, 11.6, 6.5, 12.4, 'HTTPS POST')        # ESP32 -> Supabase
arrow(7.7, 11.6, 5.8, 10.2, 'lecture SQL')        # Supabase -> Streamlit
arrow(5.0, 7.8, 5.0, 6.2, 'POST /apirest.php/Ticket\n(si alerte critique)')
arrow(5.0, 4.4, 5.0, 2.6, 'notification')

ax.set_title("Figure II.1 — Architecture de la boucle intégrée\nSonde ER → Supabase → Streamlit → CMMS open-source",
             fontsize=12, family='serif', pad=15)

plt.tight_layout()
plt.savefig('fig_ii1_architecture.png', dpi=200, bbox_inches='tight', facecolor='white')
print("OK")
