"""Génère toutes les figures structurelles du mémoire (hors résultats expérimentaux)."""
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import numpy as np

SERIF = {'family': 'serif'}


def save(fig, name):
    fig.savefig(name, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure II.1 — Architecture intégrée (déjà présente, conservée)
# ─────────────────────────────────────────────────────────────────────────────
def fig_ii1_architecture():
    fig, ax = plt.subplots(figsize=(9, 11))
    ax.set_xlim(0, 10); ax.set_ylim(0, 14); ax.axis('off')

    def box(x, y, w, h, t, c):
        ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                       linewidth=1.6, edgecolor='black', facecolor=c))
        ax.text(x + w/2, y + h/2, t, ha='center', va='center', fontsize=10.5, **SERIF)

    def arr(x1, y1, x2, y2, lab=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='-|>', color='black', lw=1.6, mutation_scale=18))
        if lab:
            ax.text((x1+x2)/2 + 0.15, (y1+y2)/2, lab, fontsize=9.5, style='italic', **SERIF)

    box(0.5, 11.6, 3.2, 1.6, "ESP32\n(sonde ER + HX711 + DS18B20)", "#FFE8B0")
    box(6.0, 11.6, 3.5, 1.6, "Base de données\nSupabase (PostgreSQL)", "#CDE8FF")
    box(3.0, 7.8, 4.0, 2.4, "Application Streamlit\n(frontend + dashboard)\n\nPipeline ML\n(XGBoost · SHAP · diagnostic)", "#D8F0D0")
    box(3.0, 4.4, 4.0, 1.8, "GLPI (CMMS open-source)\nTickets · Work Orders · KPIs", "#FFD6CC")
    box(3.0, 1.2, 4.0, 1.4, "Technicien (web / mobile)", "#EADBFF")
    arr(2.1, 11.6, 6.5, 12.4, 'HTTPS POST')
    arr(7.7, 11.6, 5.8, 10.2, 'lecture SQL')
    arr(5.0, 7.8, 5.0, 6.2, 'POST /apirest.php/Ticket\n(si alerte critique)')
    arr(5.0, 4.4, 5.0, 2.6, 'notification')

    save(fig, 'fig_ii1_architecture.png')


# ─────────────────────────────────────────────────────────────────────────────
# Figure II.2 — Pont de Wheatstone instrumenté HX711
# ─────────────────────────────────────────────────────────────────────────────
def fig_ii2_wheatstone():
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')

    # Losange du pont
    A = (5, 7); B = (8, 4); C = (5, 1); D = (2, 4)
    pts = [A, B, C, D, A]
    xs, ys = zip(*pts)
    ax.plot(xs, ys, 'k-', lw=2)

    # Résistances (rectangles sur les branches)
    def res(p1, p2, label):
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        ax.add_patch(mp.Rectangle((mx-0.35, my-0.22), 0.7, 0.44,
                                  facecolor='white', edgecolor='black', lw=1.5, zorder=3))
        ax.text(mx, my, label, ha='center', va='center', fontsize=10, zorder=4, **SERIF)

    res(A, B, "R₂\n10 Ω")
    res(B, C, "R_REF\n0,5 Ω")
    res(C, D, "Rx\n(fil Fe)")
    res(D, A, "R₁\n10 Ω")

    # Alim en haut
    ax.plot([A[0], A[0]], [A[1], A[1]+0.6], 'k-', lw=1.5)
    ax.text(A[0]+0.2, A[1]+0.35, "+ V_exc (3,3 V)", fontsize=10, **SERIF)
    # GND en bas
    ax.plot([C[0], C[0]], [C[1]-0.6, C[1]], 'k-', lw=1.5)
    ax.text(C[0]-0.3, C[1]-0.4, "GND", ha='right', fontsize=10, **SERIF)

    # HX711 ADC à droite
    ax.add_patch(mp.FancyBboxPatch((8.6, 3.2), 1.3, 1.6, boxstyle="round,pad=0.05",
                                   facecolor="#CDE8FF", edgecolor='black', lw=1.5))
    ax.text(9.25, 4.0, "HX711\n24 bits\n(gain 128)", ha='center', va='center', fontsize=9.5, **SERIF)

    # Connexions différentielles vers HX711
    ax.plot([B[0], 8.6], [B[1]+0.2, 4.5], 'b-', lw=1.5)
    ax.plot([D[0], 8.6], [D[1]-0.2, 3.5], 'b-', lw=1.5)
    ax.text(7.5, 4.85, "A+", fontsize=9, color='blue', **SERIF)
    ax.text(5.0, 3.0, "A− (vers HX711)", fontsize=9, color='blue', **SERIF)

    # ESP32 à droite
    ax.add_patch(mp.FancyBboxPatch((8.4, 0.8), 1.7, 1.6, boxstyle="round,pad=0.05",
                                   facecolor="#FFE8B0", edgecolor='black', lw=1.5))
    ax.text(9.25, 1.6, "ESP32\nDevKit V1", ha='center', va='center', fontsize=10, **SERIF)
    ax.annotate('', xy=(9.25, 2.4), xytext=(9.25, 3.2),
                arrowprops=dict(arrowstyle='-|>', color='black', lw=1.5))
    ax.text(9.5, 2.8, "DOUT/SCK", fontsize=8.5, **SERIF)

    # R_serie sur l'alim
    ax.add_patch(mp.Rectangle((A[0]-0.3, A[1]+0.7), 0.6, 0.3,
                              facecolor='white', edgecolor='black', lw=1.5))
    ax.text(A[0], A[1]+0.85, "R_série 100 Ω", ha='center', fontsize=9, **SERIF)

    save(fig, 'fig_ii2_wheatstone.png')


