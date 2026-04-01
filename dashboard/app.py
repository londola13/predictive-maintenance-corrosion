"""
app.py — Dashboard Maintenance Prédictive Corrosion

6 pages :
  P1 — KPIs globaux
  P2 — Prédiction par CML (temps réel)
  P3 — Remaining Life par CML
  P4 — Plan d'inspection RBI
  P5 — Alertes & anomalies
  P6 — Monitoring modèle + dérive

MODE PRÉ-STAGE  : données De Waard synthétiques (prototype démonstration)
MODE FUSION     : données réelles entreprise + PHMSA + SPE + simulation (production)
"""

import json
import sys
import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.features.compute_features import compute_all_features, get_feature_matrix
from src.models.decision_engine import (
    evaluer_cml, generer_plan_inspection, extraire_alertes_critiques
)

# ── Configuration page ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Maintenance Prédictive — Corrosion ML",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constantes ────────────────────────────────────────────────────────────────

COULEUR_RISQUE = {
    "Acceptable": "#28a745",
    "Faible":     "#5cb85c",
    "Modéré":     "#f0ad4e",
    "Élevé":      "#fd7e14",
    "Sévère":     "#dc3545",
    "Critique":   "#6f42c1",
}

NACE_SEUILS = [0.025, 0.050, 0.125, 0.250, 0.500]

# ── Chargement modèles ────────────────────────────────────────────────────────

@st.cache_resource
def charger_modeles():
    try:
        model_xgb  = joblib.load(ROOT / "models/xgboost_model.pkl")
        model_surv = joblib.load(ROOT / "models/survival_model.pkl")
        model_anom = joblib.load(ROOT / "models/isolation_forest.pkl")
        scaler_anom = joblib.load(ROOT / "models/scaler_anomaly.pkl")
        return model_xgb, model_surv, model_anom, scaler_anom, True
    except Exception:
        return None, None, None, None, False

model_xgb, model_surv, model_anom, scaler_anom, ML_OK = charger_modeles()

# SHAP
shap_importance = {}
shap_path = ROOT / "models/shap_importance.json"
if shap_path.exists():
    with open(shap_path) as f:
        shap_importance = json.load(f)

# État pipeline
pipeline_state = {}
state_path = ROOT / "models/pipeline_state.json"
if state_path.exists():
    with open(state_path) as f:
        pipeline_state = json.load(f)

# ── Chargement dataset ────────────────────────────────────────────────────────

@st.cache_data
def charger_dataset_fusion():
    """Charge le dataset hybride complet (4 sources)."""
    path_fusion = ROOT / "data/processed/dataset_ML_final.csv"
    path_synth  = ROOT / "data/raw/synthetic_data.csv"

    if path_fusion.exists():
        df = pd.read_csv(path_fusion)
        sources = df["source"].value_counts().to_dict() if "source" in df.columns else {}
        a_cotco = "entreprise_reel" in sources
        return df, "fusion", sources, a_cotco
    elif path_synth.exists():
        df = pd.read_csv(path_synth)
        return df, "synthetique", {"simulation_DeWaard": len(df)}, False
    else:
        from src.data.generate_synthetic_cotco import generer_dataset_cotco
        df = generer_dataset_cotco(n_points=5000)
        df = compute_all_features(df)
        return df, "synthetique", {"simulation_DeWaard": len(df)}, False


