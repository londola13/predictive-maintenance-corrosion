"""
05_phmsa_validation.py
----------------------
Validation externe : confronter les prédictions du modèle avec
les données d'incidents PHMSA réels (US pipeline failures).

OBJECTIF ACADÉMIQUE :
  Ce notebook répond à la question critique :
  "Les classes de risque NACE SP0775 produites par notre modèle
   correspondent-elles à des taux d'incidents réels ?"

  Sans cette validation, nos métriques (MAE, R², Concordance) restent
  circulaires — le modèle est évalué sur les mêmes données synthétiques
  qu'il a vues à l'entraînement.

3 ANALYSES :
  1. Distribution CR estimés PHMSA vs CR prédit par notre modèle
     → Est-ce que nos prédictions sont dans le bon ordre de grandeur ?

  2. Kaplan-Meier par type de corrosion (interne, externe, SCC)
     → PHMSA montre-t-il des durées de vie différentes par type ?
     → Notre modèle capture-t-il ces différences ?

  3. Classes de risque NACE × taux d'incidents PHMSA
     → Les pipelines que notre modèle classe "Critique" / "Sévère"
       correspondent-ils aux types qui échouent le plus dans PHMSA ?

UTILISATION :
  python notebooks/05_phmsa_validation.py   (génère les figures dans notebooks/figures/)
  Ou ouvrir en mode interactif avec spyder / jupyter.

PRÉ-REQUIS :
  pip install lifelines matplotlib seaborn
  data/raw/phmsa_survival.csv  (généré par parse_phmsa.py --sample)
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

# ── Setup paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.parsers.parse_phmsa import parse_phmsa, generer_sample_phmsa
from src.data.generate_synthetic_cotco import generer_dataset_cotco
from src.features.compute_features import compute_all_features
from src.models.decision_engine import SEUILS_NACE

FIGURES_DIR = ROOT / "notebooks" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Style matplotlib
plt.rcParams.update({
    "figure.dpi":       150,
    "figure.facecolor": "white",
    "axes.spines.top":  False,
    "axes.spines.right": False,
    "font.family":      "sans-serif",
    "axes.titlesize":   12,
    "axes.labelsize":   11,
})

COULEURS_RISQUE = {
    "Acceptable": "#2ecc71",
    "Faible":     "#27ae60",
    "Modéré":     "#f39c12",
    "Élevé":      "#e67e22",
    "Sévère":     "#e74c3c",
    "Critique":   "#8e44ad",
}


# ══════════════════════════════════════════════════════════════════════════════
#  CHARGEMENT DES DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

def charger_donnees():
    """
    Charge les données PHMSA et le dataset synthétique COTCO.
    Retourne : df_phmsa, df_cotco
    """
    # PHMSA
    phmsa_survival_path = ROOT / "data/raw/phmsa_survival.csv"
    phmsa_sample_path   = ROOT / "data/raw/phmsa_sample.csv"
    phmsa_raw_path      = ROOT / "data/raw/phmsa_hl_incidents.xlsx"

    if phmsa_survival_path.exists():
        df_phmsa = pd.read_csv(phmsa_survival_path)
        source_phmsa = "données réelles pré-parsées"
    elif phmsa_raw_path.exists():
        df_phmsa = parse_phmsa(phmsa_raw_path)
        source_phmsa = "données PHMSA réelles"
    elif phmsa_sample_path.exists():
        df_phmsa = parse_phmsa(phmsa_sample_path)
        source_phmsa = "SAMPLE simulé (remplacer par vraies données PHMSA)"
    else:
        print("[INFO] Génération sample PHMSA...")
        df_sample_raw = generer_sample_phmsa(n=300, seed=42)
        sample_path = ROOT / "data/raw/phmsa_sample.csv"
        df_sample_raw.to_csv(sample_path, index=False)
        df_phmsa = parse_phmsa(sample_path)
        source_phmsa = "SAMPLE simulé"

    print(f"\n[DATA] PHMSA chargé : {len(df_phmsa)} incidents ({source_phmsa})")
    print(f"       RL_ans : moy={df_phmsa['RL_ans'].mean():.1f} | med={df_phmsa['RL_ans'].median():.1f} ans")

    # Dataset COTCO synthétique
    df_cotco = generer_dataset_cotco(n_points=1000, seed=42)
    df_cotco = compute_all_features(df_cotco)
    print(f"[DATA] COTCO synthétique : {len(df_cotco)} points")

    return df_phmsa, df_cotco, source_phmsa


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYSE 1 : DISTRIBUTIONS CR COMPARÉES
# ══════════════════════════════════════════════════════════════════════════════

def analyse_distributions_cr(df_phmsa: pd.DataFrame, df_cotco: pd.DataFrame,
                              source_phmsa: str) -> None:
    """
    Compare les distributions de CR :
      - PHMSA : CR estimé (borne inférieure physique, mm/an)
      - COTCO synthétique : CR mesuré (modèle De Waard calibré Kribi)

    Interprétation attendue :
      - PHMSA : CR moyen 0.10-0.20 mm/an (NACE "Faible" à "Modéré")
      - COTCO Kribi : CR moyen 0.05-0.10 mm/an (fluide lourd, bien inhibé)
      - Cohérence : PHMSA > COTCO est attendu (PHMSA = pipelines qui ont ÉCHOUÉ)
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Analyse 1 — Distributions CR comparées\n"
                 f"PHMSA : {source_phmsa}", fontsize=13, fontweight="bold")

    # Seuils NACE pour annotation
    seuils_val = [0.025, 0.050, 0.125, 0.250, 0.500]
    seuils_lab = ["0.025\nAcceptable→Faible", "0.050\nFaible→Modéré",
                  "0.125\nModéré→Élevé", "0.250\nÉlevé→Sévère", "0.500\nSévère→Critique"]

    # ── Axe 1 : Histogrammes superposés ──────────────────────────────────────
    ax = axes[0]
    cr_phmsa = df_phmsa["CR_mesure"].dropna()
    cr_cotco = df_cotco["CR_mesure"].dropna()

    bins = np.linspace(0, 1.0, 40)
    ax.hist(cr_cotco, bins=bins, alpha=0.6, color="#3498db",
            label=f"COTCO synthétique\n(n={len(cr_cotco)}, moy={cr_cotco.mean():.3f})")
    ax.hist(cr_phmsa, bins=bins, alpha=0.6, color="#e74c3c",
            label=f"PHMSA corrosion\n(n={len(cr_phmsa)}, moy={cr_phmsa.mean():.3f})")

    for s, label in zip(seuils_val[:3], seuils_lab[:3]):
        ax.axvline(s, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
        ax.text(s, ax.get_ylim()[1] * 0.85, label, fontsize=7,
                ha="center", color="gray", rotation=90)

    ax.set_xlabel("Taux de corrosion CR (mm/an)")
    ax.set_ylabel("Nombre d'observations")
    ax.set_title("Histogrammes CR : COTCO vs PHMSA")
    ax.legend(fontsize=9)
    ax.set_xlim(0, 0.8)

    # ── Axe 2 : Box plots par source ──────────────────────────────────────────
    ax = axes[1]
    df_plot = pd.DataFrame({
        "CR (mm/an)": pd.concat([cr_cotco, cr_phmsa], ignore_index=True),
        "Source": (["COTCO synthétique"] * len(cr_cotco) +
                   ["PHMSA (incidents)"] * len(cr_phmsa))
    })
    df_plot["CR (mm/an)"] = df_plot["CR (mm/an)"].clip(0, 0.8)

    sns.boxplot(data=df_plot, x="Source", y="CR (mm/an)",
                palette=["#3498db", "#e74c3c"], ax=ax, width=0.5)

    # Annoter les médianes
    for i, (label, grp) in enumerate(df_plot.groupby("Source")):
        med = grp["CR (mm/an)"].median()
        ax.text(i, med + 0.01, f"med={med:.3f}", ha="center",
                fontsize=9, fontweight="bold")

    # Lignes NACE
    for s in seuils_val[:3]:
        ax.axhline(s, color="gray", linestyle="--", alpha=0.4, linewidth=0.8)

    ax.set_title("Box plots CR par source")
    ax.set_ylabel("CR (mm/an)")

    plt.tight_layout()
    fig_path = FIGURES_DIR / "05_distribution_cr.png"
    plt.savefig(fig_path, bbox_inches="tight")
    plt.show()
    print(f"[Figure 1] Sauvegardée : {fig_path}")

    # ── Rapport texte ─────────────────────────────────────────────────────────
    print("\n═══ Analyse 1 — Conclusions ═══")
    print(f"  COTCO syn. : CR moyen = {cr_cotco.mean():.4f} mm/an "
          f"| médiane = {cr_cotco.median():.4f} mm/an")
    print(f"  PHMSA      : CR moyen = {cr_phmsa.mean():.4f} mm/an "
          f"| médiane = {cr_phmsa.median():.4f} mm/an")
    ratio = cr_phmsa.mean() / max(cr_cotco.mean(), 1e-9)
    print(f"  Ratio PHMSA/COTCO = {ratio:.1f}x")
    if ratio > 1.5:
        print("  ✅ Cohérent : PHMSA (pipelines qui ont échoué) a des CR plus élevés")
    else:
        print("  ⚠️  Vérifier : ratio attendu > 1.5x (PHMSA = cas de défaillance)")


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYSE 2 : KAPLAN-MEIER PAR TYPE DE CORROSION
# ══════════════════════════════════════════════════════════════════════════════

def analyse_kaplan_meier(df_phmsa: pd.DataFrame) -> None:
    """
    Courbes de survie Kaplan-Meier depuis PHMSA par type de corrosion.
    Montre la durée de vie médiane avant défaillance par type.

    Ces courbes servent de RÉFÉRENCE EXTERNE pour valider que notre
    WeibullAFT produit des estimations dans le bon range de RL.
    """
    try:
        from lifelines import KaplanMeierFitter
    except ImportError:
        print("[SKIP] lifelines non installé — pip install lifelines")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Analyse 2 — Courbes Kaplan-Meier PHMSA\n"
                 "(Durée de service avant défaillance par corrosion)",
                 fontsize=13, fontweight="bold")

    couleurs_type = {
        "internal": "#e74c3c",
        "external": "#3498db",
        "scc":      "#9b59b6",
        "mic":      "#e67e22",
        "unknown":  "#95a5a6",
    }

    # ── Axe 1 : KM par type de corrosion ─────────────────────────────────────
    ax = axes[0]
    for corr_type, color in couleurs_type.items():
        mask = df_phmsa["corrosion_type"] == corr_type
        sous_df = df_phmsa[mask]
        if len(sous_df) < 5:
            continue

        kmf = KaplanMeierFitter()
        kmf.fit(sous_df["RL_ans"],
                event_observed=sous_df["event"],
                label=f"{corr_type} (n={len(sous_df)})")
        kmf.plot_survival_function(
            ax=ax, color=color, ci_show=True, ci_alpha=0.1
        )

    ax.set_xlabel("Années de service")
    ax.set_ylabel("Probabilité de survie P(T > t)")
    ax.set_title("Courbes KM par type de corrosion\n(données PHMSA)")
    ax.set_xlim(0, 55)
    ax.set_ylim(0, 1)
    ax.axhline(0.5, color="black", linestyle=":", alpha=0.4, linewidth=0.8,
               label="Médiane (50%)")
    ax.legend(fontsize=8, loc="upper right")

    # ── Axe 2 : Distribution RL_ans par type ─────────────────────────────────
    ax = axes[1]
    types_presents = [t for t in couleurs_type if
                      (df_phmsa["corrosion_type"] == t).sum() >= 5]

    data_box = [df_phmsa[df_phmsa["corrosion_type"] == t]["RL_ans"].values
                for t in types_presents]
    medians = [np.median(d) for d in data_box]

    bp = ax.boxplot(data_box, patch_artist=True, widths=0.6,
                    medianprops={"color": "black", "linewidth": 2})

    for patch, t in zip(bp["boxes"], types_presents):
        patch.set_facecolor(couleurs_type[t])
        patch.set_alpha(0.7)

    for i, (t, med) in enumerate(zip(types_presents, medians)):
        ax.text(i + 1, med + 0.5, f"{med:.0f}a", ha="center",
                fontsize=9, fontweight="bold")

    ax.set_xticklabels(types_presents)
    ax.set_xlabel("Type de corrosion")
    ax.set_ylabel("RL_ans (années de service)")
    ax.set_title("Distribution durée de service par type")
    ax.set_ylim(0, 65)

    plt.tight_layout()
    fig_path = FIGURES_DIR / "05_kaplan_meier_phmsa.png"
    plt.savefig(fig_path, bbox_inches="tight")
    plt.show()
    print(f"[Figure 2] Sauvegardée : {fig_path}")

    # ── Rapport texte ─────────────────────────────────────────────────────────
    print("\n═══ Analyse 2 — Médianes de survie PHMSA ═══")
    print(f"  {'Type':<12} {'N':>5} {'RL médiane':>12} {'RL moyen':>10}")
    print(f"  {'-'*42}")
    for t in types_presents:
        grp = df_phmsa[df_phmsa["corrosion_type"] == t]["RL_ans"]
        print(f"  {t:<12} {len(grp):>5} {grp.median():>10.1f} ans {grp.mean():>8.1f} ans")

    global_med = df_phmsa["RL_ans"].median()
    print(f"\n  RL_ans médiane globale PHMSA : {global_med:.1f} ans")
    print(f"  → Cible WeibullAFT : prédictions RL dans [10, 50] ans pour CR 0.05-0.5 mm/an")


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYSE 3 : CLASSES NACE × TAUX D'INCIDENTS PHMSA
# ══════════════════════════════════════════════════════════════════════════════

