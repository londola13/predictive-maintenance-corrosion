"""Figure II.1 — Architecture boucle intégrée Sonde → Supabase → Streamlit (module GMAO maison).

Architecture RÉELLE : aucun CMMS externe (GLPI). Les ordres de travail sont générés
par un module GMAO maison dans l'application Streamlit et persistés dans Supabase
(table cr_work_orders). La seule API REST est celle de Supabase (PostgREST).
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mp

fig, ax = plt.subplots(figsize=(9, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 13)
ax.axis('off')


def box(x, y, w, h, text, color):
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                   linewidth=1.6, edgecolor='black', facecolor=color))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=10.5, family='serif')


def arrow(x1, y1, x2, y2, label='', style='-|>', dx=0.18, dy=0.0):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color='black', lw=1.6, mutation_scale=18))
    if label:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, fontsize=9.3,
                family='serif', style='italic')


# --- Boîtes ---
box(0.4, 10.6, 3.3, 1.6, "ESP32\n(sonde ER + HX711 + DS18B20)", "#FFE8B0")
box(5.9, 10.3, 3.7, 2.0, "Base de données Supabase\n(PostgreSQL)\nmesures · prédictions · OT", "#CDE8FF")
box(2.4, 5.3, 5.0, 3.5,
    "Application Streamlit\n(frontend + dashboard)\n\nPipeline ML (XGBoost · SHAP · diagnostic)\n\nModule GMAO maison\n(ordres de travail · KPIs)", "#D8F0D0")
box(3.0, 1.8, 4.0, 1.4, "Technicien (web / mobile)", "#EADBFF")

# --- Flèches ---
arrow(2.0, 10.6, 6.3, 11.2, 'HTTPS POST')                                   # ESP32 -> Supabase
arrow(7.4, 10.3, 6.0, 8.8, 'REST Supabase\n(lecture mesures ·\nécriture OT)',
      style='<|-|>', dx=0.25)                                               # Supabase <-> Streamlit
arrow(4.9, 5.3, 4.9, 3.2, 'ordre de travail /\nnotification')               # Streamlit -> Technicien

ax.set_title("Figure II.1 — Architecture de la boucle intégrée\n"
             "Sonde ER → Supabase → Streamlit (module GMAO maison)",
             fontsize=12, family='serif', pad=15)

plt.tight_layout()
plt.savefig('fig_ii1_architecture.png', dpi=200, bbox_inches='tight', facecolor='white')
print("OK")
