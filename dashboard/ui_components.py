# -*- coding: utf-8 -*-
"""Composants visuels SCADA pour le dashboard de supervision.

Thème salle de contrôle : fond sombre, accents cyan/vert/ambre,
pastilles pulsantes, flux animés, jauges Plotly.
"""
import plotly.graph_objects as go
import streamlit as st

# Palette
BG       = "#0b0f19"
PANEL    = "#111827"
CYAN     = "#00d4ff"
VERT     = "#2ecc71"
AMBRE    = "#f39c12"
ROUGE    = "#e74c3c"
GRIS     = "#8b95a5"
BLANC    = "#e8edf4"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(17,24,39,0.55)",
    font=dict(color=BLANC, family="Segoe UI, sans-serif"),
    xaxis=dict(gridcolor="#1f2937", zerolinecolor="#1f2937"),
    yaxis=dict(gridcolor="#1f2937", zerolinecolor="#1f2937"),
    margin=dict(l=50, r=30, t=50, b=40),
)


def inject_css():
    st.markdown("""
<style>
/* ---------- fond général ---------- */
.stApp { background: linear-gradient(160deg, #0b0f19 0%, #0d1322 60%, #0b1626 100%); }
section[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1f2937; }

/* ---------- typographie ---------- */
h1, h2, h3 { color: #e8edf4 !important; letter-spacing: 0.5px; }
.scada-title {
  font-family: 'Consolas', 'Courier New', monospace;
  color: #00d4ff; font-size: 1.9rem; font-weight: 700;
  text-shadow: 0 0 18px rgba(0,212,255,0.45);
  letter-spacing: 2.5px; margin-bottom: 0;
}
.scada-sub { color: #8b95a5; font-size: 0.85rem; letter-spacing: 1.5px;
  text-transform: uppercase; margin-top: 2px; }

/* ---------- cartes KPI ---------- */
div[data-testid="stMetric"] {
  background: linear-gradient(145deg, #111827, #0d1424);
  border: 1px solid #1f2937; border-left: 3px solid #00d4ff;
  border-radius: 10px; padding: 14px 18px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.35);
}
div[data-testid="stMetric"] label { color: #8b95a5 !important;
  text-transform: uppercase; font-size: 0.72rem !important; letter-spacing: 1px; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
  color: #e8edf4 !important; font-family: 'Consolas', monospace; }

/* ---------- pastilles d'état ---------- */
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(46,204,113,0.65); }
  70%  { box-shadow: 0 0 0 11px rgba(46,204,113,0); }
  100% { box-shadow: 0 0 0 0 rgba(46,204,113,0); }
}
@keyframes pulseCyan {
  0%   { box-shadow: 0 0 0 0 rgba(0,212,255,0.65); }
  70%  { box-shadow: 0 0 0 9px rgba(0,212,255,0); }
  100% { box-shadow: 0 0 0 0 rgba(0,212,255,0); }
}
.dot { display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:7px; }
.dot-on   { background:#2ecc71; animation: pulse 1.8s infinite; }
.dot-cyan { background:#00d4ff; animation: pulseCyan 2s infinite; }
.dot-off  { background:#566173; }
.dot-warn { background:#f39c12; }

.badge {
  display:inline-flex; align-items:center; padding: 5px 14px;
  border-radius: 20px; font-family:'Consolas', monospace; font-size: 0.85rem;
  letter-spacing: 1.5px; font-weight: 600;
}
.badge-online  { background: rgba(46,204,113,0.12); color:#2ecc71; border:1px solid rgba(46,204,113,0.4); }
.badge-standby { background: rgba(139,149,165,0.10); color:#8b95a5; border:1px solid rgba(139,149,165,0.35); }

/* ---------- synoptique chaîne d'acquisition ---------- */
.chain { display:flex; align-items:center; justify-content:space-between;
  background: linear-gradient(145deg, #101826, #0c1320);
  border:1px solid #1f2937; border-radius:14px; padding: 26px 24px; margin: 6px 0 14px 0; }
.node { text-align:center; flex: 0 0 auto; min-width: 92px; }
.node-icon {
  width:54px; height:54px; margin: 0 auto 8px auto; border-radius: 12px;
  background: rgba(0,212,255,0.07); border: 1px solid rgba(0,212,255,0.35);
  display:flex; align-items:center; justify-content:center; font-size: 1.5rem;
  box-shadow: inset 0 0 16px rgba(0,212,255,0.07);
}
.node-label { color:#e8edf4; font-size:0.78rem; font-weight:600; letter-spacing:0.5px; }
.node-detail { color:#8b95a5; font-size:0.66rem; }

.link { flex:1 1 auto; height: 3px; margin: 0 8px; position:relative; top: -16px;
  background: linear-gradient(90deg, rgba(0,212,255,0.12), rgba(0,212,255,0.3), rgba(0,212,255,0.12));
  border-radius: 2px; overflow: visible; }
@keyframes flow { 0% { left: -8%; opacity:0; } 12% {opacity:1;} 88% {opacity:1;} 100% { left: 100%; opacity:0; } }
.packet { position:absolute; top:-3px; width:9px; height:9px; border-radius:50%;
  background:#00d4ff; box-shadow: 0 0 10px #00d4ff, 0 0 22px rgba(0,212,255,0.7);
  animation: flow 2.6s linear infinite; }
.packet.p2 { animation-delay: 0.9s; }
.packet.p3 { animation-delay: 1.7s; }

/* ---------- panneaux ---------- */
.panel {
  background: linear-gradient(145deg, #111827, #0d1424);
  border: 1px solid #1f2937; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
}
.panel-title { color:#00d4ff; font-family:'Consolas',monospace; font-size:0.8rem;
  letter-spacing:2px; text-transform:uppercase; margin-bottom:8px; }

/* tableau dataframe sombre */
div[data-testid="stDataFrame"] { border:1px solid #1f2937; border-radius:10px; }

/* divider */
hr { border-color:#1f2937 !important; }
</style>
""", unsafe_allow_html=True)