@st.cache_data
def charger_dataset_prestage():
    """
    Mode Pré-stage : données publiques disponibles avant le stage.
    Sources : PHMSA (public réel) + SPE/NACE papers (public réel) + De Waard (synthétique).
    Aucune donnée réelle entreprise.
    """
    from src.data.generate_synthetic_cotco import generer_dataset_cotco
    from src.etl.merge_all_sources import fusionner_toutes_sources

    sources = {}

    # PHMSA — données publiques réelles
    path_phmsa = ROOT / "data/raw/phmsa_pipeline.csv"
    if path_phmsa.exists():
        df_phmsa = pd.read_csv(path_phmsa)
        df_phmsa = compute_all_features(df_phmsa)
        sources["df_phmsa"] = df_phmsa

    # SPE/NACE papers — données publiques réelles
    path_spe = ROOT / "data/raw/spe_papers.csv"
    if path_spe.exists():
        df_spe = pd.read_csv(path_spe)
        df_spe = compute_all_features(df_spe)
        sources["df_spe"] = df_spe

    # De Waard — simulation synthétique (toujours présente)
    path_synth = ROOT / "data/raw/synthetic_data.csv"
    if path_synth.exists():
        df_sim = pd.read_csv(path_synth)
    else:
        df_sim = generer_dataset_cotco(n_points=5000)
        df_sim = compute_all_features(df_sim)
    sources["df_simulation"] = df_sim

    if len(sources) == 1:
        # Seulement De Waard disponible
        df = df_sim.copy()
        df["source"] = "simulation_DeWaard"
        df["poids"]  = 0.5
        src_dict = {"simulation_DeWaard": len(df)}
    else:
        df = fusionner_toutes_sources(**sources)
        src_dict = df["source"].value_counts().to_dict()

    return df, "prestage", src_dict, False

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/oil-industry.png", width=48)
    st.markdown("### 🛢️ Maintenance Prédictive")
    st.caption("Corrosion ML — Pipeline Oil & Gas")

    st.divider()

    # ── TOGGLE MODE ───────────────────────────────────────────────────────────
    st.markdown("**Mode d'affichage**")
    mode_demo = st.toggle(
        "🔗 Mode Fusion (données réelles)",
        value=False,
        help=(
            "OFF → Mode Pré-stage : données publiques uniquement\n"
            "(PHMSA réel + SPE/NACE réel + simulation De Waard)\n\n"
            "ON → Mode Fusion : données publiques + données réelles entreprise (poids ×3)\n"
            "(à activer une fois les données entreprise disponibles)"
        ),
    )

    if mode_demo:
        st.success("🔗 FUSION\nPublic + Données réelles")
    else:
        st.info("📂 PRÉ-STAGE\nPHMSA + SPE + De Waard")

    st.divider()

    # Sélecteur de page
    page = st.radio(
        "Navigation",
        ["📊 KPIs Globaux",
         "🎯 Prédiction par CML",
         "⏳ Remaining Life",
         "📋 Plan Inspection RBI",
         "🚨 Alertes & Anomalies",
         "📈 Monitoring Modèle"],
        label_visibility="collapsed"
    )

    st.divider()

    # Statut ML
    if ML_OK:
        st.success("✅ Modèles ML chargés")
    else:
        st.warning("⚠️ Mode physique\n`python src/run_pipeline.py`")

    # Import données enterprise
    st.markdown("**Import données entreprise**")
    fichier_pi  = st.file_uploader("Export PI Server (CSV)", type=["csv"], key="pi")
    fichier_ut  = st.file_uploader("Rapport UT (PDF)",      type=["pdf"], key="ut")
    fichier_lab = st.file_uploader("Analyses Labo (Excel)", type=["xlsx","xls"], key="lab")

    if any([fichier_pi, fichier_ut, fichier_lab]):
        st.info("Données uploadées → relancer `python src/run_pipeline.py --mode fusion`")

# ── Chargement selon toggle ───────────────────────────────────────────────────

if mode_demo:
    df_global, mode_actif, sources_actives, a_donnees_cotco = charger_dataset_fusion()
else:
    df_global, mode_actif, sources_actives, a_donnees_cotco = charger_dataset_prestage()

