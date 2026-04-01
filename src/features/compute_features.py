"""
compute_features.py
-------------------
Calcul des 8 features dérivées physiquement pertinentes
à partir des 20 tags DCS de la Station Kribi.

Appliqué à toutes les sources (COTCO réel, PHMSA, SPE, simulation).
"""

import numpy as np
import pandas as pd

# Paramètres physiques Station Kribi
RHO_M = 850          # kg/m3 — densité pétrole brut Doba
D_M   = 0.508        # m — diamètre ligne principale
INHIB_DOSE_CIBLE = 40  # mg/L — dose optimale inhibiteur


def compute_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les 8 features dérivées et les ajoute au DataFrame.
    Tolère les colonnes manquantes (calcule ce qui est possible).

    Args:
        df : DataFrame avec colonnes DCS standards

    Returns:
        DataFrame enrichi des 8 features
    """
    df = df.copy()

    df = _feature_pCO2(df)
    df = _feature_CR_deWaard(df)
    df = _feature_velocity(df)
    df = _feature_erosion_ratio(df)
    df = _feature_delta_T(df)
    df = _feature_inhibitor_efficiency(df)
    df = _feature_filter_fouling(df)
    df = _feature_aggressivity(df)

    return df


# ── Feature 1 — Pression partielle CO2 ───────────────────────────────────────

def _feature_pCO2(df: pd.DataFrame) -> pd.DataFrame:
    """
    pCO2 (bar) = P_mean × CO2_pct / 100
    Référence : NORSOK M-506
    Seuils NACE : < 0.5 faible | 0.5-2 modéré | > 2 sévère
    """
    if "P_mean" in df.columns and "CO2_pct" in df.columns:
        df["pCO2_bar"] = df["P_mean"] * df["CO2_pct"] / 100
        df["pCO2_bar"] = df["pCO2_bar"].clip(0.001, 20)
    return df


# ── Feature 2 — Taux de corrosion De Waard (ancre physique) ──────────────────

def _feature_CR_deWaard(df: pd.DataFrame) -> pd.DataFrame:
    """
    CR_DeWaard (mm/an) = 10^(5.8 - 1710/T_K + 0.67*log10(pCO2))
    Référence : De Waard & Milliams (1991), NORSOK M-506

    XGBoost va corriger cet écart avec la réalité COTCO.
    """
    if "T_mean" in df.columns and "pCO2_bar" in df.columns:
        T_K = df["T_mean"] + 273.15
        pCO2 = df["pCO2_bar"].clip(0.001)
        df["CR_deWaard"] = 10 ** (5.8 - 1710 / T_K + 0.67 * np.log10(pCO2))
        df["CR_deWaard"] = df["CR_deWaard"].clip(0.001, 20)
    elif "CR_deWaard" not in df.columns:
        df["CR_deWaard"] = np.nan
    return df


# ── Feature 3 — Vélocité fluide ──────────────────────────────────────────────

def _feature_velocity(df: pd.DataFrame) -> pd.DataFrame:
    """
    velocity_ms (m/s) = debit_vol / (3600 × π × r²)
    Diamètre Kribi = 508 mm (20 pouces)
    """
    if "debit_vol" in df.columns:
        r = D_M / 2
        df["velocity_ms"] = df["debit_vol"] / (3600 * np.pi * r ** 2)
        df["velocity_ms"] = df["velocity_ms"].clip(0, 15)
    elif "velocity_ms" not in df.columns:
        df["velocity_ms"] = np.nan
    return df


# ── Feature 4 — Ratio érosif ─────────────────────────────────────────────────

def _feature_erosion_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    erosion_ratio = velocity_ms / V_érosive
    V_érosive = 100 / √ρ_m (API RP 14E)
    Seuils : < 0.5 sûr | 0.5-1 surveillance | > 1 érosion active
    """
    if "velocity_ms" in df.columns:
        V_erosive = 100 / np.sqrt(RHO_M)  # ≈ 3.43 m/s
        df["erosion_ratio"] = df["velocity_ms"] / V_erosive
        df["erosion_ratio"] = df["erosion_ratio"].clip(0, 10)
    return df


# ── Feature 5 — ΔT détente ───────────────────────────────────────────────────