def header(titre: str, sous_titre: str, en_ligne: bool):
    badge = badge_statut(en_ligne)
    st.markdown(
        f"""
<div style="display:flex; justify-content:space-between; align-items:center;">
  <div>
    <p class="scada-title">{titre}</p>
    <p class="scada-sub">{sous_titre}</p>
  </div>
  <div>{badge}</div>
</div>
""", unsafe_allow_html=True)


def badge_statut(actif: bool) -> str:
    if actif:
        return '<span class="badge badge-online"><span class="dot dot-on"></span>ACQUISITION EN LIGNE</span>'
    return '<span class="badge badge-standby"><span class="dot dot-off"></span>STANDBY — AUCUN RUN ACTIF</span>'


def synoptique_chaine(acquisition_active: bool):
    """Synoptique animé : ESP32 -> capteurs -> Wi-Fi -> Supabase -> Pipeline -> ML -> Dashboard."""
    dot = "dot-on" if acquisition_active else "dot-cyan"
    packets = '<span class="packet"></span><span class="packet p2"></span><span class="packet p3"></span>'
    noeuds = [
        ("🌡️", "Sonde ER", "Fil fer + HX711 + DS18B20"),
        ("🔌", "ESP32", "Mesure 30 s · gain 64"),
        ("📶", "Wi-Fi", "HTTPS POST"),
        ("🗄️", "Supabase", "cr_measurements"),
        ("⚙️", "Pipeline", "Nettoyage · CR · RUL"),
        ("🧠", "XGBoost", "Prédiction CR"),
        ("🖥️", "Supervision", "Ce dashboard"),
    ]
    html = '<div class="chain">'
    for i, (icone, label, detail) in enumerate(noeuds):
        html += f"""
<div class="node">
  <div class="node-icon">{icone}</div>
  <div class="node-label"><span class="dot {dot}" style="width:8px;height:8px;"></span>{label}</div>
  <div class="node-detail">{detail}</div>
</div>"""
        if i < len(noeuds) - 1:
            html += f'<div class="link">{packets}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def jauge(valeur: float, titre: str, suffixe: str, vmax: float,
          seuils=(0.5, 0.8), inverse=False, hauteur=230) -> go.Figure:
    """Jauge SCADA. seuils = fractions de vmax (vert->ambre->rouge), inverse pour RUL."""
    s1, s2 = seuils[0] * vmax, seuils[1] * vmax
    if inverse:
        steps = [
            dict(range=[0, s1], color="rgba(231,76,60,0.30)"),
            dict(range=[s1, s2], color="rgba(243,156,18,0.25)"),
            dict(range=[s2, vmax], color="rgba(46,204,113,0.20)"),
        ]
    else:
        steps = [
            dict(range=[0, s1], color="rgba(46,204,113,0.20)"),
            dict(range=[s1, s2], color="rgba(243,156,18,0.25)"),
            dict(range=[s2, vmax], color="rgba(231,76,60,0.30)"),
        ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valeur,
        number=dict(suffix=f" {suffixe}", font=dict(color=BLANC, family="Consolas", size=26)),
        title=dict(text=titre.upper(), font=dict(color=GRIS, size=12, family="Consolas")),
        gauge=dict(
            axis=dict(range=[0, vmax], tickcolor=GRIS, tickfont=dict(color=GRIS, size=9)),
            bar=dict(color=CYAN, thickness=0.28),
            bgcolor="rgba(17,24,39,0.6)",
            borderwidth=1, bordercolor="#1f2937",
            steps=steps,
        ),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=hauteur)
    return fig


def panel(titre: str, contenu_html: str):
    st.markdown(
        f'<div class="panel"><div class="panel-title">{titre}</div>{contenu_html}</div>',
        unsafe_allow_html=True)