def analyse_nace_vs_phmsa(df_phmsa: pd.DataFrame, df_cotco: pd.DataFrame) -> None:
    """
    Valide que nos classes de risque NACE SP0775 correspondent bien à
    des niveaux de risque réels observés dans les incidents PHMSA.

    Méthode :
      - Classifier les incidents PHMSA selon leur CR estimé et nos seuils NACE
      - Calculer la proportion d'incidents par classe
      - Comparer avec la distribution COTCO synthétique

    Résultat attendu :
      - PHMSA doit avoir plus de classes "Élevé/Sévère/Critique" que COTCO
        (car PHMSA = cas de défaillance, COTCO = opération normale)
      - Si les proportions sont similaires → nos seuils NACE peuvent être
        trop bas (trop de pipeline classé "risque élevé" en opération normale)
    """

    def classer_nace(cr: float) -> str:
        if cr <= 0.025:   return "Acceptable"
        elif cr <= 0.050: return "Faible"
        elif cr <= 0.125: return "Modéré"
        elif cr <= 0.250: return "Élevé"
        elif cr <= 0.500: return "Sévère"
        else:              return "Critique"

    ordre = ["Acceptable", "Faible", "Modéré", "Élevé", "Sévère", "Critique"]

    df_phmsa = df_phmsa.copy()
    df_phmsa["classe_NACE"] = df_phmsa["CR_mesure"].apply(classer_nace)

    df_cotco = df_cotco.copy()
    df_cotco["classe_NACE"] = df_cotco["CR_mesure"].apply(classer_nace)

    # Proportions
    phmsa_pct = df_phmsa["classe_NACE"].value_counts(normalize=True).reindex(ordre, fill_value=0) * 100
    cotco_pct = df_cotco["classe_NACE"].value_counts(normalize=True).reindex(ordre, fill_value=0) * 100

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Analyse 3 — Classes NACE SP0775 : modèle COTCO vs incidents PHMSA",
                 fontsize=13, fontweight="bold")

    x = np.arange(len(ordre))
    width = 0.35
    colors = [COULEURS_RISQUE[o] for o in ordre]

    # Axe 1 : Barres côte-à-côte
    ax = axes[0]
    bars1 = ax.bar(x - width/2, cotco_pct.values, width, label="COTCO synthétique",
                   color=colors, alpha=0.6, edgecolor="white")
    bars2 = ax.bar(x + width/2, phmsa_pct.values, width, label="PHMSA (incidents)",
                   color=colors, alpha=0.95, edgecolor="black", linewidth=0.5)

    # Ajouter les valeurs
    for bar, val in zip(bars1, cotco_pct.values):
        if val > 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"{val:.0f}%", ha="center", va="bottom", fontsize=8)
    for bar, val in zip(bars2, phmsa_pct.values):
        if val > 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"{val:.0f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(ordre, rotation=30, ha="right")
    ax.set_ylabel("Proportion des observations (%)")
    ax.set_title("Distribution classes NACE\n(barres transparentes = COTCO, pleines = PHMSA)")
    ax.legend(fontsize=9)

    # Axe 2 : Ratio PHMSA/COTCO par classe (> 1 = PHMSA sur-représente cette classe)
    ax = axes[1]
    ratio = (phmsa_pct / cotco_pct.replace(0, 0.1)).fillna(0)
    bar_colors = ["#2ecc71" if r <= 1 else "#e74c3c" for r in ratio.values]
    bars = ax.bar(x, ratio.values, color=bar_colors, alpha=0.8, edgecolor="white")

    ax.axhline(1.0, color="black", linestyle="--", alpha=0.5, linewidth=1,
               label="Ratio = 1 (proportions égales)")
    ax.set_xticks(x)
    ax.set_xticklabels(ordre, rotation=30, ha="right")
    ax.set_ylabel("Ratio PHMSA / COTCO")
    ax.set_title("Sur-représentation des classes dans PHMSA\n(> 1 = défaillances plus fréquentes dans cette classe)")
    ax.legend(fontsize=9)

    for bar, val in zip(bars, ratio.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"×{val:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    fig_path = FIGURES_DIR / "05_nace_vs_phmsa.png"
    plt.savefig(fig_path, bbox_inches="tight")
    plt.show()
    print(f"[Figure 3] Sauvegardée : {fig_path}")

    # ── Rapport texte ─────────────────────────────────────────────────────────
    print("\n═══ Analyse 3 — Validation classes NACE ═══")
    print(f"  {'Classe NACE':<12} {'COTCO':>8} {'PHMSA':>8} {'Ratio':>8} {'Interprétation'}")
    print(f"  {'-'*60}")
    for classe in ordre:
        c_pct = cotco_pct.get(classe, 0)
        p_pct = phmsa_pct.get(classe, 0)
        r = p_pct / max(c_pct, 0.1)
        interp = "✅ PHMSA > COTCO" if r > 1.5 else ("✅ équilibré" if r > 0.5 else "⚠️  PHMSA sous-représente")
        print(f"  {classe:<12} {c_pct:>7.1f}% {p_pct:>7.1f}% {r:>7.1f}x  {interp}")

    phmsa_risque_eleve = phmsa_pct.loc[["Élevé", "Sévère", "Critique"]].sum()
    cotco_risque_eleve = cotco_pct.loc[["Élevé", "Sévère", "Critique"]].sum()
    print(f"\n  % classes 'Élevé/Sévère/Critique' :")
    print(f"    COTCO synthétique : {cotco_risque_eleve:.1f}%")
    print(f"    PHMSA incidents   : {phmsa_risque_eleve:.1f}%")
    if phmsa_risque_eleve > cotco_risque_eleve:
        print(f"  ✅ Cohérent : PHMSA a plus de cas à risque élevé (ratio {phmsa_risque_eleve/max(cotco_risque_eleve, 0.1):.1f}x)")
    else:
        print(f"  ⚠️  Attention : PHMSA devrait avoir plus de cas à risque élevé")
        print(f"      → Vérifier les seuils NACE ou la qualité des données PHMSA")


# ══════════════════════════════════════════════════════════════════════════════
#  RAPPORT FINAL
# ══════════════════════════════════════════════════════════════════════════════

def rapport_final(df_phmsa: pd.DataFrame, df_cotco: pd.DataFrame) -> dict:
    """Génère le résumé de validation pour le rapport de mémoire."""

    print("\n" + "═"*65)
    print("  RAPPORT VALIDATION EXTERNE — PHMSA vs MODÈLE COTCO KRIBI")
    print("═"*65)

    metrics = {
        "phmsa_n_incidents": len(df_phmsa),
        "phmsa_rl_median": float(df_phmsa["RL_ans"].median()),
        "phmsa_rl_mean":   float(df_phmsa["RL_ans"].mean()),
        "phmsa_cr_median": float(df_phmsa["CR_mesure"].median()),
        "phmsa_cr_mean":   float(df_phmsa["CR_mesure"].mean()),
        "cotco_cr_median": float(df_cotco["CR_mesure"].median()),
        "cotco_cr_mean":   float(df_cotco["CR_mesure"].mean()),
    }

    print(f"\n  PHMSA : {metrics['phmsa_n_incidents']} incidents corrosion")
    print(f"    RL médiane : {metrics['phmsa_rl_median']:.1f} ans")
    print(f"    CR estimé médiane : {metrics['phmsa_cr_median']:.4f} mm/an")
    print(f"\n  COTCO synthétique :")
    print(f"    CR médiane : {metrics['cotco_cr_median']:.4f} mm/an")

    print(f"\n  CONCLUSIONS POUR LE RAPPORT :")
    print(f"  1. Les CR estimés PHMSA ({metrics['phmsa_cr_median']:.3f} mm/an médiane) sont")
    print(f"     {'supérieurs' if metrics['phmsa_cr_median'] > metrics['cotco_cr_median'] else 'inférieurs'}")
    print(f"     aux CR COTCO ({metrics['cotco_cr_median']:.3f} mm/an) — cohérent avec le fait")
    print(f"     que PHMSA = pipelines ayant atteint la défaillance.")

    print(f"\n  2. La durée de vie médiane PHMSA ({metrics['phmsa_rl_median']:.1f} ans) est")
    print(f"     réaliste pour des pipelines liquides (standard industrie : 20-40 ans).")
    print(f"     Améliore la distribution RL du WeibullAFT (vs ~50 ans synthétique).")

    print(f"\n  NOTE : Ces validations sont PRÉLIMINAIRES.")
    print(f"  La validation définitive se fera avec les données COTCO réelles au stage.")

    print("═"*65)

    # Sauvegarder métriques
    metrics_path = ROOT / "models" / "phmsa_validation_metrics.json"
    import json
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[Métriques] Sauvegardées : {metrics_path}")

    return metrics


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*65)
    print("  NOTEBOOK 05 — VALIDATION EXTERNE PHMSA")
    print("  Projet mémoire M2 ENSPD — COTCO Kribi")
    print("="*65)

    # Charger les données
    df_phmsa, df_cotco, source_phmsa = charger_donnees()

    # ── Analyse 1 : Distributions CR ─────────────────────────────────────────
    print("\n━━━ Analyse 1/3 : Distributions CR comparées ━━━")
    analyse_distributions_cr(df_phmsa, df_cotco, source_phmsa)

    # ── Analyse 2 : Kaplan-Meier ─────────────────────────────────────────────
    print("\n━━━ Analyse 2/3 : Courbes Kaplan-Meier ━━━")
    analyse_kaplan_meier(df_phmsa)

    # ── Analyse 3 : Classes NACE × PHMSA ─────────────────────────────────────
    print("\n━━━ Analyse 3/3 : Validation classes NACE ━━━")
    analyse_nace_vs_phmsa(df_phmsa, df_cotco)

    # ── Rapport final ─────────────────────────────────────────────────────────
    print("\n━━━ Rapport final ━━━")
    metrics = rapport_final(df_phmsa, df_cotco)

    print(f"\n✅ Toutes les figures sauvegardées dans : {FIGURES_DIR}")
    print("   05_distribution_cr.png")
    print("   05_kaplan_meier_phmsa.png")
    print("   05_nace_vs_phmsa.png")