# ─────────────────────────────────────────────────────────────────────────────
# Figure II.3 — Cycle ESP32 deep sleep pulsé
# ─────────────────────────────────────────────────────────────────────────────
def fig_ii3_cycle_esp32():
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4); ax.axis('off')

    steps = [
        ("Lecture HX711\n(moy. 10 éch.)\n→ Rx", "#D8F0D0"),
        ("Lecture DS18B20\n(12 bits)\n→ T", "#D8F0D0"),
        ("Wi-Fi +\nHTTPS POST\nSupabase", "#CDE8FF"),
        ("Temporisation\n30 s", "#EADBFF"),
    ]
    n = len(steps)
    w, h = 2.1, 1.6
    gap = 0.35
    x0 = 1.3
    y0 = 1.4

    for i, (t, c) in enumerate(steps):
        x = x0 + i*(w+gap)
        ax.add_patch(mp.FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.05",
                                       linewidth=1.5, edgecolor='black', facecolor=c))
        ax.text(x + w/2, y0 + h/2, t, ha='center', va='center', fontsize=9.5, **SERIF)
        if i < n-1:
            ax.annotate('', xy=(x+w+gap, y0+h/2), xytext=(x+w, y0+h/2),
                        arrowprops=dict(arrowstyle='-|>', color='black', lw=1.4))

    # Boucle de retour
    last_x = x0 + (n-1)*(w+gap) + w/2
    first_x = x0 + w/2
    ax.annotate('', xy=(first_x, y0-0.05), xytext=(last_x, y0-0.05),
                arrowprops=dict(arrowstyle='-|>', color='gray', lw=1.3,
                                connectionstyle="arc3,rad=-0.25"))
    ax.text((first_x+last_x)/2, 0.4, "cycle = 30 secondes (acquisition continue)", ha='center',
            fontsize=10, style='italic', color='gray', **SERIF)

    save(fig, 'fig_ii3_cycle_esp32.png')


# ─────────────────────────────────────────────────────────────────────────────
# Figure II.4 — Pipeline de traitement des données (5 étapes)
# ─────────────────────────────────────────────────────────────────────────────
def fig_ii4_pipeline():
    fig, ax = plt.subplots(figsize=(11, 3.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 3.5); ax.axis('off')

    steps = [
        ("1. Acquisition\nSupabase\n→ DataFrame", "#CDE8FF"),
        ("2. Nettoyage\nIQR + Savitzky-\nGolay", "#FFE8B0"),
        ("3. Compensation\nthermique\n(α_Fe)", "#D8F0D0"),
        ("4. Feature\nengineering\n(10 features)", "#FFD6CC"),
        ("5. Modèle\nXGBoost\nCR + RUL + SHAP", "#EADBFF"),
    ]
    n = len(steps)
    w, h = 2.0, 1.8
    gap = 0.25
    x0 = 0.4
    y0 = 0.8

    for i, (t, c) in enumerate(steps):
        x = x0 + i*(w+gap)
        ax.add_patch(mp.FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.06",
                                       linewidth=1.5, edgecolor='black', facecolor=c))
        ax.text(x + w/2, y0 + h/2, t, ha='center', va='center', fontsize=10, **SERIF)
        if i < n-1:
            ax.annotate('', xy=(x+w+gap, y0+h/2), xytext=(x+w, y0+h/2),
                        arrowprops=dict(arrowstyle='-|>', color='black', lw=1.5))

    save(fig, 'fig_ii4_pipeline.png')


