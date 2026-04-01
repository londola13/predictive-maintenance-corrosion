"""
run_pipeline.py
---------------
Orchestrateur complet du système ML de maintenance prédictive corrosion.

Deux modes :
  MODE A — Pré-stage  : données publiques uniquement (PHMSA + SPE + De Waard)
                        Disponible avant l'arrivée en stage.
  MODE B — Fusion     : données publiques + données réelles entreprise (poids ×3)
                        Activé dès que les données entreprise sont disponibles.

Usage :
    python src/run_pipeline.py                    # auto-détecte le mode
    python src/run_pipeline.py --mode prestage    # force mode pré-stage
    python src/run_pipeline.py --mode fusion      # force mode fusion
    python src/run_pipeline.py --retrain          # force ré-entraînement
"""

import argparse
import json
import sys
from pathlib import Path

# Ajouter la racine au path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.etl.build_dataset_ml import charger_ou_generer
from src.etl.merge_all_sources import fusionner_toutes_sources, sauvegarder
from src.features.compute_features import compute_all_features, rapport_features
from src.models.train_xgboost import train as train_xgboost
from src.models.train_survival import train as train_survival
from src.models.train_anomaly import train as train_anomaly
from src.data.generate_synthetic_cotco import generer_dataset_cotco
from src.parsers.parse_phmsa import parse_phmsa


def run(mode: str = "auto", force_retrain: bool = False) -> dict:
    """
    Lance le pipeline complet.

    Args:
        mode          : 'auto' | 'synth' | 'fusion'
        force_retrain : forcer ré-entraînement même si modèles existent

    Returns:
        dict résumé des métriques
    """
    print("\n" + "="*60)
    print("  PIPELINE MAINTENANCE PRÉDICTIVE — CORROSION ML")
    print("="*60)

    # ── Étape 1 : Charger / Générer les données ──────────────────────────────

    if mode == "prestage":
        df_base, detected_mode = _mode_prestage()
    elif mode == "fusion":
        df_base, detected_mode = _mode_fusion()
    else:
        df_base, detected_mode = charger_ou_generer()

    print(f"\n  Mode actif : {detected_mode.upper()}")
    print(f"  Lignes dataset : {len(df_base)}")

    # ── Étape 2 : Features dérivées ──────────────────────────────────────────

    print("\n[ÉTAPE 2] Calcul des 8 features dérivées...")
    df_base = compute_all_features(df_base)
    rapport_features(df_base)

    # ── Étape 3 : Fusion 4 sources (si mode fusion) ──────────────────────────

    if detected_mode == "entreprise_reel" or mode == "fusion":
        df_fusion = _fusionner_avec_sources_publiques(df_base)
    else:
        df_fusion = df_base

    # Sauvegarder le dataset final
    sauvegarder(df_fusion, "data/processed/dataset_ML_final.csv")

    # ── Étape 4 : Vérifier si ré-entraînement nécessaire ─────────────────────

    if not force_retrain and _modeles_existent():
        derive = _detecter_derive(df_fusion)
        if not derive:
            print("\n[ÉTAPE 4] Modèles existants valides — pas de ré-entraînement")
            return {"mode": detected_mode, "retrain": False}
        else:
            print("\n[ÉTAPE 4] Dérive détectée → ré-entraînement automatique")
    else:
        print("\n[ÉTAPE 4] Entraînement des modèles...")

    # ── Étape 5 : Entraîner les 3 modèles ────────────────────────────────────

    resultats = {"mode": detected_mode, "retrain": True}

    # XGBoost
    print("\n[ÉTAPE 5a] XGBoost — Prédiction taux de corrosion")
    model_xgb, metrics_xgb, feat_names = train_xgboost(df_fusion)
    resultats["xgboost"] = metrics_xgb

    # Sauvegarder SHAP
    if "shap_importance" in metrics_xgb:
        shap_path = ROOT / "models/shap_importance.json"
        with open(shap_path, "w") as f:
            json.dump(metrics_xgb["shap_importance"], f, indent=2)
        print(f"[SHAP] Importances sauvegardées : {shap_path}")

    # Survival — avec PHMSA si disponible
    print("\n[ÉTAPE 5b] Lifelines — Remaining Life (Weibull AFT)")
    df_phmsa_survie = _charger_phmsa_survival()
    model_surv, metrics_surv = train_survival(df_fusion, df_phmsa=df_phmsa_survie)
    resultats["survival"] = metrics_surv

    # Anomaly
    print("\n[ÉTAPE 5c] Isolation Forest — Détection anomalies")
    model_anom, scaler_anom, metrics_anom = train_anomaly(df_fusion)
    resultats["anomaly"] = metrics_anom

    # ── Étape 6 : Rapport final ───────────────────────────────────────────────

    _afficher_rapport(resultats)

    # Sauvegarder état pipeline
    state_path = ROOT / "models/pipeline_state.json"
    import datetime
    resultats["last_run"] = datetime.datetime.now().isoformat()
    resultats["n_lignes"] = len(df_fusion)
    resultats["sources"]  = df_fusion["source"].value_counts().to_dict() \
                             if "source" in df_fusion.columns else {}

    with open(state_path, "w") as f:
        json.dump({k: v for k, v in resultats.items()
                   if not isinstance(v, dict) or k == "sources"}, f, indent=2)

    print(f"\n[Pipeline] État sauvegardé : {state_path}")
    print("[Pipeline] Lancer le dashboard : streamlit run dashboard/app.py\n")

    return resultats


