"""
generate_synthetic_cotco.py
---------------------------
Génère un dataset synthétique calibré sur les conditions réelles
de la Station de Réduction de Pression de Kribi (COTCO).

Modèle physique : De Waard & Milliams (1991) + facteurs correctifs terrain.
Source académique : NORSOK M-506 | API RP 14E | NACE SP0775

Ce dataset est la SOURCE 4 du dataset hybride (poids 0.5).
Il sert de complément aux données COTCO réelles, PHMSA et SPE papers.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# Plages opératoires calibrées sur Station Kribi
KRIBI_PARAMS = {
    # Températures (°C)
    "T_min": 35, "T_max": 75,
    # Pression entrée (bar)
    "P_min": 65, "P_max": 100,
    # CO2 gaz associé (% mol) — source AI-4001
    "CO2_pct_min": 0.5, "CO2_pct_max": 5.0,
    # BSW Basic Sediment & Water (% vol) — source AI-4003
    "BSW_min": 0.5, "BSW_max": 30,
    # Vitesse fluide (m/s) — calculée depuis FI-3001
    "velocity_min": 0.3, "velocity_max": 6.0,
    # Résiduel inhibiteur (mg/L) — source CI-5003
    "inhib_min": 5, "inhib_max": 80,
    # Teneur sable (ppm) — source AI-4004
    "sable_min": 0, "sable_max": 200,
    # H2S (ppm) — source AI-4002
    "H2S_min": 0, "H2S_max": 500,
    # Dose cible inhibiteur (mg/L)
    "inhib_dose_cible": 40,
    # Densité pétrole brut Doba (kg/m3)
    "rho_m": 850,
    # Diamètre ligne principale (m)
    "D_m": 0.508,
}


def generer_dataset_cotco(n_points: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Génère un dataset synthétique réaliste calibré Kribi.

    Returns:
        DataFrame avec 20 tags DCS simulés + 8 features + targets CR et RL
        Colonne 'source' = 'simulation_DeWaard' pour la fusion pondérée
    """
    rng = np.random.default_rng(seed)

    p = KRIBI_PARAMS

    # ── Tags DCS simulés ─────────────────────────────────────────────────────

    T       = rng.uniform(p["T_min"],        p["T_max"],        n_points)
    P       = rng.uniform(p["P_min"],        p["P_max"],        n_points)
    CO2_pct = rng.uniform(p["CO2_pct_min"],  p["CO2_pct_max"],  n_points)
    BSW     = rng.uniform(p["BSW_min"],      p["BSW_max"],      n_points)
    vitesse = rng.uniform(p["velocity_min"], p["velocity_max"], n_points)
    # Inhibiteur : distribution normale centrée sur la dose cible (40 mg/L)
    # Reflète une opération maîtrisée avec des écarts occasionnels
    inhib   = np.clip(rng.normal(42, 12, n_points), p["inhib_min"], p["inhib_max"])
    sable   = rng.uniform(p["sable_min"],    p["sable_max"],    n_points)
    H2S     = rng.uniform(p["H2S_min"],      p["H2S_max"],      n_points)

    # Température ambiante Kribi (tropicale)
    T_ambiante = rng.uniform(25, 35, n_points)
    # ΔT détente (chute au détendeur)
    T_aval = T - rng.uniform(5, 35, n_points)
    T_aval = np.clip(T_aval, 10, 60)
    # Pression aval détendeur
    P_aval = rng.uniform(8, 15, n_points)
    # ΔP filtre
    dP_filtre = rng.uniform(0, 5, n_points)
    # Débits
    debit_vol   = rng.uniform(200, 800, n_points)
    debit_masse = debit_vol * p["rho_m"] / 1000
    debit_inhib = inhib * rng.uniform(0.1, 0.3, n_points)
    # Sondes ER (seront prédites par le modèle)
    CP_mV = rng.uniform(-1100, -850, n_points)

    # ── 8 Features dérivées ──────────────────────────────────────────────────

    # Feature 1 — pCO2
    pCO2 = P * CO2_pct / 100

    # Feature 2 — CR De Waard & Milliams (1991)
    T_K = T + 273.15
    CR_deWaard = 10 ** (5.8 - 1710 / T_K + 0.67 * np.log10(pCO2.clip(0.001)))

    # Feature 3 — Vélocité fluide
    rayon = p["D_m"] / 2
    velocity_ms = debit_vol / (3600 * np.pi * rayon ** 2)

    # Feature 4 — Ratio érosif (API RP 14E)
    V_erosive = 100 / np.sqrt(p["rho_m"])
    erosion_ratio = velocity_ms / V_erosive

    # Feature 5 — ΔT détente
    delta_T = T - T_aval

    # Feature 6 — Efficacité inhibiteur
    inhib_eff = (inhib / p["inhib_dose_cible"]).clip(0, 1)

    # Feature 7 — Colmatage filtre
    filter_fouling = dP_filtre / 5

    # Feature 8 — Indice agressivité global
    aggressivity = (
        pCO2 * 0.4
        + BSW / 100 * 0.3
        + sable / 200 * 0.2
        + (1 - inhib_eff) * 0.1
    )

    # ── TARGET : taux de corrosion réel (CR_mesure) ──────────────────────────

    # Correction pH (De Waard-Lotz-Milliams 1993)
    # pH typique eau produite pipeline Kribi : 6.5 - 7.5
    # (fluide plus basique car longue distance + traitement chimique)
    pH = rng.uniform(6.5, 7.5, n_points)
    f_pH = 10 ** (-0.33 * (pH - 4.6))          # < 1 → réduit CR significativement

    # Facteur inhibiteur (réduction jusqu'à 85%)
    f_inhib = 1 - 0.85 * inhib_eff

    # Facteur BSW (eau libre → corrosion accélérée) — modéré
    f_BSW = 1 + 0.2 * (BSW / 30)

    # Facteur érosion mécanique (API RP 14E)
    f_erosion = np.where(
        erosion_ratio > 1.0,
        1 + 0.8 * (erosion_ratio - 1.0),        # moins agressif
        1.0
    )

    # Facteur sable (érosion abrasive) — modéré
    f_sable = 1 + 0.15 * (sable / 200)

    # Facteur H2S (accélération légère)
    f_H2S = 1 + 0.05 * (H2S / 500)

    # Facteur condensation (ΔT élevé → eau condensée)
    f_condensation = np.where(delta_T > 20, 1.3, 1.0)

    # Facteur terrain global (f_field) :
    # Le De Waard est une valeur max théorique (laboratoire, sans mitigation).
    # En conditions réelles managées (pigging, calcaire FeCO3, inhibition programme),
    # le CR terrain est typiquement 10-25% du De Waard théorique.
    # Source : NORSOK M-506, expérience terrain West African pipelines.
    f_field = rng.uniform(0.08, 0.25, n_points)

    # CR final avec variabilité terrain (lognormale réduite)
    CR_mesure = (
        CR_deWaard
        * f_pH                                   # correction pH
        * f_inhib                                # inhibiteur chimique
        * f_field                                # mitigation globale terrain
        * f_BSW
        * f_erosion
        * f_sable
        * f_H2S
        * f_condensation
        * rng.lognormal(0, 0.10, n_points)       # variabilité terrain ±10%
    ).clip(0.001, 1.0)

    # ── TARGET : Remaining Life ───────────────────────────────────────────────

    # Épaisseur nominale Kribi 15.9 mm, t_min ASME ≈ 8.8 mm
    t_nominal = rng.uniform(12, 19, n_points)     # variation par CML
    t_min_asme = t_nominal * rng.uniform(0.45, 0.60, n_points)
    corrosion_allowance = t_nominal - t_min_asme

    RL_ans = (corrosion_allowance / CR_mesure).clip(0, 50)

    # ── Classification risque NACE SP0775 ────────────────────────────────────

    def classifier_risque(cr):
        if cr < 0.025:  return "Acceptable"
        if cr < 0.050:  return "Faible"
        if cr < 0.125:  return "Modéré"
        if cr < 0.250:  return "Élevé"
        if cr < 0.500:  return "Sévère"
        return "Critique"

    risque = [classifier_risque(r) for r in CR_mesure]

    # ── Assemblage DataFrame ──────────────────────────────────────────────────

    df = pd.DataFrame({
        # Tags DCS
        "T_mean":         T,
        "T_aval":         T_aval,
        "T_ambiante":     T_ambiante,
        "P_mean":         P,
        "P_aval":         P_aval,
        "dP_filtre":      dP_filtre,
        "CO2_pct":        CO2_pct,
        "H2S_ppm":        H2S,
        "BSW_mean":       BSW,
        "sable_ppm":      sable,
        "debit_vol":      debit_vol,
        "debit_masse":    debit_masse,
        "inhib_mean":     inhib,
        "CP_mV":          CP_mV,
        # Features dérivées
        "pCO2_bar":           pCO2,
        "CR_deWaard":         CR_deWaard,
        "velocity_ms":        velocity_ms,
        "erosion_ratio":      erosion_ratio,
        "delta_T_detente":    delta_T,
        "inhibitor_efficiency": inhib_eff,
        "filter_fouling":     filter_fouling,
        "aggressivity_index": aggressivity,
        # Épaisseurs
        "t_nominal_mm":   t_nominal,
        "t_min_mm":       t_min_asme,
        # Targets
        "CR_mesure":      CR_mesure,
        "RL_ans":         RL_ans,
        "risque_NACE":    risque,
        # Traçabilité fusion
        "source":         "simulation_DeWaard",
        "poids":          0.5,
    })

    print(f"[Synthétique COTCO] {n_points} points générés")
    print(f"  CR moyen    : {CR_mesure.mean():.4f} mm/an")
    print(f"  CR max      : {CR_mesure.max():.4f} mm/an")
    print(f"  RL médiane  : {np.median(RL_ans):.1f} ans")
    print(f"  Risques : {pd.Series(risque).value_counts().to_dict()}")

    return df


def sauvegarder(df: pd.DataFrame, path: str = "data/raw/synthetic_cotco.csv") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[Synthétique COTCO] Sauvegardé : {path}")


if __name__ == "__main__":
    df = generer_dataset_cotco(n_points=5000)
    sauvegarder(df)