# ─────────────────────────────────────────────────────────────────────────────
# Figure C.1 (Annexe C) — Schéma de câblage de la sonde ER complet
# ─────────────────────────────────────────────────────────────────────────────
def fig_c1_cablage():
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_xlim(0, 12); ax.set_ylim(0, 10); ax.axis('off')

    # ESP32
    ax.add_patch(mp.FancyBboxPatch((0.5, 4), 2.5, 4, boxstyle="round,pad=0.08",
                                   facecolor="#FFE8B0", edgecolor='black', lw=1.8))
    ax.text(1.75, 7.6, "ESP32\nDevKit V1", ha='center', fontsize=11, weight='bold', **SERIF)
    pins_esp = [("3V3", 7.0), ("GND", 6.5), ("GPIO 21 (DOUT)", 6.0),
                ("GPIO 22 (SCK)", 5.5), ("GPIO 19 (1-Wire)", 5.0), ("GND", 4.5)]
    for label, y in pins_esp:
        ax.plot([3.0, 3.3], [y, y], 'k-', lw=1.3)
        ax.text(2.85, y, label, ha='right', va='center', fontsize=9, **SERIF)

    # HX711
    ax.add_patch(mp.FancyBboxPatch((4.5, 5), 2.0, 2.5, boxstyle="round,pad=0.08",
                                   facecolor="#CDE8FF", edgecolor='black', lw=1.8))
    ax.text(5.5, 7.1, "HX711\n24 bits (gain 64)", ha='center', fontsize=10.5, weight='bold', **SERIF)
    pins_hx = [("VCC", 6.5), ("GND", 6.2), ("DT", 5.9), ("SCK", 5.6),
               ("A+", 5.3), ("A−", 5.0)]
    for label, y in pins_hx:
        ax.text(4.65, y, label, ha='left', va='center', fontsize=9, **SERIF)
        ax.plot([4.45, 4.5], [y, y], 'k-', lw=1.2)

    # Connexions ESP32 ↔ HX711
    ax.plot([3.3, 4.45], [6.0, 5.9], 'b-', lw=1.4)  # DOUT → DT
    ax.plot([3.3, 4.45], [5.5, 5.6], 'b-', lw=1.4)  # SCK
    ax.plot([3.3, 4.45], [7.0, 6.5], 'r-', lw=1.4)  # 3V3 → VCC
    ax.plot([3.3, 4.45], [6.5, 6.2], 'k-', lw=1.4)  # GND

    # ── Montage série : 3V3 → R_shunt → [fil Fe] → R_lift → GND ──
    yb = 6.6
    x3, xs1, xs2, xAp, xAm, xl1, xl2, xg = 7.3, 7.8, 8.6, 9.0, 10.3, 10.7, 11.5, 11.9
    ax.plot([x3, xg], [yb, yb], 'k-', lw=1.4, zorder=1)
    ax.plot([x3, x3], [yb, yb+0.45], 'r-', lw=1.6)
    ax.text(x3, yb+0.62, "+3,3 V", ha='center', color='red', fontsize=9, **SERIF)
    ax.add_patch(mp.Rectangle((xs1, yb-0.18), xs2-xs1, 0.36, facecolor='white',
                              edgecolor='black', lw=1.4, zorder=3))
    ax.text((xs1+xs2)/2, yb+0.5, "R_shunt\n970 Ω", ha='center', fontsize=8.5, **SERIF)
    ax.plot([xAp, xAm], [yb, yb], color='#E08A1E', lw=4.5, zorder=2)
    ax.text((xAp+xAm)/2, yb-0.5, "Fil de fer (Rx)", ha='center', color='#E08A1E', fontsize=9, **SERIF)
    for xn, lab in [(xAp, "A+"), (xAm, "A−")]:
        ax.plot(xn, yb, 'ko', ms=4, zorder=4)
        ax.text(xn, yb+0.24, lab, ha='center', color='blue', fontsize=8.5, **SERIF)
    ax.add_patch(mp.Rectangle((xl1, yb-0.18), xl2-xl1, 0.36, facecolor='white',
                              edgecolor='black', lw=1.4, zorder=3))
    ax.text((xl1+xl2)/2, yb+0.5, "R_lift\n970 Ω", ha='center', fontsize=8.5, **SERIF)
    ax.plot([xg, xg], [yb, yb-0.45], 'k-', lw=1.6)
    ax.text(xg, yb-0.62, "GND", ha='center', fontsize=9, **SERIF)
    # Connexions A+/A− → HX711
    ax.plot([xAp, 6.5], [yb, 5.3], 'b-', lw=1.3, zorder=1)
    ax.plot([xAm, 6.5], [yb, 5.0], 'b-', lw=1.3, zorder=1)

    # DS18B20 (en bas)
    ax.add_patch(mp.FancyBboxPatch((5.0, 1.5), 2.0, 1.3, boxstyle="round,pad=0.08",
                                   facecolor="#D8F0D0", edgecolor='black', lw=1.8))
    ax.text(6.0, 2.4, "DS18B20\n(1-Wire)", ha='center', fontsize=10.5, weight='bold', **SERIF)
    pins_ds = [("VCC", 2.2), ("DQ", 1.95), ("GND", 1.7)]
    for label, y in pins_ds:
        ax.text(5.15, y, label, ha='left', va='center', fontsize=8.5, **SERIF)
    # Pull-up 4.7k entre VCC et DQ
    ax.add_patch(mp.Rectangle((4.0, 1.85), 0.5, 0.25, facecolor='white',
                              edgecolor='black', lw=1.2))
    ax.text(4.25, 1.97, "4,7 kΩ", ha='center', fontsize=8, **SERIF)
    ax.plot([4.0, 3.5, 3.5, 5.0], [1.97, 1.97, 2.2, 2.2], 'k-', lw=1.2)  # pull-up
    ax.plot([3.3, 5.0], [5.0, 1.95], 'g-', lw=1.3)  # GPIO4 → DQ

    # Cellule de mesure (récipient HDPE)
    ax.add_patch(mp.FancyBboxPatch((9.5, 2.0), 2.0, 2.5, boxstyle="round,pad=0.08",
                                   facecolor="#F5E5D5", edgecolor='black', lw=1.8))
    ax.text(10.5, 4.2, "Bécher\n(HCl, bain 30 °C)", ha='center', fontsize=10, weight='bold', **SERIF)
    ax.text(10.5, 3.2, "Fil Fe (Rx)\n+ DS18B20\nimmergés", ha='center', fontsize=9, **SERIF)
    # Liaisons cellule → fil Fe (Rx) et DS18B20 (ancrée près de A−, à l'écart du label "Fil de fer (Rx)")
    ax.annotate('', xy=(xAm - 0.1, yb - 0.1), xytext=(10.5, 4.5),
                arrowprops=dict(arrowstyle='-', color='gray', lw=1.0, ls='--'))
    ax.annotate('', xy=(7.0, 2.1), xytext=(9.5, 2.8),
                arrowprops=dict(arrowstyle='-', color='gray', lw=1.0, ls='--'))

    save(fig, 'fig_c1_cablage.png')


