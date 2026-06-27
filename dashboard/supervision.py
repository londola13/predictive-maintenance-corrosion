# -*- coding: utf-8 -*-
"""SUPERVISION CORROSION — écran de contrôle de l'expérience RTF (M2).

Dashboard temps réel : ESP32 -> Supabase -> Pipeline -> XGBoost -> ici.
Lancement local :  streamlit run dashboard/supervision.py
"""
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Supervision Corrosion — M2",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import data_layer as dl  # noqa: E402  (gère sys.path + secrets)
import ui_components as ui  # noqa: E402

ui.inject_css()

DOSSIER = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(DOSSIER)


# ============================================================
# SIDEBAR — navigation
# ============================================================
with st.sidebar:
    st.markdown('<p class="scada-title" style="font-size:1.2rem;">⚡ CORROSION<br/>MONITOR</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="scada-sub">Maintenance prédictive — M2</p>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["🏭  Synoptique", "🔬  Supervision Run", "📡  Live", "🤖  ML & Prédiction",
         "🔮  Prédiction live", "🧰  Ordres de travail", "🧪  Inhibiteur / dilution"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        '<div style="color:#566173; font-size:0.72rem; line-height:1.5;">'
        "Sonde ER fil de fer · ESP32 + HX711<br/>"
        "Mesure toutes les 30 s · Supabase<br/>"
        "Pipeline Python · XGBoost<br/><br/>"
        "Ricky Parfait BATOUMBI IKOND<br/>ESTL Douala — 2026</div>",
        unsafe_allow_html=True,
    )

run_actif_id, run_actif_row = dl.detecter_run_actif()
EN_LIGNE = run_actif_id is not None


# ============================================================
# PAGE 1 — SYNOPTIQUE
# ============================================================
if page.endswith("Synoptique"):
    ui.header("SUPERVISION CORROSION", "Chaîne d'acquisition — vue d'ensemble", EN_LIGNE)
    st.markdown("")
    ui.synoptique_chaine(EN_LIGNE)

    try:
        stats = dl.stats_globales()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Runs réalisés", stats["nb_runs"])
        c2.metric("Runs terminés", stats["nb_termines"])
        c3.metric("Run actif", stats["nb_actifs"])
        c4.metric("Mesures totales", f"{stats['total_mesures']:,}".replace(",", " "))
        c5.metric("Heures d'acquisition", f"{stats['heures_cumulees']:.0f} h")
    except Exception as e:
        st.warning(f"Connexion Supabase indisponible : {e}")

    st.markdown("### Registre des essais")
    lignes = []
    try:
        statuts = dl.lister_runs().set_index("run_id")["status"].to_dict()
    except Exception:
        statuts = {}
    for rid, meta in dl.RUNS_REGISTRY.items():
        statut = statuts.get(rid, "?")
        lignes.append({
            "Essai": meta["label"],
            "Condition": meta["condition"],
            "Groupe ML": meta["groupe"],
            "Temp. moy": meta["temp"],
            "Durée": meta["duree"],
            "Phase": meta["phase"],
            "Statut": "✅ Terminé" if statut == "completed" else ("🔴 ACTIF" if statut == "active" else statut),
            "Observation": meta["note"],
        })
    st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)

    st.markdown("### Protocole en deux phases")
    col1, col2 = st.columns(2)
    with col1:
        ui.panel("Phase 1 — Exploratoire (terminée)",
                 "<span style='color:#e8edf4;'>Runs #1-3 et #11-14 à température ambiante subie. "
                 "Résultat clé : <b>la température est la variable dominante</b> de la variabilité "
                 "entre essais (10 h à 22 h pour des conditions nominales identiques).</span>")
    with col2:
        ui.panel("Phase 2 — Contrôlée (en préparation)",
                 "<span style='color:#e8edf4;'>Bain-marie thermostaté (chauffe-eau 25 W). "
                 "Consignes fixes : <b>Run #15-16 à 30 °C</b>, <b>Run #17-18 à 32 °C</b> "
                 "→ 3 essais par consigne, plus d'orphelin thermique.</span>")


