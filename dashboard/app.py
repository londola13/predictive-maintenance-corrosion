"""
app.py — Dashboard Maintenance Prédictive Corrosion
Lancer : streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

st.set_page_config(
    page_title="Maintenance Prédictive — Corrosion Pipeline",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Maintenance Prédictive — Corrosion & Érosion/Corrosion")
st.caption("Pipelines pétroliers | Prototype M2 — Modèle de Waard-Milliams")

# ── Sidebar : saisie paramètres ──────────────────────────────────────────────
st.sidebar.header("⚙️ Paramètres du pipeline")

temperature     = st.sidebar.slider("Température (°C)",       20.0, 120.0, 60.0)
pression        = st.sidebar.slider("Pression (bar)",          10.0, 150.0, 50.0)
pH              = st.sidebar.slider("pH",                       4.5,   8.5,  6.5)
vitesse_fluide  = st.sidebar.slider("Vitesse fluide (m/s)",    0.5,  10.0,  2.0)
pco2            = st.sidebar.slider("Pression partielle CO2 (bar)", 0.1, 10.0, 1.0)
teneur_eau      = st.sidebar.slider("Teneur en eau (%)",       0.0, 100.0, 20.0)
concentration_cl= st.sidebar.number_input("Chlorures (mg/L)",  0, 50000, 5000)
age_pipeline    = st.sidebar.slider("Âge pipeline (ans)",      0.0,  30.0,  5.0)
epaisseur_paroi = st.sidebar.slider("Épaisseur paroi (mm)",    6.0,  25.0, 12.0)
inhibiteur      = st.sidebar.selectbox("Inhibiteur de corrosion", [0, 1],
                                        format_func=lambda x: "Oui" if x else "Non")

# ── Calcul prédiction (modèle physique — avant modèles ML entraînés) ─────────
def predict_corrosion(T, pco2, v, inhibiteur):
    rate = (
        0.0315
        * (10 ** (0.67 * np.log10(pco2)))
        * (10 ** (-1710 / (T + 273.15) + 5.37))
        * (v ** 0.146)
        * (1 - 0.7 * inhibiteur)
    )
    return max(0.01, min(5.0, rate))

taux = predict_corrosion(temperature, pco2, vitesse_fluide, inhibiteur)
epaisseur_min = 3.0
rul = max(0, (epaisseur_paroi - epaisseur_min) / taux)
risque = "Élevé" if taux >= 0.5 else ("Moyen" if taux >= 0.1 else "Faible")
couleur = {"Faible": "green", "Moyen": "orange", "Élevé": "red"}[risque]

# ── Layout : 3 KPIs ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Taux de corrosion", f"{taux:.4f} mm/an")
col2.metric("Durée de vie résiduelle (RUL)", f"{rul:.1f} ans")
col3.metric("Niveau de risque", risque, delta=None)

st.markdown(f"### Risque : :{couleur}[**{risque}**]")

st.divider()

# ── Courbe de dégradation ─────────────────────────────────────────────────────
st.subheader("📉 Courbe de dégradation de l'épaisseur")
annees = np.linspace(0, min(rul * 1.5, 50), 100)
epaisseurs = epaisseur_paroi - taux * annees
epaisseurs = np.clip(epaisseurs, 0, epaisseur_paroi)

fig = go.Figure()
fig.add_trace(go.Scatter(x=annees, y=epaisseurs, mode='lines',
                          name='Épaisseur paroi', line=dict(color='steelblue', width=3)))
fig.add_hline(y=epaisseur_min, line_dash="dash", line_color="red",
              annotation_text="Seuil critique (3 mm)")
if rul > 0:
    fig.add_vline(x=rul, line_dash="dot", line_color="orange",
                  annotation_text=f"RUL = {rul:.1f} ans")
fig.update_layout(xaxis_title="Années", yaxis_title="Épaisseur (mm)",
                  height=400, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# ── Jauge risque ─────────────────────────────────────────────────────────────
st.subheader("🎯 Jauge de risque")
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=taux,
    title={'text': "Taux de corrosion (mm/an)"},
    gauge={
        'axis': {'range': [0, 5]},
        'bar': {'color': couleur},
        'steps': [
            {'range': [0, 0.1],  'color': '#d4edda'},
            {'range': [0.1, 0.5],'color': '#fff3cd'},
            {'range': [0.5, 5],  'color': '#f8d7da'},
        ],
        'threshold': {'line': {'color': "red", 'width': 4}, 'value': 0.5}
    }
))
fig_gauge.update_layout(height=300)
st.plotly_chart(fig_gauge, use_container_width=True)

# ── Import données entreprise ─────────────────────────────────────────────────
st.divider()
st.subheader("🏭 Intégration données entreprise")
uploaded = st.file_uploader("Importer vos données (CSV ou Excel)", type=['csv','xlsx'])
if uploaded:
    if uploaded.name.endswith('.csv'):
        df_ent = pd.read_csv(uploaded)
    else:
        df_ent = pd.read_excel(uploaded)
    st.success(f"✅ {len(df_ent)} lignes chargées")
    st.dataframe(df_ent.head(10))
    st.info("➡️ Prochaine étape : ré-entraîner les modèles avec ces données via `python src/train.py`")