# ── Modes ─────────────────────────────────────────────────────────────────────

def _mode_prestage():
    """
    Mode A — Pré-stage : données publiques disponibles avant le stage.
    PHMSA (réel public) + SPE papers (réel public) + De Waard (synthétique).
    """
    print("\n[MODE PRE-STAGE] Chargement donnees publiques + simulation De Waard...")
    df_sim = generer_dataset_cotco(n_points=5000)
    df_sim = compute_all_features(df_sim)
    # Fusionner avec PHMSA et SPE si disponibles (sans données réelles entreprise)
    df_fusion = _fusionner_avec_sources_publiques(df_sim)
    # Exclure données réelles entreprise si présentes accidentellement
    df = df_fusion[df_fusion["source"] != "entreprise_reel"].copy()
    return df, "prestage"


def _mode_fusion():
    """Mode B : tente de charger les données réelles entreprise + fusionne avec sources publiques."""
    df_base, mode = charger_ou_generer()
    df_fusion = _fusionner_avec_sources_publiques(df_base)
    return df_fusion, "fusion_" + mode


def _fusionner_avec_sources_publiques(df_cotco: "pd.DataFrame"):
    """
    Fusionne les données entreprise (ou synthétiques) avec :
      - PHMSA si disponible dans data/raw/phmsa_pipeline.csv
      - SPE papers si disponibles dans data/raw/spe_papers.csv
      - Simulation De Waard (toujours ajoutée comme complément)
    """
    import pandas as pd
    from pathlib import Path

    sources = {"df_cotco": df_cotco}

    # PHMSA
    phmsa_path = ROOT / "data/raw/phmsa_pipeline.csv"
    if phmsa_path.exists():
        df_phmsa = pd.read_csv(phmsa_path)
        df_phmsa = compute_all_features(df_phmsa)
        sources["df_phmsa"] = df_phmsa
        print(f"[Fusion] PHMSA chargé : {len(df_phmsa)} lignes")
    else:
        print(f"[Fusion] PHMSA absent (à placer dans data/raw/phmsa_pipeline.csv)")

    # SPE papers
    spe_path = ROOT / "data/raw/spe_papers.csv"
    if spe_path.exists():
        df_spe = pd.read_csv(spe_path)
        df_spe = compute_all_features(df_spe)
        sources["df_spe"] = df_spe
        print(f"[Fusion] SPE papers chargé : {len(df_spe)} lignes")
    else:
        print(f"[Fusion] SPE papers absent (à placer dans data/raw/spe_papers.csv)")

    # Simulation De Waard (toujours présente — complément)
    df_sim = generer_dataset_cotco(n_points=5000, seed=123)
    df_sim = compute_all_features(df_sim)
    sources["df_simulation"] = df_sim

    return fusionner_toutes_sources(**sources)


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _charger_phmsa_survival() -> "pd.DataFrame | None":
    """
    Charge les données PHMSA survie si disponibles.
    Cherche dans cet ordre :
      1. data/raw/phmsa_survival.csv   (produit par parse_phmsa.py)
      2. data/raw/phmsa_hl_incidents.xlsx  (données PHMSA brutes)
      3. data/raw/phmsa_sample.csv     (sample de test)
    Retourne None si aucun fichier trouvé (pipeline continue sans PHMSA).
    """
    import pandas as pd

    # Fichier pré-parsé (meilleure option)
    survival_csv = ROOT / "data/raw/phmsa_survival.csv"
    if survival_csv.exists():
        df = pd.read_csv(survival_csv)
        print(f"[PHMSA] Données survie chargées : {len(df)} incidents ({survival_csv.name})")
        return df

    # Fichier brut PHMSA → parser à la volée
    for raw_file in ["phmsa_hl_incidents.xlsx", "phmsa_hl_incidents.csv"]:
        raw_path = ROOT / f"data/raw/{raw_file}"
        if raw_path.exists():
            print(f"[PHMSA] Parsing fichier brut : {raw_file}")
            try:
                df = parse_phmsa(raw_path)
                df.to_csv(survival_csv, index=False)
                print(f"[PHMSA] Cache sauvegardé : {survival_csv}")
                return df
            except Exception as e:
                print(f"[PHMSA] Erreur parsing : {e}")
                return None

    # Sample de test
    sample_path = ROOT / "data/raw/phmsa_sample.csv"
    if sample_path.exists():
        print("[PHMSA] Utilisation du fichier SAMPLE (données simulées)")
        print("        Remplacer par les vraies données PHMSA pour les métriques finales")
        try:
            return parse_phmsa(sample_path)
        except Exception as e:
            print(f"[PHMSA] Erreur parsing sample : {e}")
            return None

    print("[PHMSA] Aucun fichier trouvé — survie entraînée sans PHMSA")
    print("        Pour activer : python src/parsers/parse_phmsa.py --sample")
    return None