# ============================================================
# PAGE 2 — SUPERVISION RUN
# ============================================================
elif page.endswith("Supervision Run"):
    ui.header("SUPERVISION RUN", "Analyse détaillée d'un essai", EN_LIGNE)
    st.markdown("")

    choix = st.selectbox(
        "Sélection de l'essai",
        options=list(dl.RUNS_REGISTRY.keys()),
        format_func=lambda rid: f"{dl.RUNS_REGISTRY[rid]['label']} — {dl.RUNS_REGISTRY[rid]['condition']} ({dl.RUNS_REGISTRY[rid]['temp']})",
    )
    meta = dl.RUNS_REGISTRY[choix]

    try:
        df = dl.charger_run_traite(choix)
    except Exception as e:
        st.error(f"Impossible de charger ce run : {e}")
        st.stop()

    t = df["temps_immersion_h"].astype(float)
    r = df["rx_corr"].astype(float)
    duree = float(t.iloc[-1])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Durée de vie", f"{duree:.1f} h")
    c2.metric("Mesures", f"{len(df)}")
    c3.metric("R initiale", f"{r.iloc[:20].median():.2f} Ω")
    c4.metric("R finale", f"{r.iloc[-1]:.1f} Ω")
    temp_moy = df["temp_lisse"].mean()
    c5.metric("Température moy.", f"{temp_moy:.1f} °C")

    if "restaurée" in meta["note"] or "partielle" in meta["note"].lower():
        st.info(f"ℹ️ {meta['label']} : {meta['note']}")

    # ---------- REPLAY ANIMÉ R(t) ----------
    st.markdown("### Évolution de la résistance — replay de l'essai")
    dfa = dl.downsample(df[["temps_immersion_h", "rx_corr", "temp_lisse"]].dropna(), 1100)
    ta = dfa["temps_immersion_h"].values
    ra = dfa["rx_corr"].values
    tempa = dfa["temp_lisse"].values

    n_frames = 90
    pas = max(1, len(dfa) // n_frames)
    indices = list(range(2, len(dfa), pas)) + [len(dfa) - 1]

    frames = [
        go.Frame(
            data=[go.Scatter(x=ta[:k], y=ra[:k])],
            name=str(k),
            layout=go.Layout(annotations=[dict(
                x=0.02, y=0.95, xref="paper", yref="paper", showarrow=False,
                text=f"<b>t = {ta[k-1]:.1f} h</b>   R = {ra[k-1]:.2f} Ω",
                font=dict(color="#00d4ff", family="Consolas", size=16),
            )]),
        )
        for k in indices
    ]

    fig = go.Figure(
        data=[
            go.Scatter(x=ta, y=ra, mode="lines", name="R(t) complet",
                       line=dict(color="rgba(0,212,255,0.18)", width=1.5)),
            go.Scatter(x=ta[:2], y=ra[:2], mode="lines", name="Replay",
                       line=dict(color="#00d4ff", width=3)),
        ],
        frames=[go.Frame(data=[f.data[0]], name=f.name,
                         layout=f.layout,
                         traces=[1]) for f in frames],
    )
    fig.add_trace(go.Scatter(x=ta, y=tempa, mode="lines", name="Température",
                             yaxis="y2", line=dict(color="#f39c12", width=1.2, dash="dot")))
    fig.update_layout(
        **{**ui.PLOTLY_LAYOUT,
           "yaxis": dict(title="Résistance compensée (Ω)", gridcolor="#1f2937")},
        height=460,
        xaxis_title="Temps d'immersion (h)",
        yaxis2=dict(title="Température (°C)", overlaying="y", side="right",
                    showgrid=False, tickfont=dict(color="#f39c12")),
        legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)"),
        updatemenus=[dict(
            type="buttons", direction="left", x=0.0, y=1.18, bgcolor="#111827",
            font=dict(color="#e8edf4"), bordercolor="#1f2937",
            buttons=[
                dict(label="▶  REPLAY", method="animate",
                     args=[None, dict(frame=dict(duration=45, redraw=False),
                                      fromcurrent=False, transition=dict(duration=0))]),
                dict(label="⏸", method="animate",
                     args=[[None], dict(frame=dict(duration=0), mode="immediate")]),
            ],
        )],
    )
    # Annotation rupture (fait observé : fin du run)
    fig.add_annotation(x=ta[-1], y=ra[-1], text="⚡ RUPTURE", showarrow=True,
                       arrowhead=2, arrowcolor="#e74c3c", ax=-60, ay=-30,
                       font=dict(color="#e74c3c", family="Consolas", size=13))
    st.plotly_chart(fig, use_container_width=True)

    # ---------- CR + JAUGES ----------
    col_g, col_d = st.columns([2, 1])
    with col_g:
        st.markdown("### Taux de corrosion CR(t)")
        fig_cr = go.Figure()
        dfc = dl.downsample(df[["temps_immersion_h", "CR_lisse"]].dropna(), 2000)
        fig_cr.add_trace(go.Scatter(
            x=dfc["temps_immersion_h"], y=dfc["CR_lisse"], mode="lines",
            line=dict(color="#2ecc71", width=2), fill="tozeroy",
            fillcolor="rgba(46,204,113,0.08)", name="CR lissé"))
        fig_cr.update_layout(**ui.PLOTLY_LAYOUT, height=330,
                             xaxis_title="Temps d'immersion (h)",
                             yaxis_title="CR (µm/an, écrêté à 2000)")
        st.plotly_chart(fig_cr, use_container_width=True)
    with col_d:
        st.markdown("### État final")
        cr_fin = float(pd.to_numeric(df["CR_lisse"], errors="coerce").dropna().iloc[-1])
        st.plotly_chart(ui.jauge(cr_fin, "CR final", "µm/an", 2000), use_container_width=True)
        sec = float(pd.to_numeric(df["section_perdue_pct"], errors="coerce").dropna().iloc[-1])
        st.plotly_chart(ui.jauge(min(max(sec, 0), 100), "Section perdue", "%", 100),
                        use_container_width=True)

    # ---------- PRÉDICTION PHYSIQUE DE RUPTURE (modèle 1/R) ----------
    st.markdown("### Prédiction physique de la rupture — modèle 1/R")
    st.caption("R = ρL/(A₀ − k·t) ⇒ 1/R décroît linéairement ; la rupture survient quand 1/R "
               "atteint zéro. Droite ajustée sur les premiers 60 % de l'essai → prédiction "
               "émise bien avant la rupture réelle.")
    try:
        tv = t.values
        inv_r = 1.0 / r.values
        t_rup_reel = tv[-1]
        mask = (tv >= 0.15 * t_rup_reel) & (tv <= 0.60 * t_rup_reel)
        slope, intercept = np.polyfit(tv[mask], inv_r[mask], 1)
        if slope < 0:
            t_rup_pred = -intercept / slope
            erreur = t_rup_pred - t_rup_reel

            figp = go.Figure()
            dfp = dl.downsample(pd.DataFrame({"t": tv, "ir": inv_r}), 1500)
            figp.add_trace(go.Scatter(x=dfp["t"], y=dfp["ir"], mode="markers",
                                      marker=dict(color="rgba(0,212,255,0.35)", size=4),
                                      name="1/R mesuré"))
            tline = np.linspace(0.15 * t_rup_reel, max(t_rup_pred, t_rup_reel) * 1.04, 60)
            figp.add_trace(go.Scatter(x=tline, y=intercept + slope * tline, mode="lines",
                                      line=dict(color="#e74c3c", width=2.5),
                                      name="Ajustement (60 % de l'essai)"))
            figp.add_hline(y=0, line_color="#566173", line_dash="dot")
            figp.add_vline(x=t_rup_pred, line_color="#2ecc71", line_dash="dash",
                           annotation_text=f"Prédite : {t_rup_pred:.1f} h",
                           annotation_font_color="#2ecc71")
            figp.add_vline(x=t_rup_reel, line_color="#e8edf4",
                           annotation_text=f"Réelle : {t_rup_reel:.1f} h",
                           annotation_font_color="#e8edf4",
                           annotation_position="bottom right")
            figp.update_layout(**ui.PLOTLY_LAYOUT, height=380,
                               xaxis_title="Temps (h)", yaxis_title="1/R (Ω⁻¹)",
                               legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(figp, use_container_width=True)

            m1, m2, m3 = st.columns(3)
            m1.metric("Rupture réelle", f"{t_rup_reel:.1f} h")
            m2.metric("Rupture prédite (à 60 %)", f"{t_rup_pred:.1f} h", delta=f"{erreur:+.1f} h")
            m3.metric("Erreur relative", f"{abs(erreur) / t_rup_reel * 100:.0f} %")
        else:
            st.info("Pente 1/R non décroissante sur la fenêtre d'ajustement — modèle non applicable à cet essai.")
    except Exception as e:
        st.warning(f"Modèle physique non calculable : {e}")


# ============================================================
# PAGE 3 — LIVE
# ============================================================
elif page.endswith("Live"):
    ui.header("MONITORING LIVE", "Acquisition temps réel", EN_LIGNE)
    st.markdown("")

    if not EN_LIGNE:
        ui.synoptique_chaine(False)
        st.markdown(
            '<div class="panel" style="text-align:center; padding:38px;">'
            '<span class="badge badge-standby"><span class="dot dot-off"></span>'
            "AUCUNE ACQUISITION EN COURS</span>"
            '<p style="color:#8b95a5; margin-top:18px;">Le dispositif est en attente du prochain essai.<br/>'
            "<b style='color:#e8edf4;'>Run #15 — phase contrôlée (bain thermostaté, consigne 30 °C)</b> "
            "sera détecté automatiquement ici dès son lancement.</p></div>",
            unsafe_allow_html=True)

        # Dernier run terminé en rappel
        dernier = "83760a06-b2c8-4730-8368-18babfcae3e1"
        meta = dl.RUNS_REGISTRY[dernier]
        st.markdown(f"### Dernier essai terminé — {meta['label']}")
        try:
            df = dl.charger_run_traite(dernier)
            dfd = dl.downsample(df[["temps_immersion_h", "rx_corr"]].dropna(), 1500)
            figd = go.Figure(go.Scatter(x=dfd["temps_immersion_h"], y=dfd["rx_corr"],
                                        mode="lines", line=dict(color="#00d4ff", width=2)))
            figd.update_layout(**ui.PLOTLY_LAYOUT, height=300,
                               xaxis_title="Temps (h)", yaxis_title="R (Ω)")
            st.plotly_chart(figd, use_container_width=True)
        except Exception:
            pass
    else:
        notes = str(run_actif_row.get("notes", ""))[:120]
        st.success(f"🔴 Run actif détecté : `{run_actif_id[:8]}…` — {notes}")

        def _vue_live():
            df = dl.dernieres_mesures(run_actif_id, 240)  # ~2 h à 30 s/mesure
            if len(df) == 0:
                st.info("En attente des premières mesures…")
                return
            dern = df.iloc[-1]
            age_s = pd.Timestamp.utcnow().timestamp() - float(dern["timestamp_s"])
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Résistance actuelle", f"{dern['rx_ohm']:.3f} Ω")
            temp_txt = f"{dern['temp_c']:.1f} °C" if dern["temp_c"] > -100 else "—"
            c2.metric("Température bain", temp_txt)
            dr = dern.get("delta_r_per_h", float("nan"))
            c3.metric("dR/dt", f"{dr:.4f} Ω/h" if pd.notna(dr) else "—")
            c4.metric("Dernière mesure", f"il y a {age_s:.0f} s",
                      delta="OK" if age_s < 90 else "⚠ retard", delta_color="normal")

            th = (df["timestamp_s"] - df["timestamp_s"].iloc[0]) / 3600.0
            figl = go.Figure()
            figl.add_trace(go.Scatter(x=th, y=df["rx_ohm"], mode="lines",
                                      line=dict(color="#00d4ff", width=2.2),
                                      fill="tozeroy", fillcolor="rgba(0,212,255,0.06)",
                                      name="R (Ω)"))
            figl.update_layout(**ui.PLOTLY_LAYOUT, height=340,
                               xaxis_title="Fenêtre glissante (h)", yaxis_title="R (Ω)",
                               title=dict(text="DERNIÈRES 2 HEURES", font=dict(
                                   color="#8b95a5", family="Consolas", size=12)))
            st.plotly_chart(figl, use_container_width=True)

        if hasattr(st, "fragment"):
            vue = st.fragment(run_every="30s")(_vue_live)
            vue()
            st.caption("⟳ Actualisation automatique toutes les 30 secondes.")
        else:
            _vue_live()
            if st.button("⟳ Actualiser"):
                st.rerun()


# ============================================================
# PAGE 4 — ML & PRÉDICTION
# ============================================================
elif page.endswith("Prédiction"):
    ui.header("ML & PRÉDICTION", "Évaluation XGBoost — leave-one-run-out", EN_LIGNE)
    st.markdown("")

    chemin_json = os.path.join(DOSSIER, "static_results.json")
    try:
        with open(chemin_json, encoding="utf-8") as f:
            res = json.load(f)
    except FileNotFoundError:
        st.error("static_results.json introuvable — lancer gen_dashboard_results.py en local.")
        st.stop()

    st.caption(f"Résultats précalculés le {res['genere_le'][:10]} — cible : taux de corrosion "
               f"(CR, µm/an) — validation leave-one-run-out (le run testé n'est jamais vu à l'entraînement).")

    # ---------- Protocole actuel : XGBoost vs baselines ----------
    st.markdown("### XGBoost face aux méthodes de référence (protocole actuel)")
    proto = res["protocole_actuel"]
    runs_test = list(proto.keys())
    modeles = ["XGBoost", "Régression linéaire", "Moyenne constante"]
    couleurs = {"XGBoost": "#00d4ff", "Régression linéaire": "#f39c12", "Moyenne constante": "#566173"}

    figb = go.Figure()
    for m in modeles:
        vals = [proto[r][m]["r2"] for r in runs_test]
        affiche = [max(v, -2.0) for v in vals]
        figb.add_trace(go.Bar(
            name=m, x=[f"Test {r}" for r in runs_test], y=affiche,
            marker_color=couleurs[m],
            text=[f"{v:.2f}" for v in vals], textposition="outside",
            textfont=dict(family="Consolas", size=11),
        ))
    figb.add_hline(y=0, line_color="#8b95a5")
    figb.update_layout(**{**ui.PLOTLY_LAYOUT,
                          "yaxis": dict(title="R² (affichage limité à −2)",
                                        range=[-2.3, 1.0], gridcolor="#1f2937")},
                       height=400, barmode="group",
                       legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(figb, use_container_width=True)
    st.caption("Entraînement : les 2 autres runs de la série + auxiliaires sous-échantillonnés "
               "(variante C). Les valeurs < −2 sont écrêtées à l'affichage (valeur réelle sur la barre).")

    # ---------- Étude des variantes ----------
    st.markdown("### Étude méthodologique — 4 stratégies d'entraînement")
    lignes = []
    for code in ["A", "B", "C", "D"]:
        v = res["variantes"][code]
        ligne = {"Variante": f"{code} — {v['nom']}" + ("  ⭐ RETENUE" if v["retenue"] else "")}
        for rn, scores in v["runs"].items():
            ligne[f"R² {rn}"] = scores["r2"]
        ligne["R² moyen"] = v["moyenne_r2"]
        ligne["MAE moyen"] = v["moyenne_mae"]
        lignes.append(ligne)
    st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        ui.panel("Mécanisme identifié",
                 f"<span style='color:#e8edf4;'>{res['narratif']['mecanisme']}</span>")
    with col2:
        ui.panel("Prochaine étape",
                 f"<span style='color:#e8edf4;'>{res['narratif']['phase2']}</span>")

    # ---------- Importance des features ----------
    st.markdown("### Variables utilisées par le modèle")
    imp = res["importance_features"]
    noms_fr = {
        "rx_corr": "Résistance compensée (Ω)",
        "temp_lisse": "Température instantanée (°C)",
        "temp_moy_6h": "Température moyenne 6 h (°C)",
        "temps_immersion_h": "Temps d'immersion (h)",
        "delta_R_absolu": "ΔR depuis baseline (Ω)",
        "section_perdue_pct": "Section perdue (%)",
    }
    s = pd.Series({noms_fr.get(k, k): v for k, v in imp.items()}).sort_values()
    figi = go.Figure(go.Bar(
        x=s.values, y=s.index, orientation="h",
        marker=dict(color=["#e74c3c" if v == s.max() else "#00d4ff" for v in s.values]),
        text=[f"{v:.3f}" for v in s.values], textposition="outside",
        textfont=dict(family="Consolas", size=11),
    ))
    figi.update_layout(**ui.PLOTLY_LAYOUT, height=320,
                       xaxis_title="Importance relative (XGBoost)")
    st.plotly_chart(figi, use_container_width=True)

    # ---------- Figures du mémoire ----------
    st.markdown("### Figures de l'étude")
    c1, c2 = st.columns(2)
    f1 = os.path.join(RACINE, "plots", "fig_ml_vs_baseline.png")
    f2 = os.path.join(RACINE, "memoire", "figures", "fig_ii1_architecture.png")
    if os.path.exists(f1):
        c1.image(f1, caption="XGBoost plafonne face à l'extrapolation linéaire (forecasting de R)")
    if os.path.exists(f2):
        c2.image(f2, caption="Architecture du système")


# ============================================================
# PAGE 5 — PRÉDICTION LIVE (service predict_loop)
# ============================================================
elif page.endswith("live"):
    ui.header("PRÉDICTION TEMPS RÉEL", "Modèle ML sur le run actif", EN_LIGNE)
    if not EN_LIGNE:
        st.info("Aucun run actif. Lancez un run, puis le service de prédiction : "
                "`python src/realtime/predict_loop.py` (les prédictions s'afficheront ici).")
    else:
        import sys as _sys
        if RACINE not in _sys.path:
            _sys.path.insert(0, RACINE)

        @st.cache_resource
        def _modele_cr():
            import pickle
            m = pickle.load(open(os.path.join(RACINE, "models", "xgb_cr.pkl"), "rb"))
            return m, list(m.feature_names_in_)

        est = None
        try:
            from src.realtime import predict_band as pb
            _m, _fe = _modele_cr()
            est = pb.estimer(run_actif_id, _m, _fe)
        except Exception as e:
            st.caption(f"(comparatif des estimateurs indisponible : {e})")

        preds = dl.dernieres_predictions(run_actif_id)
        if est is None and preds.empty:
            st.warning("Run actif détecté, mais pas encore assez de points pour prédire. "
                       "Service de fond : `python src/realtime/predict_loop.py`.")
        else:
            # --- bandeau d'état (garde-fou : le RUL n'escalade que si section ≥ 40 %) ---
            if est is not None:
                sec, rp = est["section_pct"], est["rul_phys_h"]
                rul_ok = (not np.isnan(rp)) and sec >= 40.0
                if sec >= 85 or (rul_ok and rp <= 2):
                    badge = "🔴 ROUGE"
                elif sec >= 60 or (rul_ok and rp <= 5):
                    badge = "🟠 ORANGE"
                else:
                    badge = "🟢 VERT"
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("CR prédit (XGBoost)", f"{est['cr_xgb']:.0f}")
                c2.metric("Section perdue", f"{sec:.0f} %")
                c3.metric("Écoulé", f"{est['elapsed_h']:.1f} h")
                c4.metric("État", badge)

                # --- comparatif des 3 estimateurs de durée de vie ---
                st.markdown("#### Durée de vie totale — 3 estimateurs côte à côte")
                XMAX = 28.0  # axe fixe : robuste aux pics de RUL (physique bruité tôt)

                def _pt(v):
                    if v is None or np.isnan(v):
                        return None, ""
                    return min(v, XMAX - 0.4), (f"{v:.0f} h" if v <= XMAX else f"≈{v:.0f} h ▶")

                fig = go.Figure()
                if not np.isnan(est["sim_p10"]):
                    fig.add_shape(type="rect", x0=est["sim_p10"], x1=min(est["sim_p90"], XMAX),
                                  y0=2.62, y1=3.38, fillcolor="rgba(155,109,255,0.22)",
                                  line=dict(color="rgba(155,109,255,0.6)"))
                    fig.add_trace(go.Scatter(x=[est["sim_p50"]], y=[3], mode="markers+text",
                                  marker=dict(color="#9b6dff", size=16, symbol="diamond"),
                                  text=[f"{est['sim_p50']:.0f} h"], textposition="top center",
                                  textfont=dict(color="#cbb6ff")))
                for v, yv, col in [(est["vie_xgb_h"], 2, "#1f77b4"), (est["vie_phys_h"], 1, "#e08a1e")]:
                    x, lbl = _pt(v)
                    if x is not None:
                        fig.add_trace(go.Scatter(x=[x], y=[yv], mode="markers+text",
                                      marker=dict(color=col, size=15), text=[lbl],
                                      textposition="middle right", textfont=dict(color=col)))
                fig.add_vline(x=min(est["elapsed_h"], XMAX), line=dict(color="#9aa6b2", dash="dot"),
                              annotation_text="maintenant", annotation_position="top")
                fig.update_yaxes(tickvals=[1, 2, 3],
                                 ticktext=["Physique (mesuré)", "XGBoost (dérivé)", "Simulateur (bande)"],
                                 range=[0.4, 3.6])
                fig.update_xaxes(title="durée de vie totale estimée (h)", range=[0, XMAX])
                fig.update_layout(height=300, template="plotly_dark", showlegend=False,
                                  margin=dict(l=10, r=10, t=20, b=40))
                st.plotly_chart(fig, use_container_width=True)
                st.caption(
                    f"🟣 **Simulateur** = bande prédictive robuste **[{est['sim_p10']:.1f}–{est['sim_p90']:.1f}] h** "
                    f"(médiane {est['sim_p50']:.1f} h), a priori, couvre les 2 morphologies — *le seul vrai prédicteur "
                    f"du temps de rupture*.  🔵 **XGBoost (dérivé)** = durée déduite du CR prédit.  "
                    f"🟠 **Physique** = extrapolation de la vitesse mesurée.  Les deux derniers sont **bruités au début** "
                    f"et convergent vers la rupture en fin de run.")

            # --- séries temporelles (service predict_loop) ---
            if not preds.empty:
                last = preds.iloc[-1]
                st.caption(f"Dernière prédiction live : {last['predicted_at']:%Y-%m-%d %H:%M} "
                           f"· {len(preds)} points · CR = XGBoost (échelle labo), RUL = extrapolation physique.")
                for col, titre, coul in [("rul_pred", "RUL estimé (h) — extrapolation physique", "#e08a1e"),
                                         ("cr_pred", "CR prédit — XGBoost", "#1f77b4")]:
                    figts = go.Figure(go.Scatter(x=preds["predicted_at"], y=preds[col],
                                                 mode="lines+markers", line=dict(color=coul)))
                    figts.update_layout(title=titre, height=260, template="plotly_dark",
                                        margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(figts, use_container_width=True)


# ============================================================
# PAGE 6 — ORDRES DE TRAVAIL (CMMS maison)
# ============================================================
elif page.endswith("travail"):
    ui.header("ORDRES DE TRAVAIL", "CMMS maison — généré au dépassement de seuil", EN_LIGNE)
    from src.cmms.work_orders import list_work_orders, update_statut
    try:
        wos = list_work_orders()
    except Exception as e:
        st.error(f"Lecture cr_work_orders impossible : {e}")
        wos = []
    c1, c2, c3 = st.columns(3)
    c1.metric("Ouverts", sum(1 for w in wos if w["statut"] == "ouvert"))
    c2.metric("En cours", sum(1 for w in wos if w["statut"] == "en_cours"))
    c3.metric("Fermés", sum(1 for w in wos if w["statut"] == "ferme"))

    st.markdown("### Ordres actifs")
    actifs = [w for w in wos if w["statut"] != "ferme"]
    if not actifs:
        st.success("Aucun ordre de travail ouvert.")
    for w in actifs:
        emoji = "🔴" if w["niveau"] == "rouge" else "🟠"
        with st.expander(f"{emoji} {w['titre']}  ·  [{w['statut']}]"):
            st.text(w.get("description", ""))
            cc1, cc2, cc3 = st.columns([2, 1, 1])
            asg = cc1.text_input("Assigné à", value=w.get("assignee") or "", key=f"asg_{w['wo_id']}")
            if cc2.button("Marquer en cours", key=f"enc_{w['wo_id']}"):
                update_statut(w["wo_id"], "en_cours", asg or None)
                st.rerun()
            if cc3.button("Clôturer", key=f"clo_{w['wo_id']}"):
                update_statut(w["wo_id"], "ferme", asg or None)
                st.rerun()

    if wos:
        st.markdown("### Historique complet")
        cols = ["created_at", "niveau", "titre", "statut", "section_pct", "rul_pred", "assignee"]
        dfw = pd.DataFrame(wos)
        st.dataframe(dfw[[c for c in cols if c in dfw.columns]],
                     use_container_width=True, hide_index=True)


# ============================================================
# PAGE 7 — INHIBITEUR / DILUTION (estimateur indicatif)
# ============================================================
elif page.endswith("dilution"):
    ui.header("EFFET INHIBITEUR / DILUTION", "Estimation indicative de l'allongement de vie", EN_LIGNE)
    from src.analysis.inhibitor_calc import (
        estimer_par_duree_cible, estimer_par_reduction, ANCRES, CAVEATS, BASELINE_PURE_H,
    )
    st.warning("⚠️ " + CAVEATS)
    st.markdown(f"**Baseline acide pur** : {BASELINE_PURE_H:.1f} h (médiane des runs non dilués, 10–15 h). "
                "Réduire l'agressivité (dilution / inhibiteur) abaisse le CR → allonge la vie (durée ≈ ∝ 1/CR).")
    mode = st.radio("Mode de calcul", ["Par durée de vie cible", "Par réduction de CR visée"],
                    horizontal=True)
    if mode.startswith("Par durée"):
        cible = st.slider("Durée de vie cible (h)", 12, 120, 40, 1)
        r = estimer_par_duree_cible(cible)
        c1, c2, c3 = st.columns(3)
        c1.metric("Réduction de CR nécessaire", f"{r['reduction_cr_pct']:.0f} %")
        c2.metric("Facteur de vie", f"×{r['facteur_vie']:.1f}")
        c3.metric("Analogue réel", r["analogue"]["label"])
        st.info(f"Pour viser ~{cible} h, réduire le CR d'environ **{r['reduction_cr_pct']:.0f} %** "
                f"(acide moins agressif / inhibiteur). Niveau comparable à **{r['analogue']['label']}** "
                f"({r['analogue']['dilution']}, {r['analogue']['duree_h']:.0f} h).")
    else:
        red = st.slider("Réduction de CR visée (%)", 0, 95, 50, 5)
        r = estimer_par_reduction(red)
        c1, c2, c3 = st.columns(3)
        c1.metric("Durée de vie estimée", f"{r['duree_estimee_h']:.0f} h")
        c2.metric("Gain", f"+{r['gain_h']:.0f} h")
        c3.metric("Analogue réel", r["analogue"]["label"])
        st.info(f"Réduire le CR de **{red} %** porterait la vie à ~**{r['duree_estimee_h']:.0f} h** "
                f"(×{r['facteur_vie']:.1f}). Comparable à **{r['analogue']['label']}** "
                f"({r['analogue']['dilution']}).")
    st.markdown("### Points d'ancrage (runs réels)")
    st.dataframe(
        pd.DataFrame(ANCRES).rename(columns={"label": "Essai", "duree_h": "Durée (h)", "dilution": "Dilution"}),
        use_container_width=True, hide_index=True,
    )