# ══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def _afficher_badge_mode(mode, sources, a_cotco):
    """
    Affiche un banner visuel distinct selon le mode actif.

    MODE PRÉ-STAGE  : données publiques (PHMSA + SPE + De Waard) — avant le stage
    MODE FUSION     : données publiques + données réelles entreprise (poids ×3) — pendant/après stage
    """
    total = sum(sources.values())

    if mode == "fusion" and a_cotco:
        n_reel = sources.get("entreprise_reel", 0)
        n_public = total - n_reel
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #0d3b1f 0%, #1a6e3c 100%);
                border-left: 5px solid #28a745;
                border-radius: 6px;
                padding: 12px 16px;
                margin-bottom: 12px;
            ">
            <b style="color:#6ee68e; font-size:1.05em;">🔗 MODE FUSION — Données Publiques + Données Réelles</b><br>
            <span style="color:#ccc; font-size:0.88em;">
            📂 Données publiques : {n_public} lignes (PHMSA + SPE/NACE + De Waard simulation)<br>
            🏭 Données réelles entreprise : {n_reel} lignes <b style="color:#6ee68e;">(poids ×3 — prioritaires)</b><br>
            <b style="color:#aaa;">Métriques finales évaluées sur données réelles uniquement — honnêteté académique</b>
            </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        src_labels = {
            "PHMSA_public":       "PHMSA (données réelles publiques)",
            "SPE_papers":         "SPE/NACE papers (données réelles publiques)",
            "simulation_DeWaard": "Simulation De Waard (synthétique)",
        }
        detail_lines = "<br>".join(
            f"• {src_labels.get(s, s)} : {n} lignes"
            for s, n in sources.items()
        )
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
                border-left: 5px solid #1e88e5;
                border-radius: 6px;
                padding: 12px 16px;
                margin-bottom: 12px;
            ">
            <b style="color:#64b5f6; font-size:1.05em;">📂 MODE PRÉ-STAGE — Données Publiques uniquement</b><br>
            <span style="color:#ccc; font-size:0.88em;">
            {detail_lines}<br>
            <b style="color:#aaa;">Pas encore de données réelles entreprise — activer le toggle pour passer en Mode Fusion</b>
            </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _afficher_composition_sources(sources: dict, df: pd.DataFrame):
    """Graphique composition des sources avec poids."""
    POIDS_LABEL = {
        "entreprise_reel":    ("Données Réelles Entreprise", "#1a6e3c", 3.0),
        "PHMSA_public":       ("PHMSA Public", "#1e88e5", 1.0),
        "SPE_papers":         ("SPE/NACE Papers", "#8e24aa", 1.0),
        "simulation_DeWaard": ("Simulation De Waard", "#546e7a", 0.5),
    }

    labels, values, colors, poids_labels = [], [], [], []
    for src, n in sources.items():
        nom, coul, poids = POIDS_LABEL.get(src, (src, "#999", 1.0))
        labels.append(f"{nom}\n({n} lignes)")
        values.append(n)
        colors.append(coul)
        poids_labels.append(f"Poids ×{poids}")

    col_g, col_t = st.columns([1, 1])

    with col_g:
        fig = px.bar(
            x=labels, y=values,
            color=labels,
            color_discrete_sequence=colors,
            title="Nombre de lignes par source",
        )
        fig.update_layout(height=300, template="plotly_dark", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_t:
        st.markdown("**Pondération dans l'entraînement :**")
        for src, n in sources.items():
            nom, coul, poids = POIDS_LABEL.get(src, (src, "#999", 1.0))
            st.markdown(f"- **{nom}** : {n} lignes × poids **{poids}**")

        total_pondere = sum(
            n * POIDS_LABEL.get(src, ("", "", 1.0))[2]
            for src, n in sources.items()
        )
        st.markdown(f"- **Total pondéré** : {total_pondere:.0f} lignes équivalentes")


def _simuler_cml_station() -> pd.DataFrame:
    """Simule les métriques de 12 CMLs représentatifs de l'installation."""
    cml_data = [
        # CML_ID            CR_predit  RL_med  RL_pess  risque   freq
        ("CML-KRB-001",     0.042,      16.9,   11.8,   "Faible",   18),
        ("CML-KRB-002",     0.180,       3.9,    2.7,   "Élevé",     6),
        ("CML-KRB-003",     0.065,      10.9,    7.6,   "Modéré",   12),
        ("CML-KRB-004",     0.195,       3.6,    2.5,   "Élevé",     6),
        ("CML-KRB-005",     0.520,       1.3,    0.9,   "Critique",  1),
        ("CML-KRB-006",     0.210,       2.8,    2.0,   "Élevé",     6),
        ("CML-KRB-007",     0.175,       4.1,    2.9,   "Élevé",     6),
        ("CML-KRB-008",     0.055,      12.7,    8.9,   "Modéré",   12),
        ("CML-KRB-009",     0.035,      20.3,   14.2,   "Faible",   18),
        ("CML-KRB-010",     0.048,      14.8,   10.4,   "Faible",   18),
        ("CML-KRB-011",     0.150,       4.7,    3.3,   "Élevé",     6),
        ("CML-KRB-012",     0.072,       9.9,    6.9,   "Modéré",   12),
    ]
    return pd.DataFrame(cml_data,
                        columns=["CML_ID", "CR_predit", "RL_median",
                                 "RL_pessimiste", "risque", "frequence_mois"])


def _get_cml_ids(df: pd.DataFrame) -> list:
    """Retourne la liste des CML IDs disponibles."""
    if "CML_ID" in df.columns:
        return sorted(df["CML_ID"].dropna().unique().tolist())
    return [f"CML-KRB-{i:03d}" for i in range(1, 13)]


def _predire_CR(df_cond, T, CO2_pct, inhib, debit_vol, P):
    """Prédit le CR via XGBoost ou fallback physique."""
    T_K = T + 273.15
    pCO2 = P * CO2_pct / 100
    CR_dw = float(np.clip(
        10 ** (5.8 - 1710 / T_K + 0.67 * np.log10(max(pCO2, 0.001))),
        0.001, 5.0
    ))

    if ML_OK:
        try:
            X, _ = get_feature_matrix(df_cond)
            CR_predit = float(np.clip(model_xgb.predict(X)[0], 0.001, 5.0))
            return CR_predit, CR_dw, "🤖 XGBoost ML"
        except Exception:
            pass

    # Fallback physique
    inhib_eff = min(inhib / 40, 1.0)
    f_inhib   = 1 - 0.8 * inhib_eff
    CR_phys   = float(np.clip(CR_dw * f_inhib, 0.001, 5.0))
    return CR_phys, CR_dw, "⚙️ De Waard (fallback)"


def _afficher_comparaison_xgb_dw(cr_xgb, cr_dw):
    """Affiche la comparaison XGBoost vs De Waard."""
    delta_pct = (cr_dw - cr_xgb) / cr_dw * 100 if cr_dw > 0 else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("XGBoost (ML)", f"{cr_xgb:.4f} mm/an",
                help="Intègre les données réelles entreprise : inhibiteurs, upsets, saisonnalité")
    col2.metric("De Waard (physique)", f"{cr_dw:.4f} mm/an",
                help="Modèle physique pur — De Waard & Milliams (1991)")
    col3.metric("Écart XGBoost/DeWaard", f"{delta_pct:+.1f}%",
                help="Positif = XGBoost prédit moins que DeWaard (meilleure protection)")

    st.caption(
        "💡 L'écart entre XGBoost et De Waard représente la **valeur ajoutée du ML** : "
        "prise en compte des inhibiteurs réels, des upsets, de la géométrie locale de l'installation."
    )


def _afficher_courbe_degradation(t_mm, t_nominal, t_min, cr_xgb, cr_dw, rl):
    """Affiche la courbe de dégradation pour XGBoost et De Waard."""
    horizon = max(rl * 1.5, 5)
    annees  = np.linspace(0, min(horizon, 50), 300)

    eps_xgb = np.clip(t_mm - cr_xgb * annees, 0, t_nominal)
    eps_dw  = np.clip(t_mm - cr_dw  * annees, 0, t_nominal)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=annees, y=eps_xgb, mode="lines",
                             name="XGBoost ML", line=dict(color="#1e88e5", width=3)))
    fig.add_trace(go.Scatter(x=annees, y=eps_dw,  mode="lines",
                             name="De Waard (physique)",
                             line=dict(color="#aaa", width=2, dash="dash")))
    fig.add_hline(y=t_min, line_dash="dash", line_color="red",
                  annotation_text=f"t_min ASME ({t_min} mm)")
    if rl > 0:
        fig.add_vline(x=rl, line_dash="dot", line_color="orange",
                      annotation_text=f"RUL = {rl:.1f} ans")
    fig.update_layout(xaxis_title="Années", yaxis_title="Épaisseur (mm)",
                      height=380, template="plotly_dark", legend=dict(x=0.7, y=0.9))
    st.plotly_chart(fig, use_container_width=True)