def _feature_delta_T(df: pd.DataFrame) -> pd.DataFrame:
    """
    delta_T_detente (°C) = T_mean - T_aval
    Détecte le risque de condensation → corrosion localisée.
    Seuils : < 10°C faible | 10-20°C moyen | > 20°C critique
    """
    if "T_mean" in df.columns and "T_aval" in df.columns:
        df["delta_T_detente"] = (df["T_mean"] - df["T_aval"]).clip(0, 60)
    elif "delta_T_detente" not in df.columns:
        df["delta_T_detente"] = np.nan
    return df


# ── Feature 6 — Efficacité inhibiteur ────────────────────────────────────────

def _feature_inhibitor_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """
    inhibitor_efficiency = inhib_mean / dose_cible (40 mg/L)
    Plage 0 à 1 (0% à 100% de protection).
    Seuils : > 0.8 optimal | 0.5-0.8 partiel | < 0.5 critique
    """
    if "inhib_mean" in df.columns:
        df["inhibitor_efficiency"] = (df["inhib_mean"] / INHIB_DOSE_CIBLE).clip(0, 1)
    return df


# ── Feature 7 — Colmatage filtre ─────────────────────────────────────────────

def _feature_filter_fouling(df: pd.DataFrame) -> pd.DataFrame:
    """
    filter_fouling = dP_filtre / ΔP_max (5 bar)
    Risque MIC et dépôts si filtre colmaté.
    Seuils : < 0.5 propre | 0.5-0.8 nettoyage | > 0.8 urgent
    """
    if "dP_filtre" in df.columns:
        df["filter_fouling"] = (df["dP_filtre"] / 5).clip(0, 1)
    return df


# ── Feature 8 — Indice agressivité global ────────────────────────────────────

def _feature_aggressivity(df: pd.DataFrame) -> pd.DataFrame:
    """
    aggressivity_index = pCO2×0.4 + BSW/100×0.3 + sable/200×0.2 + (1-inhib_eff)×0.1
    Synthèse composite de l'agressivité du milieu.
    Seuils : < 0.5 doux | 0.5-1.0 modéré | > 1.0 sévère
    """
    components = {
        "pCO2_bar":             (0.4, lambda x: x),
        "BSW_mean":             (0.3, lambda x: x / 100),
        "sable_ppm":            (0.2, lambda x: x / 200),
        "inhibitor_efficiency": (0.1, lambda x: 1 - x),
    }

    index = pd.Series(0.0, index=df.index)
    for col, (poids, transform) in components.items():
        if col in df.columns:
            index += poids * transform(df[col].fillna(0))

    df["aggressivity_index"] = index.clip(0, 5)
    return df


# ── Validation des features ───────────────────────────────────────────────────

FEATURES_ML = [
    # Tags DCS
    "T_mean", "T_aval", "P_mean", "P_aval", "CO2_pct", "H2S_ppm",
    "BSW_mean", "sable_ppm", "debit_vol", "inhib_mean", "dP_filtre",
    # Features dérivées
    "pCO2_bar", "CR_deWaard", "velocity_ms", "erosion_ratio",
    "delta_T_detente", "inhibitor_efficiency", "filter_fouling",
    "aggressivity_index",
]


def get_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Retourne la matrice de features X pour XGBoost.
    Ignore les colonnes absentes (source PHMSA peut avoir des tags manquants).

    Returns:
        (X, feature_names_used)
    """
    cols_disponibles = [c for c in FEATURES_ML if c in df.columns]
    X = df[cols_disponibles].copy()

    # Imputation simple : médiane par colonne
    for col in X.columns:
        X[col] = X[col].fillna(X[col].median())

    return X, cols_disponibles


def rapport_features(df: pd.DataFrame) -> None:
    """Affiche un rapport de complétude et distribution des features."""
    print("\n=== Rapport Features ===")
    for feat in FEATURES_ML:
        if feat in df.columns:
            s = df[feat].dropna()
            print(f"  [OK] {feat:<30} n={len(s):>5} | "
                  f"moy={s.mean():>8.3f} | std={s.std():>7.3f} | "
                  f"[{s.min():.3f}, {s.max():.3f}]")
        else:
            print(f"  [--] {feat:<30} ABSENT")
