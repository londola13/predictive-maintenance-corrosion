"""
app.py — Dashboard Maintenance Prédictive Corrosion
Lancer : streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json, sys, os
import joblib
from pathlib import Path

ROOT = Path(__file__).parent.parent  # dashboard/../ = repo root
sys.path.append(str(ROOT / 'src'))

st.set_page_config(
    page_title="Maintenance Prédictive — Corrosion Pipeline",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Maintenance Prédictive — Corrosion & Érosion/Corrosion")
st.caption("Pipelines pétroliers | Prototype M2 — XGBoost + Random Forest + de Waard-Milliams")

# ── Chargement modèles ML ─────────────────────────────────────────────────────
@st.cache_resource
def load_models():
    try:
        model_reg  = joblib.load(ROOT / 'models/model_regression.pkl')
        model_clf  = joblib.load(ROOT / 'models/model_classification.pkl')
        model_rul  = joblib.load(ROOT / 'models/model_rul.pkl')
        scaler_reg = joblib.load(ROOT / 'models/scaler_taux_corrosion.pkl')
        scaler_clf = joblib.load(ROOT / 'models/scaler_risque.pkl')
        scaler_rul = joblib.load(ROOT / 'models/scaler_rul.pkl')
        le         = joblib.load(ROOT / 'models/encoder_risque.pkl')
        return model_reg, model_clf, model_rul, scaler_reg, scaler_clf, scaler_rul, le, True
    except Exception:
        return None, None, None, None, None, None, None, False

model_reg, model_clf, model_rul, scaler_reg, scaler_clf, scaler_rul, le, ml_ok = load_models()

# Importances SHAP (optionnel)
shap_importance = None
shap_path = ROOT / 'models/shap_importance.json'
if os.path.exists(shap_path):
    with open(shap_path, encoding='utf-8') as f:
        shap_importance = json.load(f)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Paramètres du pipeline")

if ml_ok:
    st.sidebar.success("✅ Modèles ML chargés")
else:
    st.sidebar.warning("⚠️ Modèles non trouvés — mode physique\n\n"
                       "Lancer : `python notebooks/03_modeling.py`")

temperature      = st.sidebar.slider("Température (°C)",            20.0, 120.0, 60.0)
pression         = st.sidebar.slider("Pression (bar)",               10.0, 150.0, 50.0)
pH               = st.sidebar.slider("pH",                            4.5,   8.5,  6.5)
vitesse_fluide   = st.sidebar.slider("Vitesse fluide (m/s)",          0.5,  10.0,  2.0)
pco2             = st.sidebar.slider("Pression partielle CO2 (bar)",  0.1,  10.0,  1.0)
teneur_eau       = st.sidebar.slider("Teneur en eau (%)",             0.0, 100.0, 20.0)
concentration_cl = st.sidebar.number_input("Chlorures (mg/L)",        0, 50000, 5000)
age_pipeline     = st.sidebar.slider("Âge pipeline (ans)",            0.0,  30.0,  5.0)
epaisseur_paroi  = st.sidebar.slider("Épaisseur paroi (mm)",          6.0,  25.0, 12.0)
inhibiteur       = st.sidebar.selectbox("Inhibiteur de corrosion", [0, 1],
                                         format_func=lambda x: "Oui" if x else "Non")

# ── Prédiction ────────────────────────────────────────────────────────────────
EPAISSEUR_MIN = 3.0  # seuil sécurité API 579

def physics_model(T, pco2_val, v, inh):
    rate = (
        0.0315
        * (10 ** (0.67 * np.log10(max(pco2_val, 0.01))))
        * (10 ** (-1710 / (T + 273.15) + 5.37))
        * (max(v, 0.01) ** 0.146)
        * (1 - 0.7 * inh)
    )
    return float(np.clip(rate, 0.01, 5.0))

# Vecteur features — 13 colonnes (doit correspondre à features.py)
feat_vec = np.array([[
    temperature, pression, pH, vitesse_fluide, pco2,
    teneur_eau, concentration_cl, age_pipeline, epaisseur_paroi, inhibiteur,
    pco2 * temperature,                   # co2_severity
    concentration_cl * teneur_eau / 100,  # cl_water_index
    vitesse_fluide / (pression + 1),      # flow_pressure_ratio
]])

if ml_ok:
    taux   = float(np.clip(model_reg.predict(scaler_reg.transform(feat_vec))[0], 0.01, 5.0))
    r_idx  = model_clf.predict(scaler_clf.transform(feat_vec))[0]
    risque = le.inverse_transform([r_idx])[0]
    rul    = float(np.clip(model_rul.predict(scaler_rul.transform(feat_vec))[0], 0, 50))
    mode_label = "🤖 Modèles ML (XGBoost + Random Forest)"
else:
    taux   = physics_model(temperature, pco2, vitesse_fluide, inhibiteur)
    risque = "Élevé" if taux >= 0.5 else ("Moyen" if taux >= 0.1 else "Faible")
    rul    = max(0, (epaisseur_paroi - EPAISSEUR_MIN) / taux)
    mode_label = "⚙️ Modèle physique (de Waard-Milliams)"

couleur = {"Faible": "green", "Moyen": "orange", "Élevé": "red"}.get(risque, "orange")

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.caption(f"Mode actif : {mode_label}")
col1, col2, col3 = st.columns(3)
col1.metric("Taux de corrosion",        f"{taux:.4f} mm/an")
col2.metric("Durée de vie résiduelle",  f"{rul:.1f} ans")
col3.metric("Niveau de risque",         risque)

st.markdown(f"### Risque : :{couleur}[**{risque}**]")
st.divider()

# ── Onglets ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📉 Dégradation", "🎯 Jauge", "📊 SHAP"])

with tab1:
    st.subheader("Courbe de dégradation de l'épaisseur")
    horizon = max(rul * 1.5, 5)
    annees  = np.linspace(0, min(horizon, 50), 200)
    eps     = np.clip(epaisseur_paroi - taux * annees, 0, epaisseur_paroi)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=annees, y=eps, mode='lines',
                              name='Épaisseur paroi',
                              line=dict(color='steelblue', width=3)))
    fig.add_hline(y=EPAISSEUR_MIN, line_dash="dash", line_color="red",
                  annotation_text="Seuil critique API 579 (3 mm)")
    if rul > 0:
        fig.add_vline(x=rul, line_dash="dot", line_color="orange",
                      annotation_text=f"RUL = {rul:.1f} ans")
    fig.update_layout(xaxis_title="Années", yaxis_title="Épaisseur (mm)",
                      height=420, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Jauge de risque")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=taux,
        title={'text': "Taux de corrosion (mm/an)"},
        gauge={
            'axis': {'range': [0, 5]},
            'bar': {'color': couleur},
            'steps': [
                {'range': [0,   0.1], 'color': '#d4edda'},
                {'range': [0.1, 0.5], 'color': '#fff3cd'},
                {'range': [0.5, 5.0], 'color': '#f8d7da'},
            ],
            'threshold': {'line': {'color': 'red', 'width': 4}, 'value': 0.5}
        }
    ))
    fig_gauge.update_layout(height=320)
    st.plotly_chart(fig_gauge, use_container_width=True)

with tab3:
    st.subheader("Importance des variables (SHAP)")
    if shap_importance:
        df_shap = (
            pd.DataFrame(list(shap_importance.items()),
                         columns=['Feature', 'Importance SHAP'])
            .sort_values('Importance SHAP', ascending=True)
            .tail(10)
        )
        fig_shap = px.bar(df_shap, x='Importance SHAP', y='Feature',
                           orientation='h', color='Importance SHAP',
                           color_continuous_scale='Blues',
                           title='Top 10 variables — impact sur taux de corrosion')
        fig_shap.update_layout(height=420, showlegend=False)
        st.plotly_chart(fig_shap, use_container_width=True)
        st.caption("SHAP : contribution moyenne absolue de chaque variable aux prédictions XGBoost.")
    else:
        st.info("Générez les valeurs SHAP en exécutant :\n\n"
                "```\npython notebooks/03_modeling.py\n```")

# ── Import données entreprise ─────────────────────────────────────────────────
st.divider()
st.subheader("🏭 Intégration données entreprise")
uploaded = st.file_uploader("Importer vos données (CSV ou Excel)", type=['csv', 'xlsx'])
if uploaded:
    df_ent = (pd.read_csv(uploaded) if uploaded.name.endswith('.csv')
              else pd.read_excel(uploaded))
    st.success(f"✅ {len(df_ent)} lignes chargées")
    st.dataframe(df_ent.head(10))
    st.info("Pour ré-entraîner les modèles avec ces données :\n\n"
            "1. Placez le fichier dans `data/enterprise/`\n"
            "2. Lancez `python src/train.py`")