# ─────────────────────────────────────────────────────────────────────────────
# Figure F.1 (Annexe F) — Schéma ERD base de données Supabase
# ─────────────────────────────────────────────────────────────────────────────
def fig_f1_erd():
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')

    def tab(x, y, w, h, name, fields, color):
        ax.add_patch(mp.Rectangle((x, y), w, h, facecolor=color, edgecolor='black', lw=1.6))
        ax.add_patch(mp.Rectangle((x, y+h-0.45), w, 0.45, facecolor='#444', edgecolor='black', lw=1.6))
        ax.text(x+w/2, y+h-0.22, name, ha='center', va='center', color='white',
                fontsize=10.5, weight='bold', **SERIF)
        # espacement des champs calculé pour tenir dans la boîte, quel que soit leur nombre
        # (évite tout débordement du dernier champ sous le cadre)
        step = min(0.28, (h - 0.85) / max(len(fields) - 1, 1))
        for i, f in enumerate(fields):
            ax.text(x+0.1, y+h-0.7-i*step, f, fontsize=8.5, **SERIF)
        return (x, y, w, h)

    def link(t1, t2, side1='right', side2='left'):
        x1, y1, w1, h1 = t1; x2, y2, w2, h2 = t2
        sx = x1+w1 if side1 == 'right' else x1
        sy = y1+h1/2
        ex = x2 if side2 == 'left' else x2+w2
        ey = y2+h2/2
        ax.plot([sx, ex], [sy, ey], 'k-', lw=1.2)
        # crow's foot simple : petit cercle côté "many"
        ax.plot(ex, ey, 'ko', markersize=5, markerfacecolor='white')

    def link_over(t1, t2, stub_x, bus_y=9.85):
        """Route en L par-dessus les tables intermédiaires (évite de traverser leurs champs)."""
        x1, y1, w1, h1 = t1; x2, y2, w2, h2 = t2
        sx, sy = x1 + w1, y1 + h1 / 2
        tx, ty = x2 + w2 / 2, y2 + h2
        ax.plot([sx, stub_x, stub_x, tx, tx], [sy, sy, bus_y, bus_y, ty], 'k-', lw=1.2)
        ax.plot(tx, ty, 'ko', markersize=5, markerfacecolor='white')

    assets = tab(0.5, 7.0, 2.6, 2.5, "assets",
                 ["id (PK)", "nom", "type", "localisation", "date_install",
                  "cr_seuil_orange", "cr_seuil_rouge", "rul_seuil_orange"], "#FFF4D6")
    measurements = tab(4.5, 7.5, 2.6, 2.0, "measurements",
                       ["id (PK)", "asset_id (FK)", "timestamp_s", "vdiff_v",
                        "rx_ohm", "temp_c", "delta_r_per_h"], "#CDE8FF")
    predictions = tab(8.5, 7.5, 2.6, 2.0, "predictions",
                      ["id (PK)", "asset_id (FK)", "timestamp",
                       "cr_predit", "rul_predit", "diagnostic",
                       "shap_top1/2/3"], "#D8F0D0")
    alerts = tab(11.5, 7.5, 2.4, 2.0, "alerts",
                 ["id (PK)", "asset_id (FK)", "niveau",
                  "type", "message", "ack_at", "resolved_at"], "#FFD6CC")
    work_orders = tab(8.5, 4.0, 2.6, 2.5, "work_orders",
                      ["id (PK)", "alert_id (FK)", "asset_id (FK)",
                       "statut", "priorite", "technicien",
                       "description", "ferme_le"], "#EADBFF")
    interventions = tab(4.5, 4.0, 2.6, 2.5, "interventions",
                        ["id (PK)", "work_order_id (FK)", "asset_id (FK)",
                         "type", "technicien", "duree_min",
                         "cout_fcfa", "photo_url"], "#FFE2E2")
    inhibitor = tab(0.5, 4.0, 2.6, 2.0, "inhibitor_doses",
                    ["id (PK)", "asset_id (FK)",
                     "intervention_id (FK)", "produit",
                     "concentration_pct", "volume_ml"], "#E5E5FF")
    kpi = tab(4.5, 0.8, 4.0, 2.2, "kpi_maintenance (vue)",
              ["asset_id", "ot_fermes", "mttr_h",
               "mtbf_h", "eta_inhibition_pct",
               "fausses_alertes_pct"], "#F5F0E5")

    # Liaisons (FK)
    link(assets, measurements, 'right', 'left')
    link_over(assets, predictions, stub_x=3.3)   # évite de traverser measurements
    link_over(assets, alerts, stub_x=3.5)        # évite de traverser measurements + predictions
    link(alerts, work_orders, 'left', 'right')
    link(work_orders, interventions, 'left', 'right')
    link(interventions, inhibitor, 'left', 'right')
    link(assets, inhibitor, 'left', 'left')
    link(work_orders, kpi, 'left', 'right')

    save(fig, 'fig_f1_erd.png')


if __name__ == '__main__':
    fig_ii1_architecture()
    fig_ii2_wheatstone()
    fig_ii3_cycle_esp32()
    fig_ii4_pipeline()
    fig_c1_cablage()
    fig_f1_erd()
    print("OK — 6 figures générées")
