"""
build_dataset_ml.py
-------------------
Construit le dataset ML final :

  1 LIGNE = 1 MESURE UT SUR UN CML
          + statistiques DCS des 30 jours précédents
          + analyse labo du mois précédent

Fonctionne avec les données COTCO réelles.
Si les données réelles sont absentes, génère un dataset synthétique calibré.
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.parsers.parse_pi_csv import aggregate_30j
from src.parsers.parse_labo_excel import get_labo_30j
from src.features.compute_features import compute_all_features
from src.data.generate_synthetic_cotco import generer_dataset_cotco


def build_dataset_from_cotco(
    df_ut:   pd.DataFrame,
    df_dcs:  pd.DataFrame,
    df_labo: pd.DataFrame,
    cml_registry: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Construit le dataset ML à partir des 3 sources COTCO réelles.

    Pour chaque mesure UT :
      - Agrège les tags DCS sur les 30j précédents
      - Joint l'analyse labo du mois précédent
      - Calcule les 8 features dérivées
      - Calcule CR_mesure = (t_précédente - t_actuelle) / Δt

    Args:
        df_ut         : mesures UT (parse_ut_pdf)
        df_dcs        : tags DCS (parse_pi_csv)
        df_labo       : analyses labo (parse_labo_excel)
        cml_registry  : registre CML avec t_nominal, t_min

    Returns:
        DataFrame ML complet avec colonne source='COTCO_reel'
    """
    lignes = []

    # Trier les mesures UT par CML et date
    df_ut = df_ut.sort_values(["CML_ID", "date"]).reset_index(drop=True)

    # Calculer le taux de corrosion réel entre 2 inspections successives
    df_ut["CR_mesure"] = _calculer_CR_entre_inspections(df_ut)

    for _, row_ut in df_ut.iterrows():
        cml_id = row_ut.get("CML_ID")
        date   = row_ut.get("date")

        if pd.isna(date):
            continue

        ligne = {
            "CML_ID":      cml_id,
            "date":        date,
            "t_mm":        row_ut.get("t_mm"),
            "CR_mesure":   row_ut.get("CR_mesure"),
        }

        # Informations registre CML
        if cml_registry is not None and cml_id in cml_registry["CML_ID"].values:
            cml_info = cml_registry[cml_registry["CML_ID"] == cml_id].iloc[0]
            ligne["t_nominal_mm"] = cml_info.get("t_nominal_mm")
            ligne["t_min_mm"]     = cml_info.get("t_min_mm")
            ligne["mecanisme"]    = cml_info.get("mecanisme_dominant")
            ligne["risque_init"]  = cml_info.get("risque_initial")

        # Calcul RL résiduelle
        if "t_mm" in ligne and "t_min_mm" in ligne and "CR_mesure" in ligne:
            t_rem = float(ligne.get("t_mm", 0)) - float(ligne.get("t_min_mm", 0))
            cr    = float(ligne.get("CR_mesure", 0))
            if cr > 0:
                ligne["RL_ans"] = min(t_rem / cr, 50)

        # Agrégation DCS 30j
        stats_dcs = aggregate_30j(df_dcs, date)
        ligne.update(stats_dcs)

        # Labo mois précédent
        stats_labo = get_labo_30j(df_labo, date, cml_id=cml_id)
        ligne.update(stats_labo)

        ligne["source"] = "COTCO_reel"
        ligne["poids"]  = 3.0

        lignes.append(ligne)

    df = pd.DataFrame(lignes)

    if len(df) == 0:
        print("[WARN] build_dataset_ml : aucune ligne construite depuis COTCO réel")
        return df

    # Renommer les colonnes DCS agrégées (enlever suffixe _mean si déjà nommé)
    df = _normaliser_colonnes_dcs(df)

    # Calcul des 8 features dérivées
    df = compute_all_features(df)

    print(f"[build_dataset] COTCO réel : {len(df)} lignes construites")

    return df


def build_dataset_synthetique(n_points: int = 5000) -> pd.DataFrame:
    """
    Fallback si aucune donnée COTCO disponible.
    Génère un dataset De Waard calibré Kribi.
    Utilisé pendant la phase prototype (avant le stage).
    """
    print("[build_dataset] Mode synthétique (aucune donnée COTCO trouvée)")
    df = generer_dataset_cotco(n_points=n_points)
    df = compute_all_features(df)
    return df


def charger_ou_generer(
    path_ut:   str = "data/enterprise/ut_reports/",
    path_dcs:  str = "data/enterprise/pi_export.csv",
    path_labo: str = "data/enterprise/labo/",
    path_cml:  str = "data/enterprise/cml_registry.csv",
    n_synth:   int = 5000,
) -> tuple[pd.DataFrame, str]:
    """
    Détecte si les données COTCO réelles existent.
    Si oui → build depuis COTCO.
    Si non → génère synthétique.

    Returns:
        (df, mode) où mode = 'cotco_reel' ou 'synthetique'
    """
    dossier_ut   = Path(path_ut)
    fichier_dcs  = Path(path_dcs)
    dossier_labo = Path(path_labo)

    has_ut  = dossier_ut.exists() and any(dossier_ut.glob("*.pdf"))
    has_dcs = fichier_dcs.exists()

    if has_dcs and has_ut:
        print("[build_dataset] Données COTCO détectées → construction dataset réel")

        from src.parsers.parse_pi_csv import parse_pi_csv
        from src.parsers.parse_ut_pdf import parse_ut_folder
        from src.parsers.parse_labo_excel import parse_labo_folder

        df_dcs  = parse_pi_csv(path_dcs)
        df_ut   = parse_ut_folder(path_ut)
        df_labo = parse_labo_folder(path_labo) if dossier_labo.exists() else pd.DataFrame()

        cml_registry = None
        if Path(path_cml).exists():
            cml_registry = pd.read_csv(path_cml)

        df = build_dataset_from_cotco(df_ut, df_dcs, df_labo, cml_registry)
        return df, "cotco_reel"
    else:
        print("[build_dataset] Pas de données COTCO → mode synthétique De Waard")
        df = build_dataset_synthetique(n_synth)
        return df, "synthetique"


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _calculer_CR_entre_inspections(df_ut: pd.DataFrame) -> pd.Series:
    """
    Calcule le taux de corrosion réel entre 2 mesures UT successives sur un CML.
    CR = (t_précédente - t_actuelle) / Δt_années
    """
    cr_series = pd.Series(np.nan, index=df_ut.index)

    for cml_id, groupe in df_ut.groupby("CML_ID"):
        groupe = groupe.sort_values("date")
        for i in range(1, len(groupe)):
            idx_curr = groupe.index[i]
            idx_prev = groupe.index[i - 1]

            t_curr = groupe.loc[idx_curr, "t_mm"]
            t_prev = groupe.loc[idx_prev, "t_mm"]
            dt = (groupe.loc[idx_curr, "date"] - groupe.loc[idx_prev, "date"])
            dt_ans = dt.days / 365.25

            if dt_ans > 0 and not pd.isna(t_curr) and not pd.isna(t_prev):
                cr = (t_prev - t_curr) / dt_ans
                cr_series.loc[idx_curr] = max(0, cr)  # CR ≥ 0

    return cr_series


def _normaliser_colonnes_dcs(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme les colonnes DCS agrégées (T_mean_mean → T_mean, etc.)"""
    rename = {}
    for col in df.columns:
        if col.endswith("_mean_mean"):
            rename[col] = col.replace("_mean_mean", "_mean")
    return df.rename(columns=rename)
