"""
merge_all_sources.py
--------------------
Fusionne les sources de données en un dataset hybride pondéré.

DEUX MODES :

  MODE PRÉ-STAGE (avant arrivée chez COTCO) :
    Source 2 — PHMSA public        poids ×1  (données réelles publiques)
    Source 3 — SPE/NACE papers     poids ×1  (données réelles publiques)
    Source 4 — Simulation DeWaard  poids ×0.5 (synthétique — complément physique)

  MODE FUSION (pendant/après stage) :
    Source 1 — COTCO réel          poids ×3  (données réelles propriétaires Kribi)
    + toutes les sources Pré-stage ci-dessus

RÈGLE ABSOLUE :
  Métriques (MAE, R², MAPE) calculées sur données COTCO réelles UNIQUEMENT.
  → Garantit l'honnêteté académique.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Colonnes communes obligatoires entre toutes les sources
COLONNES_COMMUNES = [
    # Features process
    "T_mean", "P_mean", "CO2_pct", "BSW_mean", "sable_ppm",
    "inhib_mean", "H2S_ppm",
    # Features dérivées (calculées par compute_features.py)
    "pCO2_bar", "CR_deWaard", "velocity_ms", "erosion_ratio",
    "delta_T_detente", "inhibitor_efficiency", "filter_fouling",
    "aggressivity_index",
    # Targets
    "CR_mesure", "RL_ans",
    # Traçabilité
    "source", "poids",
]

# Pondérations par source
POIDS = {
    "COTCO_reel":         3.0,
    "PHMSA_public":       1.0,
    "SPE_papers":         1.0,
    "simulation_DeWaard": 0.5,
}


def fusionner_toutes_sources(
    df_cotco:     pd.DataFrame | None = None,
    df_phmsa:     pd.DataFrame | None = None,
    df_spe:       pd.DataFrame | None = None,
    df_simulation: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Fusionne toutes les sources disponibles.
    Les sources None ou vides sont ignorées sans erreur.

    Returns:
        DataFrame hybride avec colonne 'source' et colonne 'poids'
    """
    sources = []

    if df_cotco is not None and len(df_cotco) > 0:
        df_cotco = df_cotco.copy()
        df_cotco["source"] = "COTCO_reel"
        df_cotco["poids"]  = POIDS["COTCO_reel"]
        sources.append(_harmoniser(df_cotco, "COTCO_reel"))
        print(f"  [OK] COTCO reel       : {len(df_cotco):>5} lignes (poids x3)")

    if df_phmsa is not None and len(df_phmsa) > 0:
        df_phmsa = df_phmsa.copy()
        df_phmsa["source"] = "PHMSA_public"
        df_phmsa["poids"]  = POIDS["PHMSA_public"]
        sources.append(_harmoniser(df_phmsa, "PHMSA_public"))
        print(f"  [OK] PHMSA public     : {len(df_phmsa):>5} lignes (poids x1)")

    if df_spe is not None and len(df_spe) > 0:
        df_spe = df_spe.copy()
        df_spe["source"] = "SPE_papers"
        df_spe["poids"]  = POIDS["SPE_papers"]
        sources.append(_harmoniser(df_spe, "SPE_papers"))
        print(f"  [OK] SPE/NACE papers  : {len(df_spe):>5} lignes (poids x1)")

    if df_simulation is not None and len(df_simulation) > 0:
        df_simulation = df_simulation.copy()
        df_simulation["source"] = "simulation_DeWaard"
        df_simulation["poids"]  = POIDS["simulation_DeWaard"]
        sources.append(_harmoniser(df_simulation, "simulation_DeWaard"))
        print(f"  [OK] Simulation       : {len(df_simulation):>5} lignes (poids x0.5)")

    if not sources:
        raise ValueError("Aucune source de données disponible.")

    df_final = pd.concat(sources, ignore_index=True)

    print(f"\n{'='*50}")
    print(f"  DATASET HYBRIDE FINAL : {len(df_final)} lignes")
    print(f"  Sources : {df_final['source'].value_counts().to_dict()}")
    print(f"  CR moyen : {df_final['CR_mesure'].mean():.4f} mm/an")
    print(f"{'='*50}\n")

    return df_final


def get_cotco_only(df_hybride: pd.DataFrame) -> pd.DataFrame:
    """
    Extrait uniquement les données COTCO réelles.
    Utilisé pour calculer les métriques finales (règle d'honnêteté académique).
    """
    return df_hybride[df_hybride["source"] == "COTCO_reel"].copy()


def split_train_test_temporal(
    df: pd.DataFrame,
    date_col: str = "date",
    test_ratio: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split temporel obligatoire (jamais aléatoire pour données séries temporelles).
    Train = passé, Test = futur.
    """
    if date_col not in df.columns:
        # Pas de date → split par index
        n = len(df)
        cut = int(n * (1 - test_ratio))
        return df.iloc[:cut].copy(), df.iloc[cut:].copy()

    df = df.sort_values(date_col)
    n = len(df)
    cut = int(n * (1 - test_ratio))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def sauvegarder(df: pd.DataFrame,
                path: str = "data/processed/dataset_ML_final.csv") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[ETL] Dataset hybride sauvegardé : {path}")
    print(f"      {len(df)} lignes | {df['source'].value_counts().to_dict()}")


# ── Harmonisation des schémas ─────────────────────────────────────────────────

def _harmoniser(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Harmonise un DataFrame source vers les colonnes communes.
    Les colonnes absentes sont remplies par NaN (géré en entraînement).
    """
    # Ajouter colonnes manquantes
    for col in COLONNES_COMMUNES:
        if col not in df.columns:
            df[col] = np.nan

    # Convertir en numérique sauf source/poids
    for col in COLONNES_COMMUNES:
        if col not in ("source", "poids"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Supprimer lignes sans target CR
    before = len(df)
    df = df.dropna(subset=["CR_mesure"])
    dropped = before - len(df)
    if dropped > 0:
        print(f"  [WARN] {source_name} : {dropped} lignes sans CR_mesure supprimées")

    return df[COLONNES_COMMUNES + [c for c in df.columns
                                    if c not in COLONNES_COMMUNES]]