def _afficher_shap(shap_dict):
    df_shap = (
        pd.DataFrame(list(shap_dict.items()), columns=["Feature", "SHAP"])
        .sort_values("SHAP", ascending=True)
        .tail(10)
    )
    fig = px.bar(df_shap, x="SHAP", y="Feature", orientation="h",
                 color="SHAP", color_continuous_scale="Blues",
                 title="Top 10 variables — impact sur CR (SHAP)")
    fig.update_layout(height=380, template="plotly_dark", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def _afficher_calendrier(evaluations):
    """Calendrier simplifié des prochaines inspections."""
    import datetime
    aujourd_hui = datetime.date.today()

    lignes = []
    for ev in sorted(evaluations, key=lambda x: x.priorite, reverse=True):
        prochaine = aujourd_hui + datetime.timedelta(days=ev.frequence_inspection * 30)
        lignes.append({
            "CML_ID": ev.CML_ID,
            "Risque": f"{ev.emoji} {ev.risque_NACE}",
            "Prochaine inspection": prochaine.strftime("%B %Y"),
            "Fréquence": f"{ev.frequence_inspection} mois",
            "Technique": ev.technique,
        })

    st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)


def _classer_nace(cr: float) -> str:
    if cr <= 0.025: return "Acceptable"
    if cr <= 0.050: return "Faible"
    if cr <= 0.125: return "Modéré"
    if cr <= 0.250: return "Élevé"
    if cr <= 0.500: return "Sévère"
    return "Critique"


def _style_risque(val):
    couleur = COULEUR_RISQUE.get(val, "#666")
    return f"color: {couleur}; font-weight: bold"


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — KPIs GLOBAUX
# ══════════════════════════════════════════════════════════════════════════════