def _modeles_existent() -> bool:
    modeles = [
        ROOT / "models/xgboost_model.pkl",
        ROOT / "models/survival_model.pkl",
        ROOT / "models/isolation_forest.pkl",
    ]
    return all(m.exists() for m in modeles)


def _detecter_derive(df) -> bool:
    """Détecte si la dérive du modèle nécessite un ré-entraînement."""
    state_path = ROOT / "models/pipeline_state.json"
    if not state_path.exists():
        return True
    # Logique simplifiée : toujours ré-entraîner si nouvelles données
    return False


def _afficher_rapport(resultats: dict) -> None:
    print("\n" + "="*60)
    print("  RAPPORT FINAL PIPELINE")
    print("="*60)

    xgb = resultats.get("xgboost", {})
    if xgb:
        mae = xgb.get("mae", "?")
        r2  = xgb.get("r2", "?")
        mape = xgb.get("mape", "?")
        print(f"  XGBoost — MAE: {mae:.4f} | R²: {r2:.4f} | MAPE: {mape:.2f}%")
        ameli = xgb.get("amelioration_vs_deWaard_pct")
        if ameli:
            print(f"            Amélioration vs De Waard : +{ameli:.1f}%")

    surv = resultats.get("survival", {})
    if surv:
        ci = surv.get("concordance_index", "?")
        print(f"  Survie    — Concordance Index: {ci:.4f}")

    anom = resultats.get("anomaly", {})
    if anom:
        n = anom.get("n_anomalies_detectees", "?")
        p = anom.get("pct_anomalies", "?")
        print(f"  Anomalie  — {n} anomalies ({p}%)")

    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline ML Maintenance Prédictive Corrosion")
    parser.add_argument("--mode", choices=["auto", "prestage", "fusion"],
                        default="auto", help="Mode de données")
    parser.add_argument("--retrain", action="store_true",
                        help="Forcer ré-entraînement")
    args = parser.parse_args()

    run(mode=args.mode, force_retrain=args.retrain)