if page == "📊 KPIs Globaux":

    st.title("📊 KPIs Globaux — Maintenance Prédictive")
    _afficher_badge_mode(mode_actif, sources_actives, a_donnees_cotco)

    # Données pour calcul KPIs
    df_kpi = df_global.dropna(subset=["CR_mesure"]) if "CR_mesure" in df_global.columns else df_global

    # ── KPIs principaux ───────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    cr_moyen = df_kpi["CR_mesure"].mean() if "CR_mesure" in df_kpi else 0
    rl_median = df_kpi["RL_ans"].median() if "RL_ans" in df_kpi else 0
    n_critiques = int((df_kpi["CR_mesure"] > 0.25).sum()) if "CR_mesure" in df_kpi else 0
    n_lignes = len(df_kpi)

    with col1:
        couleur_cr = "🔴" if cr_moyen > 0.25 else ("🟡" if cr_moyen > 0.05 else "🟢")
        st.metric("CR Moyen", f"{cr_moyen:.4f} mm/an", delta=f"{couleur_cr} NACE SP0775")
    with col2:
        st.metric("RL Médiane", f"{rl_median:.1f} ans")
    with col3:
        st.metric("CML Critiques/Sévères", n_critiques,
                  delta="⛔ Action requise" if n_critiques > 0 else "✅ Aucun")
    with col4:
        st.metric("Points de données", n_lignes)

    st.divider()

    # ── Distribution CR par niveau de risque ─────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Distribution des taux de corrosion")
        if "CR_mesure" in df_kpi.columns:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=df_kpi["CR_mesure"],
                nbinsx=50,
                name="CR mesuré",
                marker_color="steelblue",
            ))
            # Lignes NACE
            noms_nace = ["Acceptable", "Faible", "Modéré", "Élevé", "Sévère"]
            couleurs_nace = ["#28a745", "#5cb85c", "#f0ad4e", "#fd7e14", "#dc3545"]
            for seuil, nom, coul in zip(NACE_SEUILS, noms_nace, couleurs_nace):
                fig_hist.add_vline(x=seuil, line_dash="dash", line_color=coul,
                                   annotation_text=nom, annotation_position="top")
            fig_hist.update_layout(
                xaxis_title="Taux de corrosion (mm/an)",
                yaxis_title="Nombre de points",
                height=380,
                template="plotly_dark",
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    with col_right:
        st.subheader("Répartition par niveau de risque")
        if "CR_mesure" in df_kpi.columns:
            def classerNACE(cr):
                if cr <= 0.025: return "Acceptable"
                if cr <= 0.050: return "Faible"
                if cr <= 0.125: return "Modéré"
                if cr <= 0.250: return "Élevé"
                if cr <= 0.500: return "Sévère"
                return "Critique"

            df_kpi = df_kpi.copy()
            df_kpi["risque_calcule"] = df_kpi["CR_mesure"].apply(classerNACE)
            counts = df_kpi["risque_calcule"].value_counts()
            fig_pie = px.pie(
                values=counts.values, names=counts.index,
                color=counts.index,
                color_discrete_map=COULEUR_RISQUE,
                title="NACE SP0775",
            )
            fig_pie.update_layout(height=380, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)

    # ── Sources du dataset (différence Synthétique vs Fusion) ─────────────────
    if mode_actif == "fusion":
        st.subheader("📊 Composition du Dataset Hybride")
        _afficher_composition_sources(sources_actives, df_global)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — PRÉDICTION PAR CML
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🎯 Prédiction par CML":

    st.title("🎯 Prédiction Taux de Corrosion — par CML")
    _afficher_badge_mode(mode_actif, sources_actives, a_donnees_cotco)

    # Sélecteur CML
    cml_ids = _get_cml_ids(df_global)
    cml_selectionne = st.selectbox("Sélectionner un CML", cml_ids)

    st.divider()

    # Inputs process (sliders conditions opératoires)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Températures & Pression**")
        T_mean   = st.slider("TI-1001 Température entrée (°C)",     35.0, 75.0, 55.0)
        T_aval   = st.slider("TI-1002 Température aval détendeur (°C)", 15.0, 50.0, 35.0)
        P_mean   = st.slider("PI-2001 Pression entrée (bar)",        65.0, 100.0, 80.0)
        P_aval   = st.slider("PI-2002 Pression aval (bar)",           8.0,  15.0, 10.0)

    with col2:
        st.markdown("**Analyseurs en ligne**")
        CO2_pct  = st.slider("AI-4001 CO₂ (% mol)",                0.5,  5.0,  2.0)
        H2S_ppm  = st.slider("AI-4002 H₂S (ppm)",                  0.0, 500.0, 50.0)
        BSW_mean = st.slider("AI-4003 BSW (% vol)",                0.5, 30.0,  5.0)
        sable    = st.slider("AI-4004 Sable (ppm)",                 0.0, 200.0, 30.0)

    with col3:
        st.markdown("**Débit & Protection**")
        debit_vol = st.slider("FI-3001 Débit vol. (m³/h)",        200.0, 800.0, 400.0)
        inhib     = st.slider("CI-5003 Résiduel inhibiteur (mg/L)",  5.0, 80.0, 40.0)
        dP_filtre = st.slider("PI-2003 ΔP filtre (bar)",            0.0,  5.0,  1.0)
        t_mm      = st.number_input("Épaisseur actuelle UT (mm)",   5.0, 25.0, 15.9, step=0.1)

    # Construire vecteur features
    conditions = {
        "T_mean": T_mean, "T_aval": T_aval, "P_mean": P_mean, "P_aval": P_aval,
        "CO2_pct": CO2_pct, "H2S_ppm": H2S_ppm, "BSW_mean": BSW_mean,
        "sable_ppm": sable, "debit_vol": debit_vol, "inhib_mean": inhib,
        "dP_filtre": dP_filtre,
    }

    df_cond = pd.DataFrame([conditions])
    df_cond = compute_all_features(df_cond)

    # Prédiction
    cr_predit, cr_dw, methode = _predire_CR(df_cond, T_mean, CO2_pct, inhib, debit_vol, P_mean)

    # Épaisseurs
    t_nominal = 15.9
    t_min     = 8.8
    RL_ans    = max(0, (t_mm - t_min) / cr_predit) if cr_predit > 0 else 50

    # ── Affichage résultats ───────────────────────────────────────────────────
    st.divider()
    st.subheader(f"Résultats — {cml_selectionne}")
    st.caption(f"Méthode : {methode}")

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("CR prédit (XGBoost)", f"{cr_predit:.4f} mm/an")
    col_r2.metric("CR De Waard (physique)", f"{cr_dw:.4f} mm/an")
    col_r3.metric("Durée de vie résiduelle", f"{RL_ans:.1f} ans")

    nace_label = _classer_nace(cr_predit)
    col_r4.metric("Risque NACE SP0775", nace_label)

    # Comparaison XGBoost vs De Waard
    st.subheader("XGBoost vs De Waard — Valeur ajoutée du ML")
    _afficher_comparaison_xgb_dw(cr_predit, cr_dw)

    # Courbe dégradation
    st.subheader("Courbe de dégradation de l'épaisseur")
    _afficher_courbe_degradation(t_mm, t_nominal, t_min, cr_predit, cr_dw, RL_ans)

    # SHAP
    if shap_importance:
        st.subheader("Variables les plus importantes (SHAP)")
        _afficher_shap(shap_importance)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — REMAINING LIFE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "⏳ Remaining Life":

    st.title("⏳ Remaining Useful Life — par CML")
    _afficher_badge_mode(mode_actif, sources_actives, a_donnees_cotco)

    # Simuler les CML si pas de données réelles
    df_cml = _simuler_cml_station()

    # Graphique RL par CML
    st.subheader("Durée de vie résiduelle par CML (médiane ± pessimiste)")
    fig_rl = go.Figure()

    couleurs = [COULEUR_RISQUE.get(_classer_nace(row["CR_predit"]), "#666")
                for _, row in df_cml.iterrows()]

    fig_rl.add_trace(go.Bar(
        x=df_cml["CML_ID"],
        y=df_cml["RL_median"],
        name="RL Médiane",
        marker_color=couleurs,
        error_y=dict(
            type="data",
            array=df_cml["RL_median"] - df_cml["RL_pessimiste"],
            visible=True,
        ),
    ))
    fig_rl.add_hline(y=5, line_dash="dash", line_color="orange",
                     annotation_text="Seuil surveillance (5 ans)")
    fig_rl.add_hline(y=2, line_dash="dash", line_color="red",
                     annotation_text="Seuil critique (2 ans)")
    fig_rl.update_layout(
        xaxis_title="CML", yaxis_title="Années",
        height=420, template="plotly_dark",
    )
    st.plotly_chart(fig_rl, use_container_width=True)

    # Tableau détaillé
    st.subheader("Tableau Remaining Life — tous CMLs")
    df_display = df_cml[["CML_ID", "CR_predit", "RL_median", "RL_pessimiste",
                          "risque", "frequence_mois"]].copy()
    df_display.columns = ["CML", "CR (mm/an)", "RL médiane (ans)",
                           "RL pessimiste (ans)", "Risque", "Inspection (mois)"]
    st.dataframe(
        df_display.style.applymap(_style_risque, subset=["Risque"]),
        use_container_width=True, hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — PLAN D'INSPECTION RBI
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📋 Plan Inspection RBI":

    st.title("📋 Plan d'Inspection Optimisé — API 580/581")
    _afficher_badge_mode(mode_actif, sources_actives, a_donnees_cotco)

    df_cml = _simuler_cml_station()

    # Générer les évaluations
    evaluations = []
    for _, row in df_cml.iterrows():
        ev = evaluer_cml(
            CML_ID=row["CML_ID"],
            CR_predit=row["CR_predit"],
            RL_median=row["RL_median"],
            RL_pessimiste=row["RL_pessimiste"],
        )
        evaluations.append(ev)

    df_plan = generer_plan_inspection(evaluations)

    # KPIs RBI
    col1, col2, col3, col4 = st.columns(4)
    n_critique = sum(1 for e in evaluations if e.risque_NACE in ("Critique", "Sévère"))
    n_eleve    = sum(1 for e in evaluations if e.risque_NACE == "Élevé")
    n_modere   = sum(1 for e in evaluations if e.risque_NACE == "Modéré")
    n_faible   = sum(1 for e in evaluations if e.risque_NACE in ("Faible", "Acceptable"))

    col1.metric("⛔ Critique/Sévère", n_critique)
    col2.metric("🟠 Élevé",           n_eleve)
    col3.metric("🟡 Modéré",          n_modere)
    col4.metric("🟢 Faible/Acceptable", n_faible)

    st.divider()

    # Plan trié par priorité
    st.subheader("Plan d'inspection trié par priorité de risque")
    st.dataframe(df_plan, use_container_width=True, hide_index=True)

    # Calendrier simplifié
    st.subheader("Calendrier d'inspection — prochains 12 mois")
    _afficher_calendrier(evaluations)

    # Actions recommandées pour CMLs critiques
    alertes = extraire_alertes_critiques(evaluations)
    if alertes:
        st.subheader("⚠️ Actions immédiates requises")
        for alerte in alertes:
            with st.expander(f"{alerte['emoji']} {alerte['CML_ID']} — {alerte['risque']}"):
                for action in alerte["actions"]:
                    st.markdown(f"→ {action}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — ALERTES & ANOMALIES
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🚨 Alertes & Anomalies":

    st.title("🚨 Alertes & Détection d'Anomalies Process")
    _afficher_badge_mode(mode_actif, sources_actives, a_donnees_cotco)

    # Conditions process actuelles (simulées ou saisies)
    st.subheader("Conditions process temps réel")
    col1, col2 = st.columns(2)
    with col1:
        T_rt    = st.number_input("Température entrée TI-1001 (°C)",  35.0, 75.0, 55.0)
        P_rt    = st.number_input("Pression entrée PI-2001 (bar)",    65.0, 100.0, 80.0)
        CO2_rt  = st.number_input("CO₂ AI-4001 (% mol)",              0.5,  5.0,  2.0)
        BSW_rt  = st.number_input("BSW AI-4003 (% vol)",              0.5, 30.0,  5.0)
    with col2:
        inhib_rt  = st.number_input("Résiduel inhibiteur CI-5003 (mg/L)", 5.0, 80.0, 40.0)
        sable_rt  = st.number_input("Sable AI-4004 (ppm)",              0.0, 200.0, 30.0)
        dP_rt     = st.number_input("ΔP filtre PI-2003 (bar)",          0.0,  5.0,  1.0)
        vitesse_rt = st.number_input("Vélocité fluide (m/s)",           0.3,  6.0,  1.5)

    conditions_rt = {
        "T_mean": T_rt, "P_mean": P_rt, "CO2_pct": CO2_rt, "BSW_mean": BSW_rt,
        "inhib_mean": inhib_rt, "sable_ppm": sable_rt, "dP_filtre": dP_rt,
        "velocity_ms": vitesse_rt,
    }

    df_rt = pd.DataFrame([conditions_rt])
    df_rt = compute_all_features(df_rt)

    # Détection anomalie
    from src.models.train_anomaly import predict_anomaly
    resultat_anom = predict_anomaly(df_rt, model_anom, scaler_anom)

    st.divider()
    col_a, col_b = st.columns([1, 2])

    with col_a:
        score = resultat_anom.get("score_anomalie", 0)
        label = resultat_anom.get("label", "Inconnu")

        couleur_jauge = "#28a745" if score < 30 else ("#f0ad4e" if score < 70 else "#dc3545")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": f"Score Anomalie<br><b>{label}</b>"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": couleur_jauge},
                "steps": [
                    {"range": [0,  30], "color": "#d4edda"},
                    {"range": [30, 70], "color": "#fff3cd"},
                    {"range": [70, 100], "color": "#f8d7da"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "value": 70}
            }
        ))
        fig_gauge.update_layout(height=280)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_b:
        st.subheader("Alertes par tag DCS")
        alertes_tags = resultat_anom.get("alertes", [])
        if alertes_tags:
            for alerte in alertes_tags:
                st.error(f"🔴 **{alerte['tag']}** = {alerte['valeur']} "
                         f"(hors plage {alerte['seuil']})")
        else:
            st.success("✅ Tous les tags dans les plages normales")

        if score > 70:
            st.error("⚠️ **Conditions anormales détectées** — risque de corrosion accélérée")
            st.markdown("""
            **Actions recommandées :**
            → Vérifier CI-5003 (résiduel inhibiteur)
            → Contrôler AI-4003 (BSW) et AI-4004 (sable)
            → Alerter l'équipe corrosion
            """)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — MONITORING MODÈLE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📈 Monitoring Modèle":

    st.title("📈 Monitoring du Modèle ML")
    _afficher_badge_mode(mode_actif, sources_actives, a_donnees_cotco)

    # Métriques du dernier entraînement
    st.subheader("Performances du modèle (walk-forward validation)")
    xgb_metrics = pipeline_state.get("xgboost", {})

    col1, col2, col3 = st.columns(3)
    col1.metric("MAE",  f"{xgb_metrics.get('mae', '—'):.4f} mm/an" if xgb_metrics.get("mae") else "—",
                delta="✅ < 0.05" if xgb_metrics.get("mae", 1) < 0.05 else "⚠️ > objectif")
    col2.metric("R²",   f"{xgb_metrics.get('r2',  '—'):.4f}" if xgb_metrics.get("r2") else "—",
                delta="✅ > 0.85" if xgb_metrics.get("r2", 0) > 0.85 else "⚠️ < objectif")
    col3.metric("MAPE", f"{xgb_metrics.get('mape', '—'):.2f}%" if xgb_metrics.get("mape") else "—",
                delta="✅ < 15%" if xgb_metrics.get("mape", 100) < 15 else "⚠️ > objectif")

    # Amélioration vs De Waard
    ameli = xgb_metrics.get("amelioration_vs_deWaard_pct")
    if ameli:
        st.success(f"🏆 XGBoost améliore De Waard de **+{ameli:.1f}%** (MAE)")

    st.divider()

    # Cohérence physique
    st.subheader("Tests de cohérence physique")
    coherence = xgb_metrics.get("coherence_physique", {})
    if coherence:
        tests = [
            ("CR augmente avec T", coherence.get("CR_croissant_avec_T"), coherence.get("corr_T")),
            ("CR augmente avec pCO₂", coherence.get("CR_croissant_avec_pCO2"), coherence.get("corr_pCO2")),
            ("CR diminue avec inhibiteur", coherence.get("CR_decroissant_avec_inhib"), coherence.get("corr_inhib")),
        ]
        for nom, passe, corr in tests:
            icone = "✅" if passe else "❌"
            corr_str = f"(corr = {corr:.3f})" if corr is not None else ""
            st.write(f"{icone} {nom} {corr_str}")
    else:
        st.info("Entraîner les modèles pour voir les tests de cohérence physique.")

    st.divider()

    # Composition dataset
    st.subheader("Composition du dataset d'entraînement")
    sources = pipeline_state.get("sources", sources_actives)
    if sources:
        _afficher_composition_sources(sources, df_global)
    else:
        st.info("Entraîner le pipeline pour voir la composition du dataset.")

    # Ré-entraînement
    st.divider()
    st.subheader("Ré-entraînement automatique")
    st.markdown("""
    **3 niveaux d'automatisation :**
    1. **Scheduler** — vérifie chaque lundi les nouvelles mesures UT
    2. **File watcher** — déclenché dès qu'un rapport UT est déposé dans `/incoming/`
    3. **PI Web API** — connexion temps réel (perspective future)

    **Détecteur de dérive :** si MAE récente > 2× MAE référence → ré-entraînement
    """)

    if st.button("🔄 Ré-entraîner maintenant"):
        st.info("Lancer : `python src/run_pipeline.py --retrain`")
